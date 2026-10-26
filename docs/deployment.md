# Despliegue en DigitalOcean

Rakim corre en un **Droplet de DigitalOcean** (un servidor virtual pequeño) dentro de un contenedor Docker. Cada fusión en `master` lo actualiza sola. Por qué se eligió este host y qué se descartó: [`decisions.md`](./decisions.md#hosting-y-cicd).

| Dato          | Valor                                                                                      |
| :------------ | :----------------------------------------------------------------------------------------- |
| Servidor      | Droplet Basic, **US$4/mes** (512 MiB, 1 vCPU, 10 GiB) → **US$48/año**                      |
| Sistema       | Ubuntu 24.04 LTS, con swap de 1 GB y actualizaciones de seguridad automáticas              |
| Runtime       | Docker, imagen `python:3.13-slim` (Python 3.13, con los parches de seguridad)             |
| Estado        | Volumen de Docker `rakim-data` (el aviso de bump pendiente)                                |
| Configuración | `/opt/rakim-bot/.env`, solo en el servidor                                                 |
| Despliegue    | GitHub Actions: `docker build` → `docker save \| ssh docker load` → `docker compose up -d` |

Si el bot se queda sin memoria (lo verás como reinicios del contenedor), el Droplet se amplía a US$6 (1 GiB) desde el panel de DigitalOcean sin reconstruir nada.

## 1. Crear el Droplet

En DigitalOcean: **Create > Droplets**.

- **Imagen:** Ubuntu 24.04 (LTS) x64.
- **Plan:** Basic, CPU Regular (disco SSD), **US$4/mes** (512 MiB / 1 vCPU / 10 GiB).
- **Región:** EE. UU. del este (por ejemplo, Nueva York): el gateway de Discord está allí. Para un bot de eventos la diferencia es mínima.
- **Autenticación:** llave SSH (la tuya). No uses contraseña.
- **Opcional:** activa _Monitoring_ para ver memoria y CPU en el panel.

Anota la IP pública del Droplet: es `DEPLOY_HOST`.

## 2. Generar la llave del despliegue

La usará solo GitHub Actions, distinta de la tuya. En tu máquina, **fuera del repo**:

```bash
ssh-keygen -t ed25519 -f rakim-deploy -C "rakim-bot deploy" -N ""
```

Genera `rakim-deploy` (privada, va a un secreto de GitHub) y `rakim-deploy.pub` (pública, va al servidor). No las subas al repositorio.

## 3. Preparar el servidor (una sola vez)

```bash
scp deploy/setup-droplet.sh root@<IP>:
ssh root@<IP> "DEPLOY_PUBKEY='$(cat rakim-deploy.pub)' bash setup-droplet.sh"
```

El script crea el swap, instala Docker, cierra el firewall salvo SSH, activa las actualizaciones automáticas, crea el usuario `deploy` (con tu llave y la del CD) y deja SSH solo con llave. Puedes volver a ejecutarlo sin romper nada. No lo he probado en un Droplet real: si algo falla, el error indica el paso.

Comprueba que entras como `deploy` con tu llave antes de seguir:

```bash
ssh deploy@<IP> "docker ps && ls -ld /opt/rakim-bot"
```

## 4. Crear el `.env` en el servidor

El token y los IDs viven solo aquí. Parte de [`.env.example`](../.env.example):

```bash
ssh deploy@<IP>
nano /opt/rakim-bot/.env      # pega las variables completadas
chmod 600 /opt/rakim-bot/.env
```

No incluyas `STATE_PATH`: `compose.yml` lo fija al volumen. De dónde sale cada valor: [`setup.md`](./setup.md#3-configurar-el-entorno).

## 5. Configurar GitHub

En el repo: **Settings > Environments > New environment** llamado `production`. Después, con la CLI de GitHub (`gh`) desde la carpeta del repo:

```bash
gh variable set DEPLOY_HOST --body "<IP>"
gh variable set DEPLOY_USER --body "deploy"
gh secret set DEPLOY_SSH_KEY < rakim-deploy
```

Para `DEPLOY_KNOWN_HOSTS` (la huella del servidor, para que el CD no confíe a ciegas):

```bash
ssh-keyscan -t ed25519 <IP> > known_hosts.txt
ssh-keygen -lf known_hosts.txt         # huella que ve tu máquina
```

Compara esa huella con la del servidor, que ves en la consola web del Droplet (DigitalOcean > Droplet > _Console_): `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`. Si coinciden:

```bash
gh secret set DEPLOY_KNOWN_HOSTS < known_hosts.txt
```

## 6. Primer despliegue

En GitHub: **Actions > Deploy > Run workflow** (o fusiona un PR en `master`). El flujo valida, construye la imagen, la envía al servidor y la levanta. Si el bot no queda corriendo (por ejemplo, un `.env` incompleto), el último paso falla en rojo y muestra los logs.

Comprueba en el servidor:

```bash
ssh deploy@<IP>
cd /opt/rakim-bot
docker compose ps
docker compose logs --tail 30 rakim     # debe decir "Rakim conectado como …"
docker stats --no-stream rakim-bot      # memoria usada
```

## 7. Operación

| Quiero…                     | Cómo                                                                                                        |
| :-------------------------- | :---------------------------------------------------------------------------------------------------------- |
| Ver logs en vivo            | `docker compose logs -f rakim`                                                                              |
| Reiniciar                   | `docker compose restart rakim` (el aviso de bump pendiente se conserva)                                     |
| Actualizar el bot           | Fusionar en `master`. Los cambios solo de documentación no redespliegan                                     |
| Actualizar Python           | Cada despliegue reconstruye con `--pull`. Para forzarlo sin cambios: **Actions > Deploy > Run workflow**    |
| Volver a una versión previa | Revertir el PR en `master`: el despliegue sale solo. No se guardan imágenes anteriores                      |
| Cambiar el token o un ID    | Editar `/opt/rakim-bot/.env` y `docker compose up -d` (recrea el contenedor con el nuevo valor)             |
| Rotar la llave del CD       | Repetir el paso 2, reemplazar la línea en `/home/deploy/.ssh/authorized_keys` y el secreto `DEPLOY_SSH_KEY` |
| Ver el estado guardado      | `docker run --rm -v rakim-bot_rakim-data:/d alpine cat /d/state.json`                                       |

## 8. Proteger `master` (recomendado)

Que nadie pueda desplegar sin pasar por un PR: en **Settings > Rules** (o ramas protegidas), sobre `master`:

- Exigir Pull Request antes de fusionar.
- Exigir los checks: `Lint & Test`, `Docker build` y `PR title (Conventional Commits)`.
- Bloquear el push directo.

Depende del plan de la organización: los repos privados pueden requerir un plan de pago para estas reglas. Sin ellas, la disciplina de "nunca push directo a `master`" de `AGENTS.md` es lo único que protege el despliegue.

## 9. Seguridad

- El usuario `deploy` está en el grupo `docker`, lo que equivale a tener root en el servidor. Por eso solo entran con llave la tuya y la del CD, y no tiene `sudo` ni contraseña.
- El firewall (`ufw`) solo deja pasar SSH. Rakim no escucha en ningún puerto: solo conecta hacia Discord.
- El contenedor corre sin root, con el sistema de archivos de solo lectura (salvo el volumen y `/tmp`), sin capacidades de Linux extra y con la memoria limitada.
- Las actualizaciones de seguridad del sistema (incluido Docker) se aplican solas. Python y sus dependencias se actualizan con cada despliegue (`--pull`).
- El `.env` tiene permisos `600` y el token no pasa por GitHub. Si el token se filtra, restablécelo en el portal de desarrolladores y actualiza el `.env`.

## Lo que no cubre

- **Alertas:** si el bot se cae, nadie recibe un aviso. `restart: unless-stopped` lo reinicia solo ante una caída, y un fallo de despliegue sale en rojo en Actions. El monitoreo del panel de DigitalOcean puede avisar por memoria o CPU.
- **Copias de seguridad:** no hacen falta; el estado es un único aviso recuperable.
- **Entornos de prueba:** no hay un segundo bot de pruebas desplegado; se prueba en local con un bot y un servidor de pruebas.

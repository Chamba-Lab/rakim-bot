# Rakim Bot

El bot de Discord de [Chamba Lab](https://chambalab.org), una comunidad tech para conectar, inspirarse y crecer juntos. Rakim es la mascota de la comunidad (un mapache con taza de café) y da la cara en el servidor.

## Qué hace

1. **Da la bienvenida.** Cuando alguien termina la pantalla de reglas, Rakim lo saluda en el canal general con primeros pasos y qué ofrece el servidor. Así la persona no espera a que un moderador esté disponible.
2. **Registra entradas y salidas.** En un canal privado publica quién entró o salió, con la invitación usada, la antigüedad de la cuenta y los roles. Es solo informativo.
3. **Recuerda el bump.** Detecta el bump de Disboard y avisa cuando pasan las 2 horas de enfriamiento. No ejecuta `/bump`: un bot no puede invocar los comandos de otro.

El detalle de cada función está en [`docs/architecture.md`](./docs/architecture.md).

## Instalación

Requisitos: **Node.js 22.23.4, 24.22.1, 26.12.1 o posterior de su línea** (las versiones con el parche de seguridad de octubre de 2026) y npm.

```bash
git clone https://github.com/Chamba-Lab/rakim-bot.git
cd rakim-bot
npm install
cp .env.example .env
```

Después crea el bot en Discord (siguiente sección) y completa `.env`.

## Crear el bot y configurarlo

Para probar usa **un bot y un servidor de pruebas propios**, no los de la comunidad.

1. En el [portal de desarrolladores](https://discord.com/developers/applications) crea una aplicación. En **Bot**, restablece el token y cópialo a `DISCORD_TOKEN` en `.env`.
2. En **Bot > Privileged Gateway Intents**, activa **Server Members Intent** y **Message Content Intent**. Son los únicos intents privilegiados que usa Rakim; el porqué de cada intent está en [`docs/architecture.md`](./docs/architecture.md#intents).
3. Activa el _Modo desarrollador_ en Discord (Ajustes > Avanzado) y copia con clic derecho > _Copiar ID_ el servidor y los canales a las variables de `.env`. Cada variable está explicada en `.env.example`.

Los IDs, el token y los textos no están en el código: los IDs y el token vienen del entorno (`.env` está en `.gitignore`; solo se sube `.env.example`) y todo lo que Rakim escribe vive en [`src/messages.ts`](./src/messages.ts).

## Invitar el bot con los permisos mínimos

Reemplaza `<CLIENT_ID>` por el ID de tu aplicación (en **General Information**):

```text
https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot&permissions=19488
```

`19488` suma solo cuatro permisos:

| Permiso            | Para qué                                                        |
| :----------------- | :-------------------------------------------------------------- |
| Ver canales        | Llegar a los canales de bienvenida, logs y bump                 |
| Enviar mensajes    | Saludar, registrar y recordar                                   |
| Insertar enlaces   | Mostrar los embeds del log                                      |
| Gestionar servidor | Leer las invitaciones y sus usos (no hay otra forma de hacerlo) |

No se pide Administrador, ni leer el historial, ni mencionar a todos. Tras invitarlo:

- Da al rol de Rakim acceso al **canal de logs** (es privado).
- Si usas `BUMP_ROLE_ID`, marca ese rol como **mencionable**; así no hace falta darle a Rakim el permiso de mencionar todos los roles.
- Para ser aún más estricto, invítalo solo con `permissions=32` (Gestionar servidor) y concede Ver canales, Enviar mensajes e Insertar enlaces canal por canal en los tres que usa.

## Ejecutar

```bash
npm run dev        # desarrollo: reinicia al guardar
npm run build && npm start   # producción
```

Al conectar verás `Rakim conectado como <nombre>`. Si falta o está mal una variable, el proceso termina listando todos los errores. La guía completa de pruebas y diagnóstico está en [`docs/runbook.md`](./docs/runbook.md).

## Comandos

| Comando             | Qué hace                                        |
| :------------------ | :---------------------------------------------- |
| `npm run dev`       | Arranca el bot y lo reinicia al guardar cambios |
| `npm run build`     | Compila a `dist/`                               |
| `npm start`         | Ejecuta la versión compilada                    |
| `npm run typecheck` | Revisa los tipos sin compilar                   |
| `npm run lint`      | ESLint y comprobación de formato con Prettier   |
| `npm run lint:fix`  | Corrige lo que se pueda automáticamente         |
| `npm test`          | Ejecuta las pruebas                             |

## Despliegue

Rakim es **un único proceso de Node.js que mantiene una conexión permanente con Discord**, así que necesita un host siempre encendido (un servicio _serverless_ no sirve). Corre en un **Droplet de DigitalOcean de US$4 al mes (US$48 al año)** dentro de un contenedor Docker, y cada fusión en `master` lo actualiza sola con GitHub Actions:

1. **Validar**: lint, tipos, pruebas y build.
2. **Construir** la imagen (`Dockerfile`, Node 24 parcheado) y **enviarla por SSH** al servidor, sin registro de imágenes de por medio.
3. **Reiniciar** el contenedor con `deploy/compose.yml` y comprobar que queda corriendo.

El token y los IDs viven solo en `/opt/rakim-bot/.env` del servidor; el estado, en un volumen de Docker. La guía paso a paso (crear el Droplet, preparar el servidor, configurar GitHub, primer despliegue y operación) está en [`docs/deployment.md`](./docs/deployment.md).

Reglas que valen para cualquier host: **una sola instancia a la vez** (dos procesos con el mismo token saludarían y registrarían todo por duplicado), y al activar el bot en producción, desactiva el mensaje automático de llegada de Discord para que no se duplique con el saludo de Rakim.

## Estructura

```text
src/
  index.ts         arranque: configuración, cliente e intents
  config.ts        variables de entorno, validadas
  context.ts       lo que comparten los eventos
  messages.ts      todos los textos de Rakim
  events/          un archivo por evento de Discord
  services/        lo que hace cada función (bienvenida, log, bump)
  lib/             piezas sin Discord que se pueden probar: invitaciones, bump, estado
```

## Documentación

- [AGENTS.md](./AGENTS.md): fuente de verdad del repo (producto, stack, estructura y reglas de trabajo)
- [CONTRIBUTING.md](./CONTRIBUTING.md): cómo contribuir
- [docs/project.md](./docs/project.md): propósito, alcance y roadmap
- [docs/architecture.md](./docs/architecture.md): cómo funciona, intents y permisos
- [docs/decisions.md](./docs/decisions.md): decisiones clave
- [docs/runbook.md](./docs/runbook.md): crear el bot, configurarlo y diagnosticarlo
- [docs/deployment.md](./docs/deployment.md): desplegar en DigitalOcean y operar el servidor

El repositorio es privado y aún no tiene licencia definida.

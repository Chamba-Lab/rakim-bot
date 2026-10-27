# Rakim Bot

El bot de Discord de [Chamba Lab](https://chambalab.org), una comunidad tech para conectar, inspirarse y crecer juntos. Rakim es la mascota de la comunidad (un mapache con taza de café) y da la cara en el servidor.

## Qué hace

1. **Da la bienvenida.** Cuando alguien termina la pantalla de reglas, Rakim lo saluda en el canal general con primeros pasos y qué ofrece el servidor.
2. **Registra entradas y salidas.** En un canal privado publica quién entró o salió, con la invitación usada, la antigüedad de la cuenta y los roles.
3. **Recuerda el bump.** Detecta el bump de Disboard y avisa cuando pasan las 2 horas de enfriamiento. No ejecuta `/bump`: un bot no puede invocar los comandos de otro.

Cómo funciona cada una, los intents y los permisos: [`docs/architecture.md`](./docs/architecture.md).

## Instalación

Necesitas [uv](https://docs.astral.sh/uv/), que instala Python 3.14 y las dependencias solo.

```bash
git clone https://github.com/Chamba-Lab/rakim-bot.git
cd rakim-bot
uv sync
cp .env.example .env     # completa el token y los IDs
uv run python -m rakim
```

### Con Docker

Para dejarlo corriendo en segundo plano (con Docker abierto, desde la carpeta del repo y con el `.env` listo):

```bash
docker build -t rakim-bot .
docker run -d --name rakim --restart unless-stopped --env-file .env -e STATE_PATH=/data/state.json -v rakim-data:/data rakim-bot
```

Logs: `docker logs -f rakim`. Detener y borrar el contenedor: `docker rm -f rakim`. Una sola instancia por token: no lo dejes corriendo si el despliegue está activo.

## Crear el bot e invitarlo

Para probar usa **un bot y un servidor de pruebas propios**, no los de la comunidad. Los pasos (portal de desarrolladores, intents, IDs, cómo probar cada función y qué hacer si algo falla) están en [`docs/setup.md`](./docs/setup.md). Lo esencial:

- Activa los intents privilegiados **Server Members** y **Message Content** en el portal.
- Invítalo con los permisos mínimos (`19488`: Ver canales, Enviar mensajes, Insertar enlaces y Gestionar servidor, este último para leer las invitaciones):

```text
https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot&permissions=19488
```

El token y los IDs viven en `.env` (que no se sube al repo; solo `.env.example`). Todo lo que Rakim escribe está en [`rakim/messages.py`](./rakim/messages.py).

## Comandos

| Comando                                          | Qué hace                      |
| :----------------------------------------------- | :---------------------------- |
| `uv run python -m rakim`                         | Arranca el bot                |
| `uv run pytest`                                  | Ejecuta las pruebas           |
| `uv run mypy`                                     | Revisa los tipos              |
| `uv run ruff check . && uv run ruff format --check .` | Lint y formato           |
| `uv run ruff check --fix . && uv run ruff format .`   | Corrige lo que se pueda  |

## Despliegue

Rakim corre en un **Droplet de DigitalOcean de US$4/mes (US$48 al año)** dentro de un contenedor Docker, y, **una vez activado** (`DEPLOY_ENABLED=true`; nace apagado), cada fusión en `master` lo actualiza sola con GitHub Actions (valida, construye la imagen, la envía por SSH y reinicia). Una sola instancia a la vez: dos procesos con el mismo token saludarían y registrarían todo por duplicado. Guía paso a paso: [`docs/deployment.md`](./docs/deployment.md).

## Estructura

```text
rakim/
  __main__.py   arranque
  bot.py        el cliente, sus intents y lo que comparten los eventos
  config.py     variables de entorno, validadas
  messages.py   todos los textos de Rakim
  events/       un módulo por evento de Discord
  invites.py, bump.py, state.py, welcome.py   la lógica de cada función
tests/
```

## Documentación

[AGENTS.md](./AGENTS.md) (fuente de verdad del repo) · [CONTRIBUTING.md](./CONTRIBUTING.md) · [docs/architecture.md](./docs/architecture.md) · [docs/setup.md](./docs/setup.md) · [docs/deployment.md](./docs/deployment.md) · [docs/decisions.md](./docs/decisions.md)

El repositorio es privado y aún no tiene licencia definida.

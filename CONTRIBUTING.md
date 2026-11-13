# Cómo contribuir a Rakim Bot

Gracias por sumar. Si algo no queda claro, pregunta en [Discord](https://chambalab.org/discord).

## Preparar el entorno

Necesitas [uv](https://docs.astral.sh/uv/) (instala Python 3.14 y las dependencias).

```bash
git clone https://github.com/Chamba-Lab/rakim-bot.git
cd rakim-bot
uv sync
cp .env.example .env
```

Para probar contra Discord necesitas un bot y un servidor de pruebas propios, no los de la comunidad: [`docs/setup.md`](./docs/setup.md). Las convenciones y la estructura están en [AGENTS.md](./AGENTS.md); léelo antes de tocar código.

## Antes de proponer una función nueva

Rakim corre en un servidor pequeño, con poca memoria y CPU. Por eso solo suma funciones esenciales para la comunidad, no funciones por agregar. Antes de programar algo nuevo, cuenta la idea en el hilo de Rakim Bot del canal de proyectos de [Discord](https://chambalab.org/discord) o en un issue: qué problema resuelve, a quién le sirve y si hay una forma más simple. Las correcciones, las pruebas y las mejoras de documentación no necesitan propuesta previa.

## Flujo de trabajo

1. **Parte de `master` actualizada** y crea una rama con prefijo: `feat/welcome-copy`, `fix/invite-cache`, `docs/setup`, `chore/update-deps`.
2. **Commits pequeños**: un cambio lógico, un commit.
3. **Valida en local** antes de abrir el PR:
    ```bash
    uv run ruff check . && uv run ruff format --check .
    uv run mypy
    uv run pytest
    ```
4. **Abre un Pull Request hacia `master`** y completa la plantilla; marca solo lo que verificaste. Una persona del equipo revisa.

**Nunca hagas push directo a `master`**, tampoco el equipo ni los agentes de IA: todo entra por Pull Request, y, con el despliegue activado, cada fusión en `master` despliega el bot.

## Commits y título del PR

[Conventional Commits](https://www.conventionalcommits.org/es/), en inglés e imperativo; el título del PR también. Prefijos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`. Ejemplos: `feat: greet members after the rules screen`, `fix: ignore invites from other guilds`.

## Qué se espera de un cambio

- **Pruebas** para la lógica con reglas. Los eventos de Discord se prueban a mano en un servidor de pruebas, y se dice en el PR.
- **Documentación al día** en el mismo PR.
- **Textos de Rakim** con su voz: directos y cálidos, español neutro, tuteo, sin jerga local y un solo emoji como máximo.
- **Sin secretos**: ni tokens ni IDs reales de producción en commits, issues o capturas.

## Licencia

Al contribuir aceptas que tu aporte se publique bajo la [licencia MIT](./LICENSE). Rakim y la marca Chamba Lab quedan fuera de esa licencia: [NOTICE.md](./NOTICE.md).

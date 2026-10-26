# Cómo contribuir a Rakim Bot

Gracias por sumar. Esta guía explica cómo proponer cambios sin fricción. Si algo no queda claro, pregunta en [Discord](https://chambalab.org/discord).

## Preparar el entorno

Requisitos: **Node.js >= 22.12** y npm.

```bash
git clone https://github.com/Chamba-Lab/rakim-bot.git
cd rakim-bot
npm install
cp .env.example .env
```

Para probar contra Discord necesitas un bot propio y un servidor de pruebas; no uses el bot ni el servidor de la comunidad. Los pasos están en [`docs/runbook.md`](./docs/runbook.md). La arquitectura y las convenciones viven en [AGENTS.md](./AGENTS.md); léelo antes de tocar código.

## Flujo de trabajo

1. **Parte siempre de `master` actualizada** y crea una rama con un prefijo y una descripción corta: `feat/welcome-copy`, `fix/invite-cache`, `docs/runbook`, `chore/update-deps`.
2. **Haz commits pequeños**: un cambio lógico, un commit.
3. **Valida en local** antes de abrir el PR:
    ```bash
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```
4. **Abre un Pull Request hacia `master`** y completa la plantilla. Marca solo lo que verificaste.
5. **Espera revisión.** Una persona del equipo revisa; responde a los comentarios con nuevos commits en la misma rama.

**Nunca hagas push directo a `master`**: todo cambio va en una rama y entra por Pull Request, también el del equipo y el de los agentes de IA.

## Commits y título del PR

Usamos [Conventional Commits](https://www.conventionalcommits.org/es/), en inglés y en imperativo. El título del PR también.

| Prefijo     | Cuándo                                      |
| :---------- | :------------------------------------------ |
| `feat:`     | Función nueva                               |
| `fix:`      | Corrección de un error                      |
| `docs:`     | Solo documentación                          |
| `refactor:` | Cambio interno sin cambio de comportamiento |
| `test:`     | Pruebas                                     |
| `chore:`    | Mantenimiento, dependencias, configuración  |

Ejemplos: `feat: greet members after the rules screen`, `fix: ignore invites from other guilds`.

## Qué se espera de un cambio

- **Pruebas** para la lógica con reglas (deducir una invitación, detectar un bump, programar un aviso). Los eventos de Discord se prueban a mano en un servidor de pruebas y se dice en el PR.
- **Documentación al día**: si cambia el comportamiento, actualiza `AGENTS.md`, `README.md` o `docs/` en el mismo PR.
- **Textos de Rakim** con su voz: breves, en español neutro, con tuteo, sin jerga local y con un solo emoji como máximo.
- **Sin secretos**: nada de tokens ni IDs reales de producción en commits, issues o capturas.

import sys

from pydantic import ValidationError

from .bot import RakimBot
from .config import Settings


def main() -> None:
    try:
        settings = Settings()
    except ValidationError as error:
        # Todos los problemas de configuración a la vez, no uno por intento.
        problems = "\n".join(
            f"- {'.'.join(map(str, e['loc'])).upper()}: {e['msg']}"
            for e in error.errors()
        )
        sys.exit(f"Configuración inválida:\n{problems}")
    RakimBot(settings).run(settings.discord_token.get_secret_value())


main()

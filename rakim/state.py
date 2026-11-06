import json
import logging
import os
from pathlib import Path

log = logging.getLogger("rakim")


class State:
    """Lo único que debe sobrevivir a un reinicio: cuándo vence el aviso de bump.

    Es un archivo JSON diminuto; si el bot llega a guardar más cosas, se cambia por SQLite.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.bump_due_at: float | None = None
        if self.path.exists():
            try:
                self.bump_due_at = json.loads(self.path.read_text()).get("bump_due_at")
            except OSError, ValueError, AttributeError:
                # Un archivo ilegible no debe impedir que el bot arranque: solo se pierde
                # el aviso de bump pendiente.
                log.exception("No se pudo leer %s; se arranca sin estado", self.path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Se escribe a un archivo aparte y se renombra: un corte no deja el estado a medias.
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({"bump_due_at": self.bump_due_at}))
        os.replace(temp, self.path)

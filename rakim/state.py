import json
import logging
import os
from pathlib import Path

log = logging.getLogger("rakim")


class State:
    """Lo que debe sobrevivir a un reinicio: cuándo vence el aviso de bump y qué temas del
    día ya salieron en el ciclo actual.

    Es un archivo JSON pequeño (como mucho, unos cien temas); si el bot llega a guardar
    bastante más, se cambia por SQLite.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.bump_due_at: float | None = None
        self.used_topics: list[str] = []
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.bump_due_at = data.get("bump_due_at")
                self.used_topics = [
                    t for t in data.get("used_topics", []) if isinstance(t, str)
                ]
            except OSError, ValueError, AttributeError, TypeError:
                # Un archivo ilegible no debe impedir que el bot arranque: solo se pierden
                # el aviso de bump pendiente y el ciclo de temas.
                log.exception("No se pudo leer %s; se arranca sin estado", self.path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Se escribe a un archivo aparte y se renombra: un corte no deja el estado a medias.
        temp = self.path.with_suffix(".tmp")
        data = {"bump_due_at": self.bump_due_at, "used_topics": self.used_topics}
        temp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(temp, self.path)

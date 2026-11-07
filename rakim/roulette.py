"""Temas de la ruleta. Son una copia de `src/content/roulette.json` del sitio (Chamba-Lab/home):
al cambiar allá, se vuelve a copiar aquí. No depende de Discord."""

import json
import random
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).with_name("roulette.json")


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    options: tuple[str, ...]


def load_presets(path: Path = DATA) -> list[Preset]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Preset(p["id"], p["name"], tuple(p["options"])) for p in raw]


def find_preset(presets: list[Preset], text: str) -> Preset | None:
    """Un grupo por su id, o por una parte de su nombre (para la forma con mención)."""
    wanted = text.strip().casefold()
    if not wanted:
        return None
    for p in presets:
        if p.id == wanted:
            return p
    return next((p for p in presets if wanted in p.name.casefold()), None)


def pick(
    presets: list[Preset],
    only: Preset | None = None,
    last: str | None = None,
    rng: random.Random | None = None,
) -> tuple[Preset, str]:
    """Un tema al azar (de un grupo o de todos), sin repetir el último que salió."""
    pairs = [(p, o) for p in ([only] if only else presets) for o in p.options]
    fresh = [pair for pair in pairs if pair[1] != last]
    return (rng or random).choice(fresh or pairs)

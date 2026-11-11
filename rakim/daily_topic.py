"""El tema del día: a qué hora sale y cuál toca. No depende de Discord.

Lleva su propio ciclo, aparte de `/ruleta`: no repite un tema hasta haber usado todos los
de sus grupos.
"""

import random
from datetime import time, timedelta, timezone

from .roulette import Preset

# Hora de Lima. Perú no tiene horario de verano: UTC-5 fijo todo el año, sin depender de
# la base de zonas horarias del sistema (la imagen slim podría no traerla).
LIMA = timezone(timedelta(hours=-5), "Lima")


def split_list(text: str) -> list[str]:
    """«a, b,c» → ["a", "b", "c"]. Los vacíos se ignoran."""
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_times(text: str) -> list[time]:
    """«18:00» (o varias, separadas por coma) → horas de Lima. Vacío: ninguna."""
    times = []
    for part in split_list(text):
        try:
            hour, minute = part.split(":")
            times.append(time(int(hour), int(minute), tzinfo=LIMA))
        except ValueError as e:
            raise ValueError(f"hora no válida: {part!r} (usa HH:MM)") from e
    return times


def select_presets(presets: list[Preset], ids: list[str]) -> list[Preset]:
    """Los grupos de temas elegidos, por su id. Falla si alguno no existe."""
    by_id = {p.id: p for p in presets}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise ValueError(f"grupos de temas desconocidos: {', '.join(unknown)}")
    if not ids:
        raise ValueError("hace falta al menos un grupo de temas")
    return [by_id[i] for i in ids]


def next_topic(
    presets: list[Preset], used: list[str], rng: random.Random | None = None
) -> tuple[Preset, str, list[str]]:
    """El tema que toca y la lista de usados actualizada.

    Los usados se guardan por su texto: si `roulette.json` cambia, los temas nuevos
    entran solos al ciclo y los que ya no existen se olvidan.
    """
    pairs = [(p, o) for p in presets for o in p.options]
    known = {o for _, o in pairs}
    used = [t for t in used if t in known]
    fresh = [pair for pair in pairs if pair[1] not in used]
    if not fresh:
        # Ciclo completo: empieza otro, sin repetir enseguida el último que salió.
        last = used[-1] if used else None
        used = []
        fresh = [pair for pair in pairs if pair[1] != last] or pairs
    preset, topic = (rng or random).choice(fresh)
    return preset, topic, [*used, topic]

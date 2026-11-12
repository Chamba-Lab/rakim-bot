"""Cuántos miembros hay por rol (país, etapa). No depende de Discord: recibe los roles de
cada miembro ya filtrado."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Breakdown:
    rows: list[tuple[int, int]]  # (ID del rol, miembros), de mayor a menor
    unanswered: int  # sin ninguno de los roles
    total: int


def breakdown(member_roles: list[set[int]], role_ids: list[int]) -> Breakdown:
    """Reparte a los miembros entre los roles dados.

    Los roles en 0 también salen. A igual cantidad se respeta el orden configurado. Si
    alguien tuviera dos roles de la lista, cuenta en ambos: el total es de miembros, no
    la suma de las filas.
    """
    counts = {r: 0 for r in role_ids}
    unanswered = 0
    for roles in member_roles:
        matched = roles & counts.keys()
        for r in matched:
            counts[r] += 1
        if not matched:
            unanswered += 1
    rows = sorted(counts.items(), key=lambda kv: -kv[1])
    return Breakdown(rows, unanswered, len(member_roles))

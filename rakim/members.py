"""Cuántos miembros eligieron cada opción del Onboarding, y cuántos tienen cada rol. No
depende de Discord: recibe las preguntas y los roles de cada miembro ya filtrado."""

from dataclasses import dataclass

Rows = list[tuple[str, int]]


@dataclass(frozen=True)
class Option:
    label: str
    role_ids: frozenset[int]


@dataclass(frozen=True)
class Question:
    title: str
    options: list[Option]
    multiple: bool  # selección múltiple: las filas pueden sumar más que el total


def own_roles(question: Question) -> list[frozenset[int]]:
    """El rol (o los roles) que identifican cada opción.

    Un rol que dan varias opciones de la misma pregunta (como Member, que dan todas las de
    etapa) no sirve para saber qué se eligió: se quita. Si una opción no tiene roles
    propios, se usan todos los suyos.
    """
    result = []
    for option in question.options:
        others: set[int] = set()
        for other in question.options:
            if other is not option:
                others |= other.role_ids
        result.append(option.role_ids - others or option.role_ids)
    return result


def tally(question: Question, member_roles: list[set[int]]) -> tuple[Rows, int]:
    """Miembros por opción (de mayor a menor; a igual cantidad, en el orden del
    Onboarding) y cuántos no tienen ninguna."""
    owned = own_roles(question)
    counts = [0] * len(question.options)
    none = 0
    for roles in member_roles:
        chosen = [i for i, own in enumerate(owned) if roles & own]
        for i in chosen:
            counts[i] += 1
        if not chosen:
            none += 1
    rows = [(o.label, n) for o, n in zip(question.options, counts, strict=True)]
    return sorted(rows, key=lambda row: -row[1]), none


def role_counts(roles: list[tuple[int, str]], member_roles: list[set[int]]) -> Rows:
    """Miembros por rol, de mayor a menor (a igual cantidad, en el orden dado)."""
    rows = [(name, sum(1 for m in member_roles if rid in m)) for rid, name in roles]
    return sorted(rows, key=lambda row: -row[1])

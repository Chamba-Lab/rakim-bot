"""La tarjeta de miembro de `/perfil`: el puesto de llegada y las respuestas al Onboarding.
No depende de Discord: recibe las fechas de entrada y los roles ya leídos."""

from datetime import datetime

from .members import Question, own_roles

Join = tuple[datetime, int]  # (fecha de entrada, ID del miembro)


def join_rank(member: Join, joins: list[Join]) -> int:
    """Puesto de llegada (desde 1) entre `joins`, que incluye a `member`.

    Es el orden entre los miembros actuales: Discord no recuerda a quien salió, así que
    el número baja si sale alguien que entró antes. A igual fecha decide el ID, que
    también crece con el tiempo.
    """
    return 1 + sum(1 for j in joins if j < member)


def answers(questions: list[Question], roles: set[int]) -> list[tuple[str, list[str]]]:
    """Lo que la persona eligió en cada pregunta, por el rol propio de cada opción. Las
    preguntas sin respuesta se omiten: la tarjeta muestra solo lo que hay."""
    result = []
    for question in questions:
        chosen = [
            option.label
            for option, own in zip(question.options, own_roles(question), strict=True)
            if roles & own
        ]
        if chosen:
            result.append((question.title, chosen))
    return result


def onboarding_role_ids(questions: list[Question]) -> set[int]:
    """Todos los roles que da el Onboarding (también el común, como Member), para no
    repetirlos entre los demás roles."""
    return {r for q in questions for o in q.options for r in o.role_ids}

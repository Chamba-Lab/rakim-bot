from datetime import UTC, datetime

from rakim.profile import answers, join_rank, onboarding_role_ids
from tests.test_members import (
    ACTIVIDADES,
    AVISOS,
    COUNTRY,
    EARLY,
    EVENTOS,
    MEMBER,
    NOTICES,
    PERU,
    STAGE,
)


def day(n: int) -> datetime:
    return datetime(2026, 10, n, tzinfo=UTC)


def test_join_rank_counts_who_arrived_before():
    joins = [(day(3), 30), (day(1), 10), (day(2), 20)]
    assert join_rank((day(1), 10), joins) == 1
    assert join_rank((day(3), 30), joins) == 3


def test_join_rank_breaks_ties_by_id():
    joins = [(day(1), 11), (day(1), 10)]
    assert join_rank((day(1), 10), joins) == 1
    assert join_rank((day(1), 11), joins) == 2


def test_answers_lists_what_was_chosen_per_question():
    roles = {MEMBER, EARLY, PERU, AVISOS, EVENTOS}
    assert answers([STAGE, COUNTRY, NOTICES], roles) == [
        ("¿En qué etapa estás?", ["Early Career"]),
        ("¿De qué país eres?", ["Perú"]),
        ("¿Qué avisos quieres recibir?", ["Avisos", "Eventos"]),
    ]


def test_answers_skips_unanswered_questions():
    # Member lo dan todas las opciones de etapa: por sí solo no es una respuesta.
    assert answers([STAGE, COUNTRY, NOTICES], {MEMBER, ACTIVIDADES}) == [
        ("¿Qué avisos quieres recibir?", ["Actividades"]),
    ]


def test_onboarding_role_ids_includes_the_common_role():
    ids = onboarding_role_ids([STAGE, NOTICES])
    assert MEMBER in ids and EARLY in ids and ACTIVIDADES in ids
    assert PERU not in ids

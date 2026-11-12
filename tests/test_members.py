from types import SimpleNamespace

import discord

from rakim.events.members import questions
from rakim.members import Option, Question, own_roles, role_counts, tally

MEMBER, EARLY, MID, SENIOR = 1, 2, 3, 4
PERU, COLOMBIA, MEXICO = 11, 12, 13
AVISOS, EVENTOS, ACTIVIDADES = 21, 22, 23

# Como en el servidor: cada opción de etapa da su rol y, además, Member.
STAGE = Question(
    "¿En qué etapa estás?",
    [
        Option("Early Career", frozenset({EARLY, MEMBER})),
        Option("Mid level", frozenset({MID, MEMBER})),
        Option("Senior", frozenset({SENIOR, MEMBER})),
    ],
    multiple=False,
)
COUNTRY = Question(
    "¿De qué país eres?",
    [
        Option("Perú", frozenset({PERU})),
        Option("Colombia", frozenset({COLOMBIA})),
        Option("México", frozenset({MEXICO})),
    ],
    multiple=False,
)
NOTICES = Question(
    "¿Qué avisos quieres recibir?",
    [
        Option("Avisos", frozenset({AVISOS})),
        Option("Eventos", frozenset({EVENTOS})),
        Option("Actividades", frozenset({ACTIVIDADES})),
    ],
    multiple=True,
)


def test_a_role_shared_by_every_option_does_not_identify_the_choice():
    assert own_roles(STAGE) == [
        frozenset({EARLY}),
        frozenset({MID}),
        frozenset({SENIOR}),
    ]


def test_an_option_without_its_own_role_keeps_all_of_them():
    q = Question("x", [Option("a", frozenset({1})), Option("b", frozenset({1}))], False)
    assert own_roles(q) == [frozenset({1}), frozenset({1})]


def test_counts_the_stage_by_its_own_role_not_by_member():
    members = [{MEMBER, EARLY}, {MEMBER, EARLY}, {MEMBER, SENIOR}, {MEMBER}]
    rows, none = tally(STAGE, members)
    assert rows == [("Early Career", 2), ("Senior", 1), ("Mid level", 0)]
    assert none == 1  # tiene Member, pero no eligió etapa


def test_keeps_the_onboarding_order_on_ties():
    rows, none = tally(COUNTRY, [{MEXICO}, {PERU}, set()])
    assert rows == [("Perú", 1), ("México", 1), ("Colombia", 0)]
    assert none == 1


def test_multiple_choice_rows_can_add_up_to_more_than_the_members():
    members = [{AVISOS, EVENTOS, ACTIVIDADES}, {ACTIVIDADES}, set()]
    rows, none = tally(NOTICES, members)
    assert rows == [("Actividades", 2), ("Avisos", 1), ("Eventos", 1)]
    assert sum(n for _, n in rows) > len(members)
    assert none == 1


def test_counts_members_per_role():
    roles = [(PERU, "Perú"), (COLOMBIA, "Colombia"), (MEMBER, "Member")]
    members = [{MEMBER, PERU}, {MEMBER, COLOMBIA}, {MEMBER}]
    assert role_counts(roles, members) == [
        ("Member", 3),
        ("Perú", 1),
        ("Colombia", 1),
    ]


def role(role_id, name):
    return SimpleNamespace(id=role_id, name=name)


def option(title, roles, emoji=None):
    partial = discord.PartialEmoji(name=emoji) if emoji else None
    return SimpleNamespace(title=title, roles=roles, emoji=partial)


def prompt(title, options, single_select=True):
    return SimpleNamespace(title=title, options=options, single_select=single_select)


def test_reads_the_questions_with_short_labels_and_emojis():
    member = role(MEMBER, "Member")
    onboarding = SimpleNamespace(
        prompts=[
            prompt(
                "¿En qué etapa estás?",
                [
                    option(
                        "Estoy empezando (estudiante, autodidacta, trainee o junior)",
                        [role(EARLY, "Early Career"), member],
                        emoji="🌱",
                    ),
                    option("Ya trabajo", [role(MID, "Mid level"), member], "🌿"),
                ],
            ),
            prompt(
                "¿Qué avisos quieres recibir?",
                [option("Actividades", [role(ACTIVIDADES, "🎲 Actividades")], "🎲")],
                single_select=False,
            ),
            # Una pregunta que solo lleva a canales no se cuenta.
            prompt("¿Qué buscas?", [option("Feedback", [])]),
        ]
    )
    stage, notices = questions(onboarding)
    assert [o.label for o in stage.options] == ["🌱 Early Career", "🌿 Mid level"]
    assert stage.options[0].role_ids == {EARLY, MEMBER}
    assert not stage.multiple
    # El emoji no se repite si el rol ya lo lleva en el nombre.
    assert [o.label for o in notices.options] == ["🎲 Actividades"]
    assert notices.multiple

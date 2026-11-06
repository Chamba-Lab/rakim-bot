import re

from rakim import messages
from rakim.invites import InviteInfo


class FakeSettings:
    intro_channel_id = 111111111111111111
    ask_feedback_channel_id = 222222222222222222
    links_channel_id = 444444444444444444


def invite(code="abc", uses=3, inviter_id=100000000000000001):
    return InviteInfo(code, uses, 0, inviter_id)


def test_welcome_mentions_the_person_and_the_channels():
    text = messages.welcome(999999999999999999, FakeSettings())
    assert "<@999999999999999999>" in text
    for channel in (
        111111111111111111,
        222222222222222222,
        444444444444444444,
    ):
        assert f"<#{channel}>" in text


def test_welcome_fits_in_a_discord_message():
    assert len(messages.welcome(1, FakeSettings())) <= 2000


def test_welcome_uses_a_single_emoji():
    text = messages.welcome(1, FakeSettings())
    emojis = re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", text)
    assert len(emojis) == 1


def test_bump_reminder_mentions_the_role_when_configured():
    assert (
        messages.bump_reminder(123, None, 120)
        == "<@&123> Pasaron 120 minutos. Toca hacer `/bump`."
    )


def test_bump_reminder_mentions_a_person_when_configured():
    assert (
        messages.bump_reminder(None, 456, 120)
        == "<@456> Pasaron 120 minutos. Toca hacer `/bump`."
    )


def test_bump_reminder_works_without_a_role():
    assert (
        messages.bump_reminder(None, None, 120)
        == "Pasaron 120 minutos. Toca hacer `/bump`."
    )


def test_describes_the_used_invite_with_its_label_creator_and_uses():
    text = messages.describe_invites([invite()], {"abc": "Web y redes"})
    assert text == "Web y redes (`abc`) · creada por <@100000000000000001> · 3 usos"


def test_describes_a_bare_code_with_singular_use():
    text = messages.describe_invites([invite(uses=1, inviter_id=None)], {})
    assert text == "`abc` · 1 uso"


def test_explains_when_it_could_not_be_determined():
    assert "No se pudo determinar" in messages.describe_invites([], {})


def test_lists_the_candidates_when_ambiguous():
    text = messages.describe_invites([invite("a"), invite("b")], {"a": "Disboard"})
    assert text == "No se pudo determinar. Posibles: Disboard, `b`"


def test_invites_report_groups_codes_by_label_and_sorts():
    invites = {
        "a": InviteInfo("a", 5, 0, None),
        "b": InviteInfo("b", 2, 0, None),
        "c": InviteInfo("c", 9, 0, None),
        "d": InviteInfo("d", 0, 0, None),
    }
    labels = {"a": "Web", "b": "Web", "c": "TikTok", "d": "LinkedIn"}
    text = messages.invites_report(invites, labels, include_all=True)
    assert text.index("**TikTok**: 9") < text.index("**Web**: 7")
    assert "**LinkedIn**: 0" in text
    assert "Total: 16" in text


def test_invites_report_shows_unlabeled_codes_and_handles_none():
    text = messages.invites_report(
        {"x": InviteInfo("x", 1, 0, None)}, {}, include_all=True
    )
    assert "`x`" in text
    assert "No hay" in messages.invites_report({}, {})


def test_invites_report_defaults_to_registered_invites_only():
    invites = {"a": InviteInfo("a", 5, 0, None), "x": InviteInfo("x", 8, 0, None)}
    text = messages.invites_report(invites, {"a": "Web"})
    assert "**Web**: 5" in text
    assert "`x`" not in text
    assert "Total: 5" in text
    assert "`x`" in messages.invites_report(invites, {"a": "Web"}, include_all=True)


def test_invites_report_explains_when_nothing_is_registered():
    text = messages.invites_report({"x": InviteInfo("x", 8, 0, None)}, {})
    assert "todas" in text

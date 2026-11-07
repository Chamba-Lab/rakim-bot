from datetime import UTC, datetime
from types import SimpleNamespace

from rakim import messages
from rakim.health import Check, check_setup
from rakim.invites import InviteInfo

ALL = {"view_channel", "send_messages", "embed_links"}


def channel(allowed):
    return SimpleNamespace(
        permissions_for=lambda me: SimpleNamespace(**{p: p in allowed for p in ALL})
    )


def guild(channels, manage=True):
    return SimpleNamespace(
        me=SimpleNamespace(guild_permissions=SimpleNamespace(manage_guild=manage)),
        get_channel=channels.get,
    )


def settings(labels=None):
    return SimpleNamespace(
        log_channel_id=1,
        bump_channel_id=2,
        welcome_channel_id=3,
        intro_channel_id=4,
        ask_feedback_channel_id=5,
        links_channel_id=6,
        invite_labels=labels or {},
    )


def healthy_channels():
    return {1: channel(ALL), 2: channel(ALL), 3: channel(ALL)} | {
        n: channel({"view_channel"}) for n in (4, 5, 6)
    }


def by_name(checks):
    return {c.name: c for c in checks}


def test_everything_in_order():
    invites = {"abc": InviteInfo("abc", 1, 0, None)}
    checks = check_setup(guild(healthy_channels()), settings({"abc": "Web"}), invites)
    assert all(c.ok for c in checks)
    assert "1 registradas" in by_name(checks)["Invitaciones"].detail


def test_reports_a_missing_manage_server_permission():
    checks = check_setup(guild(healthy_channels(), manage=False), settings(), {})
    assert not by_name(checks)["Gestionar servidor"].ok


def test_reports_a_channel_that_does_not_exist():
    channels = healthy_channels()
    del channels[2]
    checks = by_name(check_setup(guild(channels), settings(), {}))
    assert not checks["Canal de bump"].ok
    assert checks["Canal de logs"].ok


def test_reports_which_permissions_are_missing_in_a_channel():
    channels = healthy_channels() | {1: channel({"view_channel"})}
    log = by_name(check_setup(guild(channels), settings(), {}))["Canal de logs"]
    assert not log.ok
    assert "enviar mensajes" in log.detail
    assert "insertar enlaces" in log.detail


def test_flags_a_registered_code_that_matches_no_invite():
    checks = check_setup(guild(healthy_channels()), settings({"typo": "Web"}), {})
    invites = by_name(checks)["Invitaciones"]
    assert not invites.ok
    assert "`typo`" in invites.detail


def test_reports_unreadable_invites():
    checks = check_setup(guild(healthy_channels()), settings(), None)
    assert not by_name(checks)["Invitaciones"].ok


def test_status_embed_shows_ok_and_failures():
    good = messages.status_embed([Check("A", True)], 0.05, None, None)
    assert good.title == "Estado de Rakim"
    assert "✔ **A**" in (good.description or "")
    assert good.fields[0].value == "50 ms"
    assert good.fields[-1].value == "sin aviso pendiente"

    bad = messages.status_embed(
        [Check("A", True), Check("B", False, "falta algo")],
        0.05,
        datetime.now(UTC),
        1_800_000_000.0,
    )
    assert bad.title == "Rakim tiene pendientes"
    assert "✘ **B**: falta algo" in (bad.description or "")

from datetime import UTC, datetime
from types import SimpleNamespace

from rakim import messages
from rakim.health import Check, check_setup
from rakim.invites import InviteInfo

ALL = {"view_channel", "send_messages", "embed_links", "mention_everyone"}


def channel(allowed):
    return SimpleNamespace(
        permissions_for=lambda me: SimpleNamespace(**{p: p in allowed for p in ALL})
    )


def guild(channels, manage=True, roles=None):
    return SimpleNamespace(
        me=SimpleNamespace(guild_permissions=SimpleNamespace(manage_guild=manage)),
        get_channel=channels.get,
        get_role=(roles or {}).get,
    )


def settings(
    labels=None, topic_times=(), topic_role=None, countries=(), stages=(), notices=()
):
    return SimpleNamespace(
        country_roles=list(countries),
        stage_roles=list(stages),
        notification_roles=list(notices),
        topic_times=list(topic_times),
        daily_topic_role_id=topic_role,
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


def test_the_daily_topic_needs_embeds_in_the_general_channel():
    channels = healthy_channels() | {3: channel({"view_channel", "send_messages"})}
    off = by_name(check_setup(guild(channels), settings(), {}))
    assert off["Canal general"].ok
    on = by_name(check_setup(guild(channels), settings(topic_times=["18:00"]), {}))
    assert "insertar enlaces" in on["Canal general"].detail


def test_the_daily_topic_role_must_exist():
    s = settings(topic_times=["18:00"], topic_role=9)
    role = by_name(check_setup(guild(healthy_channels()), s, {}))
    assert role["Rol del tema del día"].detail == "no existe"


def test_the_daily_topic_role_must_be_mentionable_in_the_general_channel():
    s = settings(topic_times=["18:00"], topic_role=9)
    closed = {9: SimpleNamespace(mentionable=False)}
    no_permission = healthy_channels() | {3: channel(ALL - {"mention_everyone"})}

    checks = by_name(check_setup(guild(no_permission, roles=closed), s, {}))
    assert not checks["Rol del tema del día"].ok

    checks = by_name(check_setup(guild(healthy_channels(), roles=closed), s, {}))
    assert checks["Rol del tema del día"].ok

    mentionable = {9: SimpleNamespace(mentionable=True)}
    checks = by_name(check_setup(guild(no_permission, roles=mentionable), s, {}))
    assert checks["Rol del tema del día"].ok


def test_no_role_check_when_the_daily_topic_is_off():
    checks = by_name(check_setup(guild(healthy_channels()), settings(topic_role=9), {}))
    assert "Rol del tema del día" not in checks


def test_flags_member_roles_that_do_not_exist():
    roles = {10: SimpleNamespace(mentionable=False)}
    s = settings(countries=[10, 11], stages=[10], notices=[12])
    checks = by_name(check_setup(guild(healthy_channels(), roles=roles), s, {}))
    assert not checks["Roles de país"].ok
    assert checks["Roles de país"].detail == "1 de 2; no existen: 11"
    assert checks["Roles de etapa"].ok
    assert checks["Roles de notificación"].detail == "0 de 1; no existen: 12"


def test_no_member_role_checks_when_not_configured():
    checks = by_name(check_setup(guild(healthy_channels()), settings(), {}))
    assert "Roles de país" not in checks
    assert "Roles de etapa" not in checks

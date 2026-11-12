import pytest
from pydantic import ValidationError

from rakim.config import Settings

VALID = {
    "DISCORD_TOKEN": "token",
    "GUILD_ID": "100000000000000001",
    "WELCOME_CHANNEL_ID": "100000000000000002",
    "INTRO_CHANNEL_ID": "100000000000000003",
    "ASK_FEEDBACK_CHANNEL_ID": "100000000000000004",
    "LINKS_CHANNEL_ID": "100000000000000006",
    "LOG_CHANNEL_ID": "100000000000000007",
    "BUMP_CHANNEL_ID": "100000000000000008",
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Las pruebas no deben leer el entorno ni el .env de quien las ejecuta."""
    for key in [
        *VALID,
        "BUMP_ROLE_ID",
        "INVITE_LABELS",
        "BUMP_SUCCESS_PATTERN",
        "WELCOME_WAIT_SYSTEM_MESSAGE",
        "DAILY_TOPIC_TIMES",
        "DAILY_TOPIC_ROLE_ID",
        "DAILY_TOPIC_PRESETS",
        "COUNTRY_ROLE_IDS",
        "STAGE_ROLE_IDS",
    ]:
        monkeypatch.delenv(key, raising=False)


def settings(monkeypatch, **overrides):
    for key, value in {**VALID, **overrides}.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def test_applies_defaults(monkeypatch):
    s = settings(monkeypatch)
    assert s.disboard_bot_id == 302050872383242240
    assert s.bump_cooldown_minutes == 120
    assert s.bump_role_id is None
    assert s.invite_labels == {}
    assert s.state_path == "data/state.json"
    assert s.welcome_wait_system_message is True
    assert s.topic_times == []  # el tema del día nace apagado
    assert s.daily_topic_role_id is None
    assert s.topic_preset_ids == [
        "employability",
        "icebreaker-culture",
        "daily-learning",
    ]


def test_welcome_can_stop_waiting_for_the_system_message(monkeypatch):
    s = settings(monkeypatch, WELCOME_WAIT_SYSTEM_MESSAGE="false")
    assert s.welcome_wait_system_message is False


def test_empty_variable_counts_as_undefined(monkeypatch):
    s = settings(monkeypatch, BUMP_ROLE_ID="", INVITE_LABELS="")
    assert s.bump_role_id is None
    assert s.invite_labels == {}


def test_reads_invite_labels_and_bump_pattern(monkeypatch):
    s = settings(
        monkeypatch,
        INVITE_LABELS='{"abc": "Web y redes"}',
        BUMP_SUCCESS_PATTERN="bump (done|realizado)",
    )
    assert s.invite_labels == {"abc": "Web y redes"}
    assert s.bump_regex.search("Bump REALIZADO")


def test_reports_every_problem_at_once(monkeypatch):
    monkeypatch.delenv("LOG_CHANNEL_ID", raising=False)
    with pytest.raises(ValidationError) as error:
        settings(monkeypatch, GUILD_ID="x", LOG_CHANNEL_ID="")
    fields = {e["loc"][0] for e in error.value.errors()}
    assert {"guild_id", "log_channel_id"} <= fields


def test_rejects_invalid_invite_labels(monkeypatch):
    with pytest.raises(Exception, match=r"invite_labels|INVITE_LABELS"):
        settings(monkeypatch, INVITE_LABELS="no es json")


def test_reads_the_daily_topic(monkeypatch):
    s = settings(
        monkeypatch,
        DAILY_TOPIC_TIMES="18:00",
        DAILY_TOPIC_ROLE_ID="100000000000000009",
        DAILY_TOPIC_PRESETS="employability, daily-learning",
    )
    assert [t.hour for t in s.topic_times] == [18]
    assert s.daily_topic_role_id == 100000000000000009
    assert s.topic_preset_ids == ["employability", "daily-learning"]


def test_rejects_an_invalid_daily_topic_time_or_preset(monkeypatch):
    with pytest.raises(ValidationError) as error:
        settings(monkeypatch, DAILY_TOPIC_TIMES="6pm", DAILY_TOPIC_PRESETS="no-existe")
    fields = {e["loc"][0] for e in error.value.errors()}
    assert fields == {"daily_topic_times", "daily_topic_presets"}


def test_reads_the_member_role_ids(monkeypatch):
    s = settings(
        monkeypatch,
        COUNTRY_ROLE_IDS="100000000000000010, 100000000000000011",
    )
    assert s.country_roles == [100000000000000010, 100000000000000011]
    assert s.stage_roles == []


def test_rejects_an_invalid_member_role_id(monkeypatch):
    with pytest.raises(ValidationError) as error:
        settings(monkeypatch, STAGE_ROLE_IDS="100000000000000010, Senior")
    assert {e["loc"][0] for e in error.value.errors()} == {"stage_role_ids"}

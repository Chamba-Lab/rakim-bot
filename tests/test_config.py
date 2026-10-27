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
    for key in [*VALID, "BUMP_ROLE_ID", "INVITE_LABELS", "BUMP_SUCCESS_PATTERN"]:
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

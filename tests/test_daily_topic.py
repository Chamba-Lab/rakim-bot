import random
from datetime import time

import pytest

from rakim.daily_topic import LIMA, next_topic, parse_times, select_presets
from rakim.roulette import Preset, load_presets
from rakim.state import State


def seeded(seed):
    return random.Random(seed)  # noqa: S311 - semilla fija a propósito


A = Preset("a", "🅰️ A", ("a1", "a2", "a3"))
B = Preset("b", "🅱️ B", ("b1", "b2"))


def test_parses_lima_times():
    assert parse_times("18:00") == [time(18, 0, tzinfo=LIMA)]
    assert parse_times(" 9:30, 18:00 ") == [
        time(9, 30, tzinfo=LIMA),
        time(18, 0, tzinfo=LIMA),
    ]
    assert LIMA.utcoffset(None).total_seconds() == -5 * 3600


def test_no_times_means_the_feature_is_off():
    assert parse_times("") == []


@pytest.mark.parametrize("bad", ["18", "25:00", "18:60", "seis"])
def test_rejects_invalid_times(bad):
    with pytest.raises(ValueError, match="hora no válida"):
        parse_times(bad)


def test_selects_presets_by_id():
    assert select_presets([A, B], ["b"]) == [B]


def test_rejects_unknown_or_missing_presets():
    with pytest.raises(ValueError, match="desconocidos: z"):
        select_presets([A, B], ["a", "z"])
    with pytest.raises(ValueError, match="al menos un grupo"):
        select_presets([A, B], [])


def test_the_default_presets_exist_in_roulette_json():
    ids = ["employability", "icebreaker-culture", "daily-learning"]
    assert len(select_presets(load_presets(), ids)) == 3


def test_uses_every_topic_before_repeating():
    rng = seeded(1)
    used: list[str] = []
    seen = []
    for _ in range(5):
        _, topic, used = next_topic([A, B], used, rng)
        seen.append(topic)
    assert sorted(seen) == ["a1", "a2", "a3", "b1", "b2"]


def test_a_new_cycle_does_not_repeat_the_last_topic():
    for seed in range(20):
        _, topic, used = next_topic([B], ["b2", "b1"], seeded(seed))
        assert topic == "b2"
        assert used == ["b2"]


def test_forgets_topics_that_no_longer_exist():
    _, topic, used = next_topic([B], ["b1", "borrado"], seeded(0))
    assert topic == "b2"
    assert used == ["b1", "b2"]


def test_returns_the_preset_of_the_topic():
    preset, topic, _ = next_topic([A, B], ["a1", "a2", "a3"], seeded(0))
    assert preset is B
    assert topic in B.options


def test_state_keeps_the_used_topics(tmp_path):
    path = str(tmp_path / "state.json")
    state = State(path)
    state.used_topics = ["¿Qué estás aprendiendo estos días?"]
    state.bump_due_at = 123.0
    state.save()
    again = State(path)
    assert again.used_topics == ["¿Qué estás aprendiendo estos días?"]
    assert again.bump_due_at == 123.0


def test_state_from_before_the_daily_topic_still_loads(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"bump_due_at": 5.0}')
    state = State(str(path))
    assert state.bump_due_at == 5.0
    assert state.used_topics == []

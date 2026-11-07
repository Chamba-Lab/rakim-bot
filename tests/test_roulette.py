import random

from rakim import messages
from rakim.roulette import Preset, find_preset, load_presets, pick

A = Preset("tech-debates", "⚔️ Debates Tech", ("uno", "dos"))
B = Preset("icebreaker-culture", "⚡ Rompehielos", ("tres",))


def test_the_bundled_topics_load_and_fit_a_choice_menu():
    presets = load_presets()
    assert presets
    assert len(presets) <= 25  # límite de opciones de un comando `/` de Discord
    for p in presets:
        assert p.options
        assert len(p.name) <= 100


def test_finds_a_preset_by_id_or_by_part_of_its_name():
    assert find_preset([A, B], "tech-debates") is A
    assert find_preset([A, B], "rompehielos") is B
    assert find_preset([A, B], "  DEBATES ") is A
    assert find_preset([A, B], "nada") is None
    assert find_preset([A, B], "") is None


def test_picks_from_the_chosen_group_only():
    for seed in range(20):
        preset, topic = pick([A, B], only=B, rng=random.Random(seed))  # noqa: S311 - semilla fija a propósito
        assert preset is B
        assert topic == "tres"


def test_never_repeats_the_last_topic_when_there_is_another():
    for seed in range(20):
        _, topic = pick([A], last="uno", rng=random.Random(seed))  # noqa: S311 - semilla fija a propósito
        assert topic == "dos"


def test_repeats_only_when_there_is_no_other_topic():
    assert pick([B], last="tres")[1] == "tres"


def test_roulette_embed_shows_the_topic_and_a_single_emoji():
    embed = messages.roulette_embed(A.name, "uno")
    assert embed.description == "**uno**"
    assert embed.footer.text is not None
    assert A.name in embed.footer.text
    assert "/ruleta" in embed.footer.text


def test_unknown_group_lists_the_valid_ones():
    text = messages.roulette_unknown([A, B])
    assert "`tech-debates`" in text
    assert "`icebreaker-culture`" in text

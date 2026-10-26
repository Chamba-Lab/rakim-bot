import asyncio
import re

from rakim.bump import BumpReminder, is_bump_success
from rakim.state import State

DISBOARD = 302050872383242240
PATTERN = re.compile("bump done", re.IGNORECASE)
COOLDOWN = 7200.0


def test_recognises_disboards_confirmation():
    texts = ["Bump done! Check it out on DISBOARD."]
    assert is_bump_success(DISBOARD, texts, DISBOARD, PATTERN)


def test_ignores_the_same_text_from_someone_else():
    assert not is_bump_success(1, ["Bump done!"], DISBOARD, PATTERN)


def test_ignores_the_cooldown_reply():
    texts = ["Please wait another 42 minutes until the server can be bumped"]
    assert not is_bump_success(DISBOARD, texts, DISBOARD, PATTERN)


def test_handles_messages_without_text():
    assert not is_bump_success(DISBOARD, [], DISBOARD, PATTERN)


class Clock:
    """Reloj y `sleep` falsos: dormir solo adelanta la hora y anota cuánto."""

    def __init__(self, start=1_000_000.0):
        self.time = start
        self.sleeps: list[float] = []

    def now(self):
        return self.time

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.time += seconds


def make(tmp_path, clock, send):
    state = State(str(tmp_path / "state.json"))
    return BumpReminder(state, COOLDOWN, send, clock.now, clock.sleep), state


def run(coro):
    return asyncio.run(coro)


def test_reminds_after_the_cooldown(tmp_path):
    clock, sent = Clock(), []

    async def send():
        sent.append(clock.now())

    async def scenario():
        reminder, state = make(tmp_path, clock, send)
        reminder.schedule()
        await reminder.task
        return state

    state = run(scenario())
    assert clock.sleeps == [COOLDOWN]
    assert sent == [1_000_000.0 + COOLDOWN]
    assert state.bump_due_at is None


def test_a_new_bump_replaces_the_pending_reminder(tmp_path):
    clock, sent = Clock(), []

    async def send():
        sent.append(1)

    async def scenario():
        reminder, _ = make(tmp_path, clock, send)
        reminder.schedule()
        first = reminder.task
        reminder.schedule()
        await reminder.task
        return first

    first = run(scenario())
    assert first.cancelled()
    assert sent == [1]


def test_resumes_the_pending_reminder_after_a_restart(tmp_path):
    clock, sent = Clock(), []

    async def send():
        sent.append(1)

    async def scenario():
        reminder, _ = make(tmp_path, clock, send)
        reminder.schedule()
        reminder.task.cancel()  # el proceso anterior se apaga antes de avisar

        restarted, _ = make(tmp_path, clock, send)
        restarted.start()
        await restarted.task

    run(scenario())
    assert sent == [1]


def test_reminds_immediately_if_it_expired_while_off(tmp_path):
    clock, sent = Clock(), []

    async def send():
        sent.append(1)

    async def scenario():
        reminder, _ = make(tmp_path, clock, send)
        reminder.schedule()
        reminder.task.cancel()
        clock.time += COOLDOWN * 2  # el bot estuvo apagado más de un enfriamiento

        restarted, _ = make(tmp_path, clock, send)
        restarted.start()
        await restarted.task

    run(scenario())
    assert sent == [1]
    assert clock.sleeps == [0.0]


def test_does_not_repeat_a_reminder_already_sent(tmp_path):
    clock, sent = Clock(), []

    async def send():
        sent.append(1)

    async def scenario():
        reminder, _ = make(tmp_path, clock, send)
        reminder.schedule()
        await reminder.task

        restarted, _ = make(tmp_path, clock, send)
        restarted.start()
        return restarted.task

    assert run(scenario()) is None
    assert sent == [1]


def test_clears_the_reminder_even_if_sending_fails(tmp_path):
    clock = Clock()

    async def send():
        raise RuntimeError("sin permisos")

    async def scenario():
        reminder, state = make(tmp_path, clock, send)
        reminder.schedule()
        await reminder.task
        return state

    assert run(scenario()).bump_due_at is None


def test_recognises_the_real_disboard_confirmation():
    """Texto real de Disboard, copiado de una captura del 26 oct 2026 (va en el embed)."""
    from rakim.config import Settings

    embed_title = "DISBOARD: The Public Server List"
    embed_description = (
        "Bump done! 👍\n"
        "Check it out [on DISBOARD](https://disboard.org/server/1).\n\n"
        "**Make your listing feel like your server.**\n"
        "Customize this server's listing, get review controls, and explore server insights."
    )
    default_pattern = Settings.model_fields["bump_success_pattern"].default
    pattern = re.compile(default_pattern, re.IGNORECASE)
    assert is_bump_success(
        DISBOARD, [embed_title, embed_description], DISBOARD, pattern
    )

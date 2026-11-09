import asyncio
from types import SimpleNamespace

from rakim import welcome


def fake_bot(wait_system_message: bool):
    sent = []

    async def send(channel_id, **kwargs):
        sent.append(kwargs["content"])

    bot = SimpleNamespace(
        settings=SimpleNamespace(
            welcome_wait_system_message=wait_system_message,
            welcome_channel_id=1,
            intro_channel_id=2,
            ask_feedback_channel_id=3,
            links_channel_id=4,
        ),
        system_messages={},
        welcomed={},
        send=send,
    )
    return bot, sent


def member(member_id=10):
    return SimpleNamespace(bot=False, id=member_id)


def fast(monkeypatch):
    monkeypatch.setattr(welcome, "SYSTEM_MESSAGE_TIMEOUT", 0.05)
    monkeypatch.setattr(welcome, "FIXED_DELAY", 0.05)
    monkeypatch.setattr(welcome, "AFTER_SYSTEM_MESSAGE_DELAY", 0.05)


def test_pauses_after_the_system_message_before_greeting(monkeypatch):
    fast(monkeypatch)
    bot, sent = fake_bot(wait_system_message=True)

    async def scenario():
        task = asyncio.create_task(welcome.greet_in_order(bot, member()))
        await asyncio.sleep(0)
        welcome.system_message_arrived(bot, 10)
        await asyncio.sleep(0.01)
        assert sent == []  # llegó el mensaje nativo, pero aún corre la pausa
        await task

    asyncio.run(scenario())
    assert len(sent) == 1


def test_greets_after_the_system_message(monkeypatch):
    fast(monkeypatch)
    bot, sent = fake_bot(wait_system_message=True)

    async def scenario():
        task = asyncio.create_task(welcome.greet_in_order(bot, member()))
        await asyncio.sleep(0)
        assert sent == []  # aún espera el mensaje nativo
        welcome.system_message_arrived(bot, 10)
        await task

    asyncio.run(scenario())
    assert len(sent) == 1
    assert bot.system_messages == {}


def test_system_message_that_came_first_is_not_lost(monkeypatch):
    monkeypatch.setattr(welcome, "SYSTEM_MESSAGE_TIMEOUT", 5.0)
    monkeypatch.setattr(welcome, "AFTER_SYSTEM_MESSAGE_DELAY", 0.05)
    bot, sent = fake_bot(wait_system_message=True)
    welcome.system_message_arrived(bot, 10)

    asyncio.run(asyncio.wait_for(welcome.greet_in_order(bot, member()), 1.0))
    assert len(sent) == 1


def test_greets_anyway_when_the_system_message_never_comes(monkeypatch):
    fast(monkeypatch)
    bot, sent = fake_bot(wait_system_message=True)

    asyncio.run(welcome.greet_in_order(bot, member()))
    assert len(sent) == 1
    assert bot.system_messages == {}


def test_fixed_delay_when_not_waiting_for_the_system_message(monkeypatch):
    fast(monkeypatch)
    bot, sent = fake_bot(wait_system_message=False)

    async def scenario():
        task = asyncio.create_task(welcome.greet_in_order(bot, member()))
        await asyncio.sleep(0)
        assert sent == []  # la pausa fija todavía no termina
        await task

    asyncio.run(scenario())
    assert len(sent) == 1
    assert bot.system_messages == {}


def test_does_not_greet_twice(monkeypatch):
    fast(monkeypatch)
    bot, sent = fake_bot(wait_system_message=False)

    async def scenario():
        await asyncio.gather(
            welcome.greet_in_order(bot, member()),
            welcome.greet_in_order(bot, member()),
        )

    asyncio.run(scenario())
    assert len(sent) == 1


def test_remembers_only_the_most_recent_greetings(monkeypatch):
    monkeypatch.setattr(welcome, "MAX_WELCOMED", 2)
    bot, _ = fake_bot(wait_system_message=False)
    for n in (1, 2, 3):
        asyncio.run(welcome.greet(bot, member(n)))
    assert list(bot.welcomed) == [2, 3]


def test_does_not_keep_system_messages_nobody_waits_for():
    bot, _ = fake_bot(wait_system_message=False)
    welcome.system_message_arrived(bot, 10)
    assert bot.system_messages == {}

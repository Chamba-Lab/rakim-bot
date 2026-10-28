import asyncio

import discord

from . import messages
from .bot import RakimBot

# Cuánto se espera el mensaje nativo de Discord antes de saludar sin él.
SYSTEM_MESSAGE_TIMEOUT = 10.0
# Pausa fija cuando no se espera el mensaje nativo (está desactivado en el servidor).
FIXED_DELAY = 5.0


def system_message_arrived(bot: RakimBot, member_id: int) -> None:
    """Llegó el mensaje nativo de entrada de este miembro: avisa a quien lo espera.

    Si llegó antes de que alguien lo espere, el aviso queda guardado.
    """
    bot.system_messages.setdefault(member_id, asyncio.Event()).set()


async def wait_for_system_message(bot: RakimBot, member_id: int) -> None:
    """Espera el mensaje nativo de entrada; si no llega a tiempo, sigue sin él."""
    event = bot.system_messages.setdefault(member_id, asyncio.Event())
    try:
        await asyncio.wait_for(event.wait(), SYSTEM_MESSAGE_TIMEOUT)
    except TimeoutError:
        pass
    finally:
        bot.system_messages.pop(member_id, None)


async def greet_in_order(bot: RakimBot, member: discord.Member) -> None:
    """Saluda después del mensaje nativo de Discord, para que el saludo no salga antes.

    Con `welcome_wait_system_message` espera ese mensaje (con un máximo); sin él,
    una pausa fija da a Discord el mismo margen para dejar listo al miembro.
    """
    if member.bot or member.id in bot.welcomed:
        return
    if bot.settings.welcome_wait_system_message:
        await wait_for_system_message(bot, member.id)
    else:
        await asyncio.sleep(FIXED_DELAY)
    await greet(bot, member)


async def greet(bot: RakimBot, member: discord.Member) -> None:
    """Saluda a un miembro nuevo en el canal general."""
    if member.bot or member.id in bot.welcomed:
        return
    bot.welcomed.add(member.id)
    try:
        await bot.send(
            bot.settings.welcome_channel_id,
            content=messages.welcome(member.id, bot.settings),
            allowed_mentions=discord.AllowedMentions(users=[member]),
        )
    except Exception:
        bot.welcomed.discard(member.id)  # permite reintentar si el envío falló
        raise

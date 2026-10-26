import discord

from . import messages
from .bot import RakimBot


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

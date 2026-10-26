import discord

from .. import messages
from ..bot import RakimBot


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_member_remove(member: discord.Member) -> None:
        """Alguien salió del servidor (o lo sacaron): se registra en el log."""
        if member.guild.id == bot.settings.guild_id:
            await bot.send(
                bot.settings.log_channel_id, embed=messages.leave_embed(member)
            )

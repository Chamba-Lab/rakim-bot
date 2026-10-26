import discord

from ..bot import RakimBot
from ..welcome import greet


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_member_update(before: discord.Member, after: discord.Member) -> None:
        """Un miembro cambió. Solo interesa que dejó de estar `pending`: acaba de
        aceptar las reglas del Onboarding y ya puede escribir. Ese es el momento del saludo.
        """
        if (
            after.guild.id == bot.settings.guild_id
            and before.pending
            and not after.pending
        ):
            await greet(bot, after)

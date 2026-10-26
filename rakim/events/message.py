import logging

import discord

from ..bot import RakimBot
from ..bump import is_bump_success

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_message(message: discord.Message) -> None:
        """Llegó un mensaje: solo importa si es la confirmación de bump de Disboard."""
        if message.guild is None or message.guild.id != bot.settings.guild_id:
            return

        # El texto y los embeds de otros bots solo llegan con el intent message_content.
        texts = [message.content]
        for embed in message.embeds:
            texts += [embed.title or "", embed.description or ""]

        s = bot.settings
        if is_bump_success(message.author.id, texts, s.disboard_bot_id, s.bump_regex):
            log.info("Bump detectado; aviso programado")
            bot.bump.schedule()

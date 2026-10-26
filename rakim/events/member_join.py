import asyncio
import logging

import discord

from .. import messages
from ..bot import RakimBot
from ..invites import read_invites, used_invites
from ..welcome import greet

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_member_join(member: discord.Member) -> None:
        """Alguien entró: se registra en el log y, si ya puede escribir, se le saluda.

        Si aún debe aceptar las reglas (`pending`), el saludo espera a `on_member_update`.
        """
        if member.guild.id != bot.settings.guild_id:
            return
        tasks = [log_join(bot, member)]
        if not member.pending:
            tasks.append(greet(bot, member))

        # Son independientes: si falla el log, el saludo sale igual.
        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                log.error("Falló algo al recibir a %s", member.id, exc_info=result)


async def log_join(bot: RakimBot, member: discord.Member) -> None:
    """Registra la entrada con la invitación usada: la que subió de usos desde la última lectura."""
    async with bot.join_lock:
        after = await read_invites(member.guild)
        candidates = []
        if bot.invites is not None and after is not None:
            candidates = used_invites(bot.invites, after)
        if after is not None:
            bot.invites = after

    text = messages.describe_invites(candidates, bot.settings.invite_labels)
    await bot.send(bot.settings.log_channel_id, embed=messages.join_embed(member, text))

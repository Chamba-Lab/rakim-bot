import logging
from datetime import UTC, datetime

import discord

from .. import messages
from ..bot import RakimBot
from ..health import check_setup
from ..invites import read_invites

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_ready() -> None:
        """El bot terminó de conectarse: deja listo lo que necesita al arrancar."""
        if bot.started:  # Discord repite este evento al reconectar
            return
        bot.started = True
        bot.started_at = datetime.now(UTC)
        log.info("Rakim conectado como %s", bot.user)

        guild = bot.get_guild(bot.settings.guild_id)
        if guild is None:
            log.warning("El bot no está en el servidor configurado (GUILD_ID)")
        else:
            # Primera lectura de invitaciones, para compararlas en la primera entrada.
            bot.invites = await read_invites(guild)
            await report_problems(bot, guild)

        # Retoma un aviso de bump pendiente; aquí porque, si venció, se envía al instante.
        bot.bump.start()


async def report_problems(bot: RakimBot, guild: discord.Guild) -> None:
    """Al arrancar, avisa de lo que falte (permisos, canales, invitaciones mal escritas).

    Va al log y, si el canal de logs funciona, también allí: un fallo de permisos suele
    pasar desapercibido hasta que alguien entra o hace bump.
    """
    checks = check_setup(guild, bot.settings, bot.invites)
    failed = [c for c in checks if not c.ok]
    if not failed:
        log.info("Comprobación inicial: todo en orden")
        return
    for c in failed:
        log.warning("Comprobación inicial: %s: %s", c.name, c.detail)
    try:
        await bot.send(
            bot.settings.log_channel_id,
            embed=messages.status_embed(
                checks, bot.latency, bot.started_at, bot.state.bump_due_at
            ),
        )
    except Exception:
        log.exception("No se pudo avisar de los pendientes en el canal de logs")

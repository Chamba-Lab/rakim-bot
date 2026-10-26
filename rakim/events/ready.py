import logging

from ..bot import RakimBot
from ..invites import read_invites

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_ready() -> None:
        """El bot terminó de conectarse: deja listo lo que necesita al arrancar."""
        if bot.started:  # Discord repite este evento al reconectar
            return
        bot.started = True
        log.info("Rakim conectado como %s", bot.user)

        guild = bot.get_guild(bot.settings.guild_id)
        if guild is None:
            log.warning("El bot no está en el servidor configurado (GUILD_ID)")
        else:
            # Primera lectura de invitaciones, para compararlas en la primera entrada.
            bot.invites = await read_invites(guild)

        # Retoma un aviso de bump pendiente; aquí porque, si venció, se envía al instante.
        bot.bump.start()

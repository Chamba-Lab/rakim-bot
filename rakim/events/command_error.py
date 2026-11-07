import logging

from discord.ext import commands

from ..bot import RakimBot

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    @bot.listen()
    async def on_command_error(
        ctx: commands.Context[RakimBot], error: commands.CommandError
    ) -> None:
        """Falló un comando. Al escuchar este evento, discord.py deja de registrar los
        fallos, así que se registran aquí. Con `/` hay que responder algo; con mención,
        responder a quien no puede usar el comando solo haría ruido.
        """
        if isinstance(error, commands.MissingPermissions):
            if ctx.interaction:
                await ctx.reply(
                    "Necesitas el permiso Gestionar servidor.", ephemeral=True
                )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                f"Calma, vuelve a intentarlo en {error.retry_after:.0f} s.",
                ephemeral=True,
            )
        elif not isinstance(error, commands.CommandNotFound):
            log.error("Falló el comando %s", ctx.command, exc_info=error)

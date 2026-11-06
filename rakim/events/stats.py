import logging
from typing import Literal

from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..invites import read_invites

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    # Un solo comando con dos formas: `@Rakim invitaciones [todas]` y `/invitaciones [alcance]`.
    @commands.hybrid_command(  # type: ignore[arg-type]
        name="invitaciones",
        aliases=["invites"],
        description="Entradas por invitación (por defecto, solo las registradas)",
    )
    @app_commands.describe(alcance="«todas» incluye invitaciones sin registrar")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @commands.has_permissions(manage_guild=True)  # también para la forma con mención
    async def invitaciones(
        ctx: commands.Context[RakimBot], alcance: Literal["todas", "all"] | None = None
    ) -> None:
        # Es información interna: solo en el canal de logs o en el de bump.
        if ctx.guild is None or ctx.guild.id != bot.settings.guild_id:
            return
        if ctx.channel.id not in (
            bot.settings.log_channel_id,
            bot.settings.bump_channel_id,
        ):
            if ctx.interaction:  # con `/` hay que responder algo; con mención se ignora
                await ctx.reply(
                    "Este comando solo funciona en el canal de logs o en el de bump.",
                    ephemeral=True,
                )
            return
        invites = await read_invites(ctx.guild)
        if invites is None:
            await ctx.reply("No pude leer las invitaciones. Revisa mis permisos.")
            return
        await ctx.reply(
            messages.invites_report(
                invites, bot.settings.invite_labels, include_all=alcance is not None
            )
        )

    bot.add_command(invitaciones)

    @bot.listen()
    async def on_command_error(
        ctx: commands.Context[RakimBot], error: commands.CommandError
    ) -> None:
        # Mencionar al bot con otro texto no es un error. Al escuchar este evento,
        # discord.py deja de registrar los fallos, así que se registran aquí.
        if isinstance(error, commands.MissingPermissions):
            if ctx.interaction:  # con mención no se responde a quien no puede usarlo
                await ctx.reply(
                    "Necesitas el permiso Gestionar servidor.", ephemeral=True
                )
        elif not isinstance(error, commands.CommandNotFound):
            log.error("Falló el comando %s", ctx.command, exc_info=error)

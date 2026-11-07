from typing import Literal

from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..invites import read_invites


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
        if not bot.in_staff_channel(ctx.channel.id):
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
            embed=messages.invites_embed(
                invites, bot.settings.invite_labels, include_all=alcance is not None
            )
        )

    bot.add_command(invitaciones)

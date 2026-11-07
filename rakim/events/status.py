from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..health import check_setup
from ..invites import read_invites


async def setup(bot: RakimBot) -> None:
    @commands.hybrid_command(
        name="estado",
        aliases=["status"],
        description="Cómo está Rakim: permisos, canales e invitaciones",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def estado(ctx: commands.Context[RakimBot]) -> None:
        if ctx.guild is None or ctx.guild.id != bot.settings.guild_id:
            return
        if not bot.in_staff_channel(ctx.channel.id):
            if ctx.interaction:
                await ctx.reply(
                    "Este comando solo funciona en el canal de logs o en el de bump.",
                    ephemeral=True,
                )
            return
        checks = check_setup(ctx.guild, bot.settings, await read_invites(ctx.guild))
        # Efímero con `/`: el estado no necesita quedar en el canal.
        await ctx.reply(
            embed=messages.status_embed(
                checks, bot.latency, bot.started_at, bot.state.bump_due_at
            ),
            ephemeral=True,
        )

    bot.add_command(estado)

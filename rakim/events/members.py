import discord
from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..members import breakdown


async def setup(bot: RakimBot) -> None:
    # Cuenta a los miembros actuales por los roles de las preguntas del Onboarding. Es
    # aparte de `invitaciones`, que usa el acumulado de Discord (incluye a quienes salieron).
    @commands.hybrid_command(
        name="miembros",
        aliases=["members"],
        description="Miembros por país y por etapa, según el Onboarding",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @commands.has_permissions(manage_guild=True)  # también para la forma con mención
    async def miembros(ctx: commands.Context[RakimBot]) -> None:
        if ctx.guild is None or ctx.guild.id != bot.settings.guild_id:
            return
        if not bot.in_staff_channel(ctx.channel.id):
            if ctx.interaction:
                await ctx.reply(
                    "Este comando solo funciona en el canal de logs o en el de bump.",
                    ephemeral=True,
                )
            return
        await ctx.reply(embed=members_embed(ctx.guild, bot))

    bot.add_command(miembros)


def members_embed(guild: discord.Guild, bot: RakimBot) -> discord.Embed:
    # Con el intent `members`, la lista completa ya está en memoria: no hay llamadas a la API.
    # Quien no aceptó las reglas (`pending`) aún no terminó el Onboarding.
    counted = [
        {r.id for r in m.roles} for m in guild.members if not m.bot and not m.pending
    ]
    sections: list[tuple[str, list[tuple[str, int]] | None]] = []
    for title, role_ids in (
        ("Por país", bot.settings.country_roles),
        ("Por etapa", bot.settings.stage_roles),
    ):
        # Un rol borrado no se muestra; la comprobación inicial y `/estado` lo señalan.
        existing = [r for r in role_ids if guild.get_role(r) is not None]
        if not existing:
            sections.append((title, None))
            continue
        result = breakdown(counted, existing)
        rows = [(_role_name(guild, r), n) for r, n in result.rows]
        rows.append(("Sin responder", result.unanswered))
        sections.append((title, rows))
    return messages.members_embed(sections, len(counted))


def _role_name(guild: discord.Guild, role_id: int) -> str:
    role = guild.get_role(role_id)
    return role.name if role else str(role_id)

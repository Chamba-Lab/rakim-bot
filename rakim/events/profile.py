import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..profile import answers, join_rank, onboarding_role_ids
from .members import questions

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    # La tarjeta de miembro, para cualquiera y en cualquier canal. Es pública porque es
    # social (sirve para presentarse); el enfriamiento por persona evita que llene un canal.
    # Todo sale de lo que el intent `members` ya tiene en memoria y del Onboarding.
    @commands.hybrid_command(  # type: ignore[arg-type]
        name="perfil",
        aliases=["profile"],
        description="Muestra tu tarjeta de miembro de Chamba Lab (o la de otra persona)",
    )
    @app_commands.describe(persona="De quién (si no, la tuya)")
    @app_commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def perfil(
        ctx: commands.Context[RakimBot], persona: discord.Member | None = None
    ) -> None:
        guild = ctx.guild
        if guild is None or guild.id != bot.settings.guild_id:
            return
        member = persona or ctx.author
        if not isinstance(member, discord.Member):
            return
        if member.bot or member.pending or member.joined_at is None:
            # No hay tarjeta que mostrar: no se gasta el enfriamiento.
            ctx.command.reset_cooldown(ctx)  # type: ignore[union-attr]
            text = (
                messages.profile_bot()
                if member.bot
                else messages.profile_pending(member.id)
            )
            await ctx.reply(text, ephemeral=True)
            return

        try:
            # Pide Gestionar servidor, el permiso que ya usa para las invitaciones.
            found = questions(await guild.onboarding())
        except discord.HTTPException:
            # Sin el Onboarding, la tarjeta sale igual, sin sus respuestas.
            log.warning("No se pudo leer el Onboarding para /perfil")
            found = []

        # Puesto entre las personas del servidor (también las que aún no aceptan las
        # reglas: ya entraron, y así el número no cambia cuando las aceptan).
        joins = [
            (m.joined_at, m.id) for m in guild.members if not m.bot and m.joined_at
        ]
        roles = {r.id for r in member.roles}
        skip = onboarding_role_ids(found)
        # De mayor a menor, sin @everyone ni los roles de bots o integraciones; el de
        # Booster sí se muestra.
        others = [
            r
            for r in reversed(member.roles)
            if not r.is_default()
            and not r.is_bot_managed()
            and not r.is_integration()
            and r.id not in skip
        ]
        await ctx.reply(
            embed=messages.profile_embed(
                member,
                join_rank((member.joined_at, member.id), joins),
                len(joins),
                answers(found, roles),
                others,
            )
        )

    bot.add_command(perfil)

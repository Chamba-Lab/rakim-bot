import logging
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..members import Option, Question, Rows, own_roles, role_counts, tally

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    # Cuántos miembros eligieron cada opción del Onboarding. Las preguntas se leen de
    # Discord en cada uso: no hay IDs que configurar y los cambios se reflejan solos. Es
    # aparte de `invitaciones`, que usa el acumulado de Discord (incluye a quienes salieron).
    @commands.hybrid_command(  # type: ignore[arg-type]
        name="miembros",
        aliases=["members"],
        description="Cuántos miembros eligieron cada opción del Onboarding",
    )
    @app_commands.describe(alcance="«todos» agrega cuántos miembros tiene cada rol")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @commands.has_permissions(manage_guild=True)  # también para la forma con mención
    async def miembros(
        ctx: commands.Context[RakimBot], alcance: Literal["todos", "all"] | None = None
    ) -> None:
        if ctx.guild is None or ctx.guild.id != bot.settings.guild_id:
            return
        if not bot.in_staff_channel(ctx.channel.id):
            if ctx.interaction:
                await ctx.reply(
                    "Este comando solo funciona en el canal de logs o en el de bump.",
                    ephemeral=True,
                )
            return
        try:
            # Leer el Onboarding pide Gestionar servidor, el mismo permiso de las invitaciones.
            onboarding = await ctx.guild.onboarding()
        except discord.HTTPException:
            log.warning("No se pudo leer el Onboarding (¿falta Gestionar servidor?)")
            await ctx.reply(messages.onboarding_unreadable())
            return
        await ctx.reply(
            embed=members_embed(
                ctx.guild, onboarding, include_roles=alcance is not None
            )
        )

    bot.add_command(miembros)


def members_embed(
    guild: discord.Guild, onboarding: discord.Onboarding, include_roles: bool
) -> discord.Embed:
    # Con el intent `members`, la lista completa ya está en memoria: no hay más llamadas.
    # Quien no aceptó las reglas (`pending`) aún no terminó el Onboarding.
    counted = [
        {r.id for r in m.roles} for m in guild.members if not m.bot and not m.pending
    ]
    sections: list[tuple[str, Rows]] = []
    for question in questions(onboarding):
        rows, none = tally(question, counted)
        rows.append(("Ninguna" if question.multiple else "Sin responder", none))
        title = question.title
        if question.multiple:
            title += " (se puede elegir más de una)"
        sections.append((title, rows))
    if include_roles:
        # Sin @everyone ni los roles de bots, que gestiona Discord.
        roles = [
            (r.id, r.name)
            for r in reversed(guild.roles)
            if not r.is_default() and not r.managed
        ]
        sections.append(("Todos los roles", role_counts(roles, counted)))
    return messages.members_embed(sections, len(counted))


def questions(onboarding: discord.Onboarding) -> list[Question]:
    """Las preguntas del Onboarding que dan roles, con sus opciones que dan roles."""
    result = []
    for prompt in onboarding.prompts:
        with_roles = [o for o in prompt.options if o.roles]
        if not with_roles:
            continue
        question = Question(
            prompt.title,
            [Option(o.title, frozenset(r.id for r in o.roles)) for o in with_roles],
            not prompt.single_select,
        )
        # El nombre de cada fila sale del rol propio de la opción (sin Member, que dan todas).
        labeled = [
            Option(_label(o, own), opt.role_ids)
            for o, opt, own in zip(
                with_roles, question.options, own_roles(question), strict=True
            )
        ]
        result.append(Question(question.title, labeled, question.multiple))
    return result


def _label(option: discord.OnboardingPromptOption, own: frozenset[int]) -> str:
    """El nombre del rol propio de la opción («Early Career»), que es corto; si no tiene
    uno solo, el texto de la opción. Con el emoji de la opción si es uno estándar."""
    names = [r.name for r in option.roles if r.id in own]
    name = names[0] if len(names) == 1 else option.title
    emoji = option.emoji
    if (
        isinstance(emoji, discord.PartialEmoji)
        and emoji.is_unicode_emoji()
        and emoji.name not in name
    ):
        name = f"{emoji.name} {name}"
    return name

"""Todo lo que Rakim escribe en Discord, para ajustar el tono sin tocar la lógica.

Voz de Rakim: directa, cálida y expresiva (un ¡! cuando toca); a veces gruñona, no siempre.
Español neutro, tuteo y un solo emoji como máximo.
"""

from datetime import datetime

import discord

from .config import Settings
from .invites import InviteInfo

GREEN = 0x57F287
RED = 0xED4245


def welcome(user_id: int, s: Settings) -> str:
    """Borrador del mensaje de bienvenida (el texto final lo define el equipo)."""
    return (
        f"¡Qué bueno tenerte en Chamba Lab, <@{user_id}>! Soy Rakim, la mascota de esta "
        "comunidad tech chill para conectar, inspirarte y crecer.\n"
        "\n"
        f"- Preséntate en <#{s.intro_channel_id}>: quién eres, qué haces y qué te gusta.\n"
        "- ¿Quieres feedback de tu portafolio, GitHub, LinkedIn o CV? Pídelo en "
        f"<#{s.ask_feedback_channel_id}>.\n"
        f"- Nuestras redes y el blog están en <#{s.links_channel_id}>.\n"
        "\n"
        "Ponte a gusto. ☕"
    )


def bump_reminder(role_id: int | None, user_id: int | None, minutes: int) -> str:
    mention = f"<@&{role_id}> " if role_id else ""
    mention += f"<@{user_id}> " if user_id else ""
    return f"{mention}Pasaron {minutes} minutos. Toca hacer `/bump`."


def describe_invites(candidates: list[InviteInfo], labels: dict[str, str]) -> str:
    """Texto del log para la invitación usada (o por qué no se pudo determinar)."""
    if not candidates:
        return (
            "No se pudo determinar (invitación vanity, enlace de otro tipo "
            "o permisos insuficientes)"
        )
    if len(candidates) > 1:
        names = ", ".join(labels.get(i.code, f"`{i.code}`") for i in candidates)
        return f"No se pudo determinar. Posibles: {names}"

    invite = candidates[0]
    name = labels.get(invite.code)
    text = f"{name} (`{invite.code}`)" if name else f"`{invite.code}`"
    if invite.inviter_id:
        text += f" · creada por <@{invite.inviter_id}>"
    return text + f" · {invite.uses} {'uso' if invite.uses == 1 else 'usos'}"


def _when(dt: datetime) -> str:
    """Marca de tiempo de Discord: cada persona la ve en su hora local."""
    return discord.utils.format_dt(dt, "R")


def join_embed(member: discord.Member, invite_text: str) -> discord.Embed:
    embed = discord.Embed(
        title="Entró un bot" if member.bot else "Entró un miembro", color=GREEN
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Miembro", value=f"{member.mention} ({member})", inline=False)
    embed.add_field(name="ID", value=str(member.id))
    embed.add_field(name="Cuenta creada", value=_when(member.created_at))
    embed.add_field(name="Invitación", value=invite_text, inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


def leave_embed(member: discord.Member) -> discord.Embed:
    roles = [r.name for r in member.roles if not r.is_default()]
    embed = discord.Embed(
        title="Salió un bot" if member.bot else "Salió un miembro", color=RED
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Miembro", value=f"{member.mention} ({member})", inline=False)
    embed.add_field(name="ID", value=str(member.id))
    embed.add_field(
        name="Se unió",
        value=_when(member.joined_at) if member.joined_at else "Desconocido",
    )
    embed.add_field(name="Roles", value=", ".join(roles) or "Ninguno", inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed

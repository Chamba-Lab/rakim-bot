"""Comprobaciones de que Rakim tiene lo que necesita en el servidor. No hablan con Discord:
reciben el servidor ya cargado y las invitaciones ya leídas."""

from dataclasses import dataclass

import discord

from .config import Settings
from .invites import InviteInfo

PERMISSION_NAMES = {
    "view_channel": "ver el canal",
    "send_messages": "enviar mensajes",
    "embed_links": "insertar enlaces",
}


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str = ""


def check_setup(
    guild: discord.Guild, settings: Settings, invites: dict[str, InviteInfo] | None
) -> list[Check]:
    me = guild.me
    topics_on = bool(settings.topic_times)
    channels = [
        # (nombre, ID, permisos que necesita ahí)
        (
            "Canal de logs",
            settings.log_channel_id,
            ("view_channel", "send_messages", "embed_links"),
        ),
        (
            "Canal de bump",
            settings.bump_channel_id,
            ("view_channel", "send_messages", "embed_links"),
        ),
        (
            "Canal general",
            settings.welcome_channel_id,
            # El tema del día va en un embed.
            ("view_channel", "send_messages") + (("embed_links",) if topics_on else ()),
        ),
        ("Canal de presentaciones", settings.intro_channel_id, ("view_channel",)),
        ("Canal de preguntas", settings.ask_feedback_channel_id, ("view_channel",)),
        ("Canal de enlaces", settings.links_channel_id, ("view_channel",)),
    ]
    manage = me.guild_permissions.manage_guild
    checks = [
        Check(
            "Gestionar servidor",
            manage,
            "" if manage else "sin él no puedo leer las invitaciones",
        )
    ]
    for name, channel_id, needed in channels:
        channel = guild.get_channel(channel_id)
        if channel is None:
            checks.append(Check(name, False, "no existe o no lo veo"))
            continue
        perms = channel.permissions_for(me)
        missing = [PERMISSION_NAMES[p] for p in needed if not getattr(perms, p)]
        checks.append(
            Check(
                name, not missing, f"me falta {', '.join(missing)}" if missing else ""
            )
        )

    if invites is None:
        checks.append(Check("Invitaciones", False, "no pude leerlas"))
    else:
        unknown = [c for c in settings.invite_labels if c not in invites]
        detail = f"{len(invites)} leídas, {len(settings.invite_labels) - len(unknown)} registradas"
        if unknown:
            detail += f"; sin invitación para {', '.join(f'`{c}`' for c in unknown)}"
        checks.append(Check("Invitaciones", not unknown, detail))

    if topics_on and settings.daily_topic_role_id:
        checks.append(topic_role_check(guild, settings.daily_topic_role_id, settings))

    # Un ID mal copiado en los roles de `/miembros` dejaría ese rol fuera sin avisar.
    for name, role_ids in (
        ("Roles de país", settings.country_roles),
        ("Roles de etapa", settings.stage_roles),
        ("Roles de notificación", settings.notification_roles),
    ):
        if role_ids:
            missing = [str(r) for r in role_ids if guild.get_role(r) is None]
            detail = f"{len(role_ids) - len(missing)} de {len(role_ids)}"
            if missing:
                detail += f"; no existen: {', '.join(missing)}"
            checks.append(Check(name, not missing, detail))
    return checks


def topic_role_check(guild: discord.Guild, role_id: int, settings: Settings) -> Check:
    """Que el rol del tema del día exista y que Rakim pueda mencionarlo en el general.

    Discord no tiene un permiso para mencionar un rol concreto: hace falta que el rol sea
    mencionable por cualquiera o que Rakim tenga «Mencionar @everyone, @here y todos los
    roles» en ese canal. Sin esto, el tema sale igual, pero la mención no notifica.
    """
    name = "Rol del tema del día"
    role = guild.get_role(role_id)
    if role is None:
        return Check(name, False, "no existe")
    channel = guild.get_channel(settings.welcome_channel_id)
    can = role.mentionable or (
        channel is not None and channel.permissions_for(guild.me).mention_everyone
    )
    detail = (
        ""
        if can
        else "no puedo mencionarlo en el canal general: falta «Mencionar @everyone, @here y todos los roles» ahí"
    )
    return Check(name, can, detail)

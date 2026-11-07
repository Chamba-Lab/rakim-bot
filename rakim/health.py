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
            ("view_channel", "send_messages"),
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
    return checks

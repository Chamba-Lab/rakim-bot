import asyncio
import logging
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

from . import messages
from .bump import BumpReminder
from .config import Settings
from .invites import InviteInfo
from .state import State

log = logging.getLogger("rakim")

# Un módulo por evento de Discord, en rakim/events/.
EVENTS = [
    "ready",
    "member_join",
    "member_update",
    "member_remove",
    "message",
    "stats",
    "members",
    "status",
    "roulette",
    "daily_topic",
    "command_error",
]


# Rakim no usa voz: se apaga el aviso de discord.py por no tener PyNaCl.
discord.VoiceClient.warn_nacl = False


class RakimBot(commands.Bot):
    def __init__(self, settings: Settings):
        # Solo los intents que usa el bot (el porqué de cada uno: docs/architecture.md).
        intents = discord.Intents.none()
        intents.guilds = True  # servidor, canales y roles
        intents.members = True  # privilegiado: entradas, salidas y fin de las reglas
        intents.guild_messages = True  # mensajes de Disboard
        intents.message_content = True  # privilegiado: leer el texto de esos mensajes
        super().__init__(
            command_prefix=commands.when_mentioned,  # comandos con mención (y con `/`)
            help_command=None,  # el `help` por defecto respondería a cualquiera
            intents=intents,
            # Por defecto no menciona a nadie; cada envío permite solo lo que necesita.
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.settings = settings
        self.state = State(settings.state_path)
        self.bump = BumpReminder(
            self.state, settings.bump_cooldown_minutes * 60, self.remind_bump
        )
        # Usos de cada invitación en la última lectura, para deducir cuál se usó.
        self.invites: dict[str, InviteInfo] | None = None
        self.join_lock = asyncio.Lock()  # las entradas se procesan de una en una
        # Evita un saludo doble. Es un dict para conservar el orden y acotar su tamaño.
        self.welcomed: dict[int, None] = {}
        # Miembros cuyo mensaje nativo de entrada ya llegó (o se está esperando).
        self.system_messages: dict[int, asyncio.Event] = {}
        self.started = False
        self.started_at: datetime | None = None

    def in_staff_channel(self, channel_id: int) -> bool:
        """Los comandos del equipo solo responden en el canal de logs y en el de bump."""
        return channel_id in (
            self.settings.log_channel_id,
            self.settings.bump_channel_id,
        )

    async def setup_hook(self) -> None:
        for name in EVENTS:
            await self.load_extension(f"rakim.events.{name}")
        # Los comandos `/` se publican solo en este servidor (aparecen al instante).
        # Sin el permiso `applications.commands` falla, y el comando con mención sigue sirviendo.
        guild = discord.Object(self.settings.guild_id)
        self.tree.copy_global_to(guild=guild)
        try:
            await self.tree.sync(guild=guild)
        except discord.HTTPException:
            log.exception(
                "No se pudieron publicar los comandos / (¿falta applications.commands?)"
            )

    async def send(self, channel_id: int, **kwargs: Any) -> None:
        """Publica en un canal por su ID; falla con claridad si no se puede escribir ahí."""
        channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            raise RuntimeError(f"El canal {channel_id} no admite mensajes")
        await channel.send(**kwargs)

    async def remind_bump(self) -> None:
        s = self.settings
        # Solo se mencionan el rol y la persona del bump, si existen (el rol debe ser mencionable).
        mentions = discord.AllowedMentions(
            roles=[discord.Object(s.bump_role_id)] if s.bump_role_id else False,
            users=[discord.Object(s.bump_user_id)] if s.bump_user_id else False,
        )
        await self.send(
            s.bump_channel_id,
            content=messages.bump_reminder(
                s.bump_role_id, s.bump_user_id, s.bump_cooldown_minutes
            ),
            allowed_mentions=mentions,
        )

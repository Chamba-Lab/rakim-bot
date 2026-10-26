import asyncio
from typing import Any

import discord
from discord.ext import commands

from . import messages
from .bump import BumpReminder
from .config import Settings
from .invites import InviteInfo
from .state import State

# Un módulo por evento de Discord, en rakim/events/.
EVENTS = ["ready", "member_join", "member_update", "member_remove", "message"]


class RakimBot(commands.Bot):
    def __init__(self, settings: Settings):
        # Solo los intents que usa el bot (el porqué de cada uno: docs/architecture.md).
        intents = discord.Intents.none()
        intents.guilds = True  # servidor, canales y roles
        intents.members = True  # privilegiado: entradas, salidas y fin de las reglas
        intents.guild_messages = True  # mensajes de Disboard
        intents.message_content = True  # privilegiado: leer el texto de esos mensajes
        super().__init__(
            command_prefix=commands.when_mentioned,  # el bot no tiene comandos
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
        self.welcomed: set[int] = set()  # evita un saludo doble
        self.started = False

    async def setup_hook(self) -> None:
        for name in EVENTS:
            await self.load_extension(f"rakim.events.{name}")

    async def send(self, channel_id: int, **kwargs: Any) -> None:
        """Publica en un canal por su ID; falla con claridad si no se puede escribir ahí."""
        channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            raise RuntimeError(f"El canal {channel_id} no admite mensajes")
        await channel.send(**kwargs)

    async def remind_bump(self) -> None:
        s = self.settings
        # Solo se menciona el rol del bump, si existe (debe ser mencionable).
        mentions = (
            discord.AllowedMentions(roles=[discord.Object(s.bump_role_id)])
            if s.bump_role_id
            else discord.AllowedMentions.none()
        )
        await self.send(
            s.bump_channel_id,
            content=messages.bump_reminder(s.bump_role_id, s.bump_cooldown_minutes),
            allowed_mentions=mentions,
        )

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..welcome import send_welcome, sort_for_manual

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    # Para cuando Rakim estuvo apagado y alguien terminó las reglas sin saludo. El equipo
    # nombra a quién saludar (con el bot apagado tampoco hubo log de entrada que lo diga).
    # Los comandos híbridos no admiten un número variable de argumentos: van cinco huecos.
    @commands.hybrid_command(  # type: ignore[arg-type]
        name="saludar",
        aliases=["welcome"],
        description="Da la bienvenida en el canal general a quien se quedó sin saludo",
    )
    @app_commands.describe(
        persona="A quién saludar",
        persona2="Otra persona (opcional)",
        persona3="Otra persona (opcional)",
        persona4="Otra persona (opcional)",
        persona5="Otra persona (opcional)",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @commands.has_permissions(manage_guild=True)  # también para la forma con mención
    async def saludar(
        ctx: commands.Context[RakimBot],
        persona: discord.Member,
        persona2: discord.Member | None = None,
        persona3: discord.Member | None = None,
        persona4: discord.Member | None = None,
        persona5: discord.Member | None = None,
    ) -> None:
        if ctx.guild is None or ctx.guild.id != bot.settings.guild_id:
            return
        # Se lanza desde los canales del equipo; el saludo sale en el general.
        if not bot.in_staff_channel(ctx.channel.id):
            if ctx.interaction:
                await ctx.reply(
                    "Este comando solo funciona en el canal de logs o en el de bump.",
                    ephemeral=True,
                )
            return
        named = [persona, persona2, persona3, persona4, persona5]
        greet_now, pending, already = sort_for_manual(
            bot, [m for m in named if m is not None]
        )
        if greet_now:
            try:
                await send_welcome(bot, greet_now)
            except Exception:
                log.exception("No se pudo enviar el saludo a mano")
                await ctx.reply(messages.manual_welcome_failed(), ephemeral=True)
                return
        # La respuesta menciona sin notificar: el bot no permite menciones por defecto.
        await ctx.reply(
            messages.manual_welcome_result(
                [m.id for m in greet_now],
                [m.id for m in pending],
                [m.id for m in already],
                bot.settings.welcome_channel_id,
            ),
            ephemeral=True,
        )

    bot.add_command(saludar)

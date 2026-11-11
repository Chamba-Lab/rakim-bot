import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import messages
from ..bot import RakimBot
from ..daily_topic import next_topic, select_presets
from ..roulette import Preset, load_presets

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    s = bot.settings
    presets = select_presets(load_presets(), s.topic_preset_ids)
    # El automático y el manual comparten ciclo: el candado evita que, si coinciden,
    # los dos elijan el mismo tema antes de que el otro lo guarde.
    lock = asyncio.Lock()

    async def post() -> str:
        async with lock:
            return await post_topic(bot, presets)

    # A mano, para el equipo. No reemplaza ni mueve el automático: solo gasta un tema
    # del mismo ciclo, así que el de la hora programada trae otro.
    @commands.hybrid_command(
        name="tema",
        aliases=["topic"],
        description="Publica ahora un tema del día en el canal general",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @commands.has_permissions(manage_guild=True)  # también para la forma con mención
    async def tema(ctx: commands.Context[RakimBot]) -> None:
        if ctx.guild is None or ctx.guild.id != s.guild_id:
            return
        # Se lanza desde los canales del equipo; el tema sale en el general.
        if not bot.in_staff_channel(ctx.channel.id):
            if ctx.interaction:
                await ctx.reply(
                    "Este comando solo funciona en el canal de logs o en el de bump.",
                    ephemeral=True,
                )
            return
        try:
            topic = await post()
        except Exception:
            log.exception("No se pudo publicar el tema del día a mano")
            await ctx.reply(messages.daily_topic_failed(), ephemeral=True)
            return
        await ctx.reply(
            messages.daily_topic_posted(topic, s.welcome_channel_id), ephemeral=True
        )

    bot.add_command(tema)

    if not s.topic_times:
        log.info("Tema del día automático apagado (DAILY_TOPIC_TIMES está vacío)")
        return

    # Sale a las horas fijas, aunque el canal tenga conversación: no se vigila la
    # actividad. Si el bot está apagado a esa hora, ese tema no se envía después.
    @tasks.loop(time=s.topic_times)
    async def daily_topic() -> None:
        try:
            await post()
        except Exception:
            # Una excepción sin capturar detendría el loop hasta el próximo reinicio.
            log.exception("No se pudo publicar el tema del día")

    @daily_topic.before_loop
    async def wait_until_ready() -> None:
        await bot.wait_until_ready()

    daily_topic.start()


async def post_topic(bot: RakimBot, presets: list[Preset]) -> str:
    """Publica el siguiente tema del ciclo en el canal general y lo devuelve."""
    s = bot.settings
    preset, topic, used = next_topic(presets, bot.state.used_topics)
    # Solo se menciona el rol de Actividades, si existe.
    role = s.daily_topic_role_id
    mentions = discord.AllowedMentions(roles=[discord.Object(role)] if role else False)
    await bot.send(
        s.welcome_channel_id,
        content=messages.daily_topic(role),
        embed=messages.daily_topic_embed(preset.name, topic),
        allowed_mentions=mentions,
    )
    # Se marca como usado solo si salió: un envío fallido no gasta el tema.
    bot.state.used_topics = used
    bot.state.save()
    log.info("Tema del día publicado: %s", topic)
    return topic

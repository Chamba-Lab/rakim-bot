import logging

import discord
from discord.ext import tasks

from .. import messages
from ..bot import RakimBot
from ..daily_topic import next_topic, select_presets
from ..roulette import Preset, load_presets

log = logging.getLogger("rakim")


async def setup(bot: RakimBot) -> None:
    s = bot.settings
    if not s.topic_times:
        log.info("Tema del día apagado (DAILY_TOPIC_TIMES está vacío)")
        return
    presets = select_presets(load_presets(), s.topic_preset_ids)

    # Sale a las horas fijas, aunque el canal tenga conversación: no se vigila la
    # actividad. Si el bot está apagado a esa hora, ese tema no se envía después.
    @tasks.loop(time=s.topic_times)
    async def daily_topic() -> None:
        try:
            await post_topic(bot, presets)
        except Exception:
            # Una excepción sin capturar detendría el loop hasta el próximo reinicio.
            log.exception("No se pudo publicar el tema del día")

    @daily_topic.before_loop
    async def wait_until_ready() -> None:
        await bot.wait_until_ready()

    daily_topic.start()


async def post_topic(bot: RakimBot, presets: list[Preset]) -> None:
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

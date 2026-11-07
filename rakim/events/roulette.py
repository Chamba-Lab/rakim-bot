from discord import app_commands
from discord.ext import commands

from .. import messages
from ..bot import RakimBot
from ..roulette import find_preset, load_presets, pick


async def setup(bot: RakimBot) -> None:
    presets = load_presets()
    last: dict[int, str] = {}  # el último tema por canal, para no repetirlo seguido

    # Disponible en cualquier canal y para cualquier persona: es contenido público.
    # El enfriamiento por canal evita que el comando llene la conversación.
    @commands.hybrid_command(  # type: ignore[arg-type]
        name="ruleta",
        aliases=["roulette"],
        description="Lanza un tema de conversación al azar",
    )
    @app_commands.describe(tema="Un grupo de temas (si no, sale de todos)")
    @app_commands.choices(
        tema=[app_commands.Choice(name=p.name[:100], value=p.id) for p in presets]
    )
    @app_commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def ruleta(ctx: commands.Context[RakimBot], tema: str | None = None) -> None:
        if ctx.guild is None or ctx.guild.id != bot.settings.guild_id:
            return
        only = None
        if tema:
            only = find_preset(presets, tema)
            if only is None:  # con `/` no pasa: el menú solo ofrece grupos que existen
                await ctx.reply(messages.roulette_unknown(presets), ephemeral=True)
                return
        preset, topic = pick(presets, only, last.get(ctx.channel.id))
        last[ctx.channel.id] = topic
        await ctx.reply(embed=messages.roulette_embed(preset.name, topic))

    bot.add_command(ruleta)

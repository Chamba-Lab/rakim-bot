"""Todo lo que Rakim escribe en Discord, para ajustar el tono sin tocar la lógica.

Voz de Rakim: directa, cálida y expresiva (un ¡! cuando toca); a veces gruñona, no siempre.
Español neutro, tuteo y un solo emoji como máximo.
"""

from datetime import UTC, datetime

import discord

from .config import Settings
from .health import Check
from .invites import InviteInfo
from .roulette import Preset

GREEN = 0x57F287
RED = 0xED4245
YELLOW = 0xFACC15  # amarillo de la marca

# Tabla de entradas por invitación
MAX_ROWS = 15
NAME_WIDTH = 16
BAR_WIDTH = 10


def welcome(user_id: int, s: Settings) -> str:
    """Borrador del mensaje de bienvenida (el texto final lo define el equipo)."""
    return (
        f"¡Bienvenid@, <@{user_id}>! Soy Rakim, la mascota de esta comunidad: un espacio "
        "chill para conectar, inspirarte y crecer en el mundo tech.\n"
        "\n"
        f"- Cuéntanos de ti en <#{s.intro_channel_id}>: tu nombre, de dónde eres, en qué "
        "trabajas o qué estudias, y tus hobbies e intereses. Lo que quieras compartir.\n"
        "- ¿Quieres que la comunidad le eche un ojo a tu portafolio, GitHub, LinkedIn o "
        f"CV? Pide feedback en <#{s.ask_feedback_channel_id}>.\n"
        f"- Nuestras redes y el blog los encuentras en <#{s.links_channel_id}>.\n"
        "\n"
        "Sírvete un café y ponte a gusto. ☕"
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


def invite_totals(
    invites: dict[str, InviteInfo], labels: dict[str, str], include_all: bool = False
) -> list[tuple[str, int]]:
    """Entradas por fuente, de mayor a menor: suma los usos de las invitaciones con el mismo nombre.

    Por defecto solo cuenta las registradas en `INVITE_LABELS`; con `include_all`, todas
    (las sin nombre salen con su código).
    """
    totals: dict[str, int] = {}
    for code, label in labels.items():  # las nombradas salen aunque tengan 0 usos
        if code in invites:
            totals.setdefault(label, 0)
    for i in invites.values():
        if i.code not in labels and not include_all:
            continue
        key = labels.get(i.code, i.code)
        totals[key] = totals.get(key, 0) + i.uses
    return sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))


def invites_embed(
    invites: dict[str, InviteInfo], labels: dict[str, str], include_all: bool = False
) -> discord.Embed:
    """Tabla con barras de las entradas por invitación, en un embed con el amarillo de la marca."""
    rows = invite_totals(invites, labels, include_all)
    embed = discord.Embed(title="Entradas por invitación", color=YELLOW)
    if not rows:
        embed.description = (
            "No hay invitaciones registradas que contar. "
            "Usa `todas` para ver también las demás."
        )
        return embed

    total = sum(n for _, n in rows)
    top = rows[0][1]
    shown = rows[:MAX_ROWS]
    width = min(max(len(name) for name, _ in shown), NAME_WIDTH)
    lines = []
    for name, n in shown:
        filled = round(BAR_WIDTH * n / top) if top else 0
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        pct = f"{round(100 * n / total)}%" if total else "0%"
        lines.append(f"{name[:NAME_WIDTH]:<{width}}  {bar}  {n:>4}  {pct:>4}")
    if len(rows) > len(shown):
        lines.append(f"…y {len(rows) - len(shown)} más")
    embed.description = "```\n" + "\n".join(lines) + "\n```"
    embed.add_field(name="Total", value=str(total))
    embed.add_field(name="Mostrando", value="todas" if include_all else "registradas")
    embed.set_footer(text="Acumulado de Discord · incluye a quienes ya salieron")
    embed.timestamp = discord.utils.utcnow()
    return embed


def roulette_embed(preset_name: str, topic: str) -> discord.Embed:
    """El tema de la ruleta. El emoji del grupo (viene en su nombre) es el único del mensaje."""
    embed = discord.Embed(
        title="La ruleta dice…", description=f"**{topic}**", color=YELLOW
    )
    embed.set_footer(text=f"{preset_name} · otra vuelta con /ruleta")
    return embed


def daily_topic(role_id: int | None) -> str:
    mention = f"<@&{role_id}> " if role_id else ""
    return f"{mention}¡Tema del día! Responde aquí, aunque sea en una línea."


def daily_topic_embed(preset_name: str, topic: str) -> discord.Embed:
    """El tema del día, con el formato de la ruleta. El emoji del grupo es el único del mensaje."""
    embed = discord.Embed(
        title="Tema del día", description=f"**{topic}**", color=YELLOW
    )
    embed.set_footer(text=f"{preset_name} · mañana hay otro")
    return embed


def roulette_unknown(presets: list[Preset]) -> str:
    names = ", ".join(f"`{p.id}`" for p in presets)
    return f"No conozco ese grupo. Prueba con: {names}."


def status_embed(
    checks: list[Check],
    latency: float,
    started_at: datetime | None,
    bump_due_at: float | None,
) -> discord.Embed:
    """Estado de Rakim: una línea por comprobación, y los datos del proceso."""
    ok = all(c.ok for c in checks)
    embed = discord.Embed(
        title="Estado de Rakim" if ok else "Rakim tiene pendientes",
        color=GREEN if ok else RED,
    )
    embed.description = "\n".join(
        f"{'✔' if c.ok else '✘'} **{c.name}**" + (f": {c.detail}" if c.detail else "")
        for c in checks
    )
    embed.add_field(name="Latencia", value=f"{latency * 1000:.0f} ms")
    if started_at:
        embed.add_field(name="Activo desde", value=_when(started_at))
    due = (
        _when(datetime.fromtimestamp(bump_due_at, tz=UTC))
        if bump_due_at
        else "sin aviso pendiente"
    )
    embed.add_field(name="Próximo bump", value=due)
    embed.timestamp = discord.utils.utcnow()
    return embed


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

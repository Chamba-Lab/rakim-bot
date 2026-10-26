import logging
from dataclasses import dataclass, replace

import discord

log = logging.getLogger("rakim")


@dataclass(frozen=True)
class InviteInfo:
    code: str
    uses: int
    max_uses: int  # 0 = sin límite
    inviter_id: int | None


def used_invites(
    before: dict[str, InviteInfo], after: dict[str, InviteInfo]
) -> list[InviteInfo]:
    """Invitaciones que pudo usar quien acaba de entrar. Discord no lo informa: se deduce.

    Una sola candidata es la usada; varias o ninguna, no se puede determinar.
    """
    # Una invitación nueva (ausente en `before`) con usos se creó y se usó entre las dos lecturas.
    increased = [
        i
        for i in after.values()
        if i.uses > (before[i.code].uses if i.code in before else 0)
    ]
    if increased:
        return increased
    # Discord borra una invitación al agotarse: si desapareció y estaba a un uso de su límite, fue esa.
    return [
        replace(i, uses=i.uses + 1)
        for i in before.values()
        if i.code not in after and i.max_uses > 0 and i.uses + 1 >= i.max_uses
    ]


async def read_invites(guild: discord.Guild) -> dict[str, InviteInfo] | None:
    """Lee las invitaciones del servidor (pide el permiso Gestionar servidor)."""
    try:
        invites = await guild.invites()
    except discord.HTTPException:
        log.warning("No se pudieron leer las invitaciones (¿falta Gestionar servidor?)")
        return None
    return {
        i.code: InviteInfo(
            i.code, i.uses or 0, i.max_uses or 0, i.inviter.id if i.inviter else None
        )
        for i in invites
    }

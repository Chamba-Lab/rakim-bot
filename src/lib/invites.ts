export interface InviteSnapshot {
    code: string;
    uses: number;
    /** 0 = sin límite de usos. */
    maxUses: number;
    inviterId: string | null;
    inviterTag: string | null;
}

export type InviteCache = Map<string, InviteSnapshot>;

export type InviteMatch =
    | { kind: "known"; invite: InviteSnapshot }
    | { kind: "ambiguous"; candidates: InviteSnapshot[] }
    | { kind: "unknown" };

/**
 * Deduce qué invitación usó quien acaba de entrar, comparando los usos antes
 * y después. Discord no lo informa: se calcula.
 *
 * Una invitación que desapareció y estaba a un uso de su límite también cuenta,
 * porque Discord la borra al agotarse. Sin pistas (invitación vanity, flujos
 * de OAuth, o dos entradas casi simultáneas) el resultado es `unknown` o
 * `ambiguous`.
 */
export function matchUsedInvite(
    before: InviteCache,
    after: InviteCache,
): InviteMatch {
    // Una invitación nueva (ausente en `before`) con usos también cuenta: se creó y se usó entre las dos lecturas.
    const increased = [...after.values()].filter(
        (invite) => invite.uses > (before.get(invite.code)?.uses ?? 0),
    );
    if (increased.length === 1) return { kind: "known", invite: increased[0]! };
    if (increased.length > 1) {
        return { kind: "ambiguous", candidates: increased };
    }

    const exhausted = [...before.values()]
        .filter(
            (invite) =>
                !after.has(invite.code) &&
                invite.maxUses > 0 &&
                invite.uses + 1 >= invite.maxUses,
        )
        .map((invite) => ({ ...invite, uses: invite.uses + 1 }));
    if (exhausted.length === 1) return { kind: "known", invite: exhausted[0]! };
    if (exhausted.length > 1) {
        return { kind: "ambiguous", candidates: exhausted };
    }

    return { kind: "unknown" };
}

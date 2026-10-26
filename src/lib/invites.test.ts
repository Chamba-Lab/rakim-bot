import { describe, expect, it } from "vitest";

import {
    matchUsedInvite,
    type InviteCache,
    type InviteSnapshot,
} from "./invites.js";

function invite(
    code: string,
    uses: number,
    overrides: Partial<InviteSnapshot> = {},
): InviteSnapshot {
    return {
        code,
        uses,
        maxUses: 0,
        inviterId: "100000000000000001",
        inviterTag: "fundador",
        ...overrides,
    };
}

function cache(...invites: InviteSnapshot[]): InviteCache {
    return new Map(invites.map((item) => [item.code, item]));
}

describe("matchUsedInvite", () => {
    it("detecta la invitación cuyo contador subió", () => {
        const before = cache(invite("oficial", 10), invite("disboard", 4));
        const after = cache(invite("oficial", 11), invite("disboard", 4));
        expect(matchUsedInvite(before, after)).toEqual({
            kind: "known",
            invite: invite("oficial", 11),
        });
    });

    it("cuenta una invitación creada y usada entre dos lecturas", () => {
        const before = cache(invite("oficial", 10));
        const after = cache(invite("oficial", 10), invite("nueva", 1));
        expect(matchUsedInvite(before, after)).toMatchObject({
            kind: "known",
            invite: { code: "nueva" },
        });
    });

    it("detecta una invitación que se agotó y desapareció", () => {
        const before = cache(
            invite("oficial", 10),
            invite("un-uso", 0, { maxUses: 1 }),
        );
        const after = cache(invite("oficial", 10));
        expect(matchUsedInvite(before, after)).toMatchObject({
            kind: "known",
            invite: { code: "un-uso", uses: 1 },
        });
    });

    it("no atribuye una invitación que desapareció sin estar agotada", () => {
        const before = cache(invite("oficial", 10), invite("borrada", 2));
        const after = cache(invite("oficial", 10));
        expect(matchUsedInvite(before, after)).toEqual({ kind: "unknown" });
    });

    it("marca como ambiguo cuando subieron varias", () => {
        const before = cache(invite("a", 1), invite("b", 1));
        const after = cache(invite("a", 2), invite("b", 2));
        expect(matchUsedInvite(before, after).kind).toBe("ambiguous");
    });

    it("devuelve desconocido si nada cambió", () => {
        const same = cache(invite("oficial", 10));
        expect(matchUsedInvite(same, same)).toEqual({ kind: "unknown" });
    });
});

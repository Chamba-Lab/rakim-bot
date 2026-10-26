import { describe, expect, it } from "vitest";

import type { InviteSnapshot } from "./lib/invites.js";
import {
    bumpReminderMessage,
    describeInvite,
    describeMatch,
    welcomeMessage,
} from "./messages.js";

const channels = {
    intro: "111111111111111111",
    askFeedback: "222222222222222222",
    serverFeedback: "333333333333333333",
    links: "444444444444444444",
};

function invite(overrides: Partial<InviteSnapshot> = {}): InviteSnapshot {
    return {
        code: "abc",
        uses: 3,
        maxUses: 0,
        inviterId: "100000000000000001",
        inviterTag: "fundador",
        ...overrides,
    };
}

describe("welcomeMessage", () => {
    const message = welcomeMessage("999999999999999999", channels);

    it("menciona a la persona y a cada canal", () => {
        expect(message).toContain("<@999999999999999999>");
        expect(message).toContain("<#111111111111111111>");
        expect(message).toContain("<#222222222222222222>");
        expect(message).toContain("<#333333333333333333>");
        expect(message).toContain("<#444444444444444444>");
    });

    it("cabe en un mensaje de Discord", () => {
        expect(message.length).toBeLessThanOrEqual(2000);
    });

    it("usa un solo emoji, como pide la guía de tono", () => {
        const emojis = message.match(/\p{Extended_Pictographic}/gu) ?? [];
        expect(emojis).toHaveLength(1);
    });
});

describe("bumpReminderMessage", () => {
    it("menciona el rol cuando está configurado", () => {
        expect(bumpReminderMessage("123", 120)).toBe(
            "<@&123> Pasaron 120 minutos. Toca hacer `/bump`.",
        );
    });

    it("funciona sin rol", () => {
        expect(bumpReminderMessage(undefined, 120)).toBe(
            "Pasaron 120 minutos. Toca hacer `/bump`.",
        );
    });
});

describe("describeInvite", () => {
    it("usa el nombre configurado, el creador y los usos", () => {
        expect(describeInvite(invite(), { abc: "Web y redes" })).toBe(
            "Web y redes (`abc`) · creada por <@100000000000000001> · 3 usos",
        );
    });

    it("muestra solo el código si no hay nombre y usa el singular", () => {
        expect(describeInvite(invite({ uses: 1, inviterId: null }), {})).toBe(
            "`abc` · 1 uso",
        );
    });
});

describe("describeMatch", () => {
    it("explica cuando no se pudo determinar", () => {
        expect(describeMatch({ kind: "unknown" }, {})).toContain(
            "No se pudo determinar",
        );
    });

    it("lista las candidatas cuando es ambiguo", () => {
        const text = describeMatch(
            {
                kind: "ambiguous",
                candidates: [invite({ code: "a" }), invite({ code: "b" })],
            },
            { a: "Disboard" },
        );
        expect(text).toBe("No se pudo determinar. Posibles: Disboard, `b`");
    });
});

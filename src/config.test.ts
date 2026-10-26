import { describe, expect, it } from "vitest";

import { loadConfig } from "./config.js";

const valid = {
    DISCORD_TOKEN: "token",
    GUILD_ID: "100000000000000001",
    WELCOME_CHANNEL_ID: "100000000000000002",
    INTRO_CHANNEL_ID: "100000000000000003",
    ASK_FEEDBACK_CHANNEL_ID: "100000000000000004",
    SERVER_FEEDBACK_CHANNEL_ID: "100000000000000005",
    LINKS_CHANNEL_ID: "100000000000000006",
    LOG_CHANNEL_ID: "100000000000000007",
    BUMP_CHANNEL_ID: "100000000000000008",
};

describe("loadConfig", () => {
    it("aplica los valores por defecto", () => {
        const config = loadConfig(valid);
        expect(config.bump.disboardBotId).toBe("302050872383242240");
        expect(config.bump.cooldownMs).toBe(120 * 60_000);
        expect(config.bump.roleId).toBeUndefined();
        expect(config.inviteLabels).toEqual({});
        expect(config.statePath).toBe("data/state.json");
    });

    it("trata una variable vacía como no definida", () => {
        const config = loadConfig({
            ...valid,
            BUMP_ROLE_ID: "",
            INVITE_LABELS: "",
        });
        expect(config.bump.roleId).toBeUndefined();
        expect(config.inviteLabels).toEqual({});
    });

    it("lee los nombres de invitación y el patrón de bump", () => {
        const config = loadConfig({
            ...valid,
            INVITE_LABELS: '{"abc":"Web y redes"}',
            BUMP_SUCCESS_PATTERN: "bump (done|realizado)",
        });
        expect(config.inviteLabels).toEqual({ abc: "Web y redes" });
        expect(config.bump.successPattern.test("Bump REALIZADO")).toBe(true);
    });

    it("informa todos los errores a la vez", () => {
        expect(() =>
            loadConfig({ ...valid, GUILD_ID: "x", LOG_CHANNEL_ID: undefined }),
        ).toThrow(/GUILD_ID[\s\S]*LOG_CHANNEL_ID/);
    });

    it("rechaza un JSON de invitaciones inválido", () => {
        expect(() =>
            loadConfig({ ...valid, INVITE_LABELS: "no es json" }),
        ).toThrow(/INVITE_LABELS/);
    });
});

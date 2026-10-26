import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BumpReminder, isBumpSuccess } from "./bump.js";
import { StateStore } from "./state.js";

const detection = {
    disboardBotId: "302050872383242240",
    successPattern: /bump done/i,
};

describe("isBumpSuccess", () => {
    it("reconoce la confirmación de Disboard", () => {
        expect(
            isBumpSuccess(
                {
                    authorId: "302050872383242240",
                    texts: ["Bump done! Check it out on DISBOARD."],
                },
                detection,
            ),
        ).toBe(true);
    });

    it("ignora el mismo texto escrito por otra persona", () => {
        expect(
            isBumpSuccess({ authorId: "1", texts: ["Bump done!"] }, detection),
        ).toBe(false);
    });

    it("ignora la respuesta de enfriamiento de Disboard", () => {
        expect(
            isBumpSuccess(
                {
                    authorId: "302050872383242240",
                    texts: [
                        "Please wait another 42 minutes until the server can be bumped",
                    ],
                },
                detection,
            ),
        ).toBe(false);
    });

    it("no falla con mensajes sin texto", () => {
        expect(
            isBumpSuccess(
                { authorId: "302050872383242240", texts: [] },
                detection,
            ),
        ).toBe(false);
    });
});

const COOLDOWN = 120 * 60_000;

let dir: string;
let stores: StateStore[] = [];

beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-26T20:00:00Z"));
    dir = mkdtempSync(join(tmpdir(), "rakim-"));
});

afterEach(async () => {
    vi.useRealTimers();
    await Promise.all(stores.map((store) => store.flush()));
    stores = [];
    rmSync(dir, { recursive: true, force: true });
});

function setup(statePath = join(dir, "state.json")) {
    const store = new StateStore(statePath);
    stores.push(store);
    const send = vi.fn(async () => {});
    const reminder = new BumpReminder({ store, cooldownMs: COOLDOWN, send });
    return { store, send, reminder, statePath };
}

describe("BumpReminder", () => {
    it("avisa al terminar el enfriamiento y no antes", async () => {
        const { send, reminder } = setup();
        await reminder.schedule();

        await vi.advanceTimersByTimeAsync(COOLDOWN - 1);
        expect(send).not.toHaveBeenCalled();

        await vi.advanceTimersByTimeAsync(1);
        expect(send).toHaveBeenCalledTimes(1);
    });

    it("un bump nuevo reemplaza al aviso anterior", async () => {
        const { send, reminder } = setup();
        await reminder.schedule();
        await vi.advanceTimersByTimeAsync(COOLDOWN / 2);
        await reminder.schedule();

        await vi.advanceTimersByTimeAsync(COOLDOWN / 2 + 1);
        expect(send).not.toHaveBeenCalled();

        await vi.advanceTimersByTimeAsync(COOLDOWN / 2);
        expect(send).toHaveBeenCalledTimes(1);
    });

    it("retoma el aviso pendiente tras un reinicio", async () => {
        const first = setup();
        await first.reminder.schedule();

        first.reminder.stop(); // el proceso anterior ya no existe
        const restarted = setup(first.statePath);
        restarted.reminder.start();
        await vi.advanceTimersByTimeAsync(COOLDOWN);
        expect(restarted.send).toHaveBeenCalledTimes(1);
    });

    it("avisa de inmediato si el aviso venció con el bot apagado", async () => {
        const first = setup();
        await first.reminder.schedule();

        vi.setSystemTime(Date.now() + COOLDOWN * 2);
        first.reminder.stop();
        const restarted = setup(first.statePath);
        restarted.reminder.start();
        await vi.advanceTimersByTimeAsync(0);
        expect(restarted.send).toHaveBeenCalledTimes(1);
    });

    it("no repite el aviso después de enviarlo", async () => {
        const first = setup();
        await first.reminder.schedule();
        await vi.advanceTimersByTimeAsync(COOLDOWN);
        await first.store.flush();

        first.reminder.stop();
        const restarted = setup(first.statePath);
        restarted.reminder.start();
        await vi.advanceTimersByTimeAsync(COOLDOWN);
        expect(restarted.send).not.toHaveBeenCalled();
    });

    it("limpia el aviso aunque falle el envío", async () => {
        const { store, send, reminder } = setup();
        send.mockRejectedValueOnce(new Error("sin permisos"));
        await reminder.schedule();
        await vi.advanceTimersByTimeAsync(COOLDOWN);

        expect(store.get().bump.dueAt).toBeNull();
    });
});

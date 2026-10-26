import type { Client, ClientEvents } from "discord.js";

import type { Context } from "../context.js";
import { log } from "../lib/logger.js";
import clientReady from "./clientReady.js";
import guildMemberAdd from "./guildMemberAdd.js";
import guildMemberRemove from "./guildMemberRemove.js";
import guildMemberUpdate from "./guildMemberUpdate.js";
import messageCreate from "./messageCreate.js";

/**
 * Forma común de todos los eventos. Cada archivo tipa sus argumentos con
 * `defineEvent`; aquí, al conectarlos, ya solo se reenvían tal cual llegan.
 */
interface AnyBotEvent {
    name: keyof ClientEvents;
    once?: boolean;
    execute(ctx: Context, ...args: unknown[]): Promise<void> | void;
}

/** Todos los eventos que escucha el bot. Para sumar uno, agrégalo aquí. */
const events = [
    clientReady,
    guildMemberAdd,
    guildMemberRemove,
    guildMemberUpdate,
    messageCreate,
] as unknown as AnyBotEvent[];

/** Conecta cada evento al cliente. Un error dentro de un evento se registra y nunca tumba el proceso. */
export function registerEvents(client: Client, ctx: Context): void {
    for (const event of events) {
        const run = async (...args: unknown[]) => {
            try {
                await event.execute(ctx, ...args);
            } catch (error) {
                log.error(`Falló el evento ${event.name}`, error);
            }
        };
        if (event.once) client.once(event.name, run);
        else client.on(event.name, run);
    }
}

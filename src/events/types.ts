import type { ClientEvents } from "discord.js";

import type { Context } from "../context.js";

/**
 * Un evento de Discord: su nombre, si se escucha una sola vez y qué hace.
 * Hay un archivo por evento en esta carpeta; para sumar uno, se crea el archivo
 * con `defineEvent` y se agrega a la lista de `index.ts`.
 */
export interface BotEvent<K extends keyof ClientEvents = keyof ClientEvents> {
    name: K;
    once?: boolean;
    execute(ctx: Context, ...args: ClientEvents[K]): Promise<void> | void;
}

/** Solo ayuda a TypeScript a inferir los argumentos de cada evento. */
export function defineEvent<K extends keyof ClientEvents>(
    event: BotEvent<K>,
): BotEvent<K> {
    return event;
}

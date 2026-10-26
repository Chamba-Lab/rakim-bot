import { Events } from "discord.js";

import { defineEvent } from "./types.js";

/**
 * Un miembro cambió. Solo interesa un cambio: dejó de estar `pending`, es decir,
 * acaba de aceptar las reglas del Onboarding y ya puede escribir. Ese es el
 * momento del saludo.
 */
export default defineEvent({
    name: Events.GuildMemberUpdate,
    async execute(ctx, before, after) {
        if (after.guild.id !== ctx.config.guildId) return;

        // `=== true` y no `!== false`: si el miembro anterior no estaba en caché,
        // `pending` llega nulo y se saludaría a cualquiera que cambie de rol.
        if (before.pending === true && after.pending === false) {
            await ctx.welcome.greet(after);
        }
    },
});

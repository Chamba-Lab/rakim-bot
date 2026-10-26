import { Events } from "discord.js";

import { defineEvent } from "./types.js";

/** Llegó un mensaje: solo importa si es la confirmación de bump de Disboard. */
export default defineEvent({
    name: Events.MessageCreate,
    async execute(ctx, message) {
        if (message.guildId !== ctx.config.guildId) return;
        await ctx.bump.handleMessage(message);
    },
});

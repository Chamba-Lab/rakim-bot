import { Events } from "discord.js";

import { log } from "../lib/logger.js";
import { defineEvent } from "./types.js";

/** El bot terminó de conectarse: deja listo lo que necesita al arrancar. */
export default defineEvent({
    name: Events.ClientReady,
    once: true,
    async execute(ctx, client) {
        log.info(`Rakim conectado como ${client.user.tag}`);

        // Primera lectura de invitaciones, para poder compararlas en la primera entrada.
        const guild = client.guilds.cache.get(ctx.config.guildId);
        if (guild) await ctx.memberLog.init(guild);
        else log.warn("El bot no está en el servidor configurado (GUILD_ID)");

        // Retoma un aviso de bump pendiente; aquí porque, si venció, se envía de inmediato.
        ctx.bump.start();
    },
});

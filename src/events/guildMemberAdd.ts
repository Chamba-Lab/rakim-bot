import { Events } from "discord.js";

import { log } from "../lib/logger.js";
import { defineEvent } from "./types.js";

/**
 * Alguien entró al servidor: se registra en el log y, si ya puede escribir,
 * se le saluda. Si aún debe aceptar las reglas (`pending`), el saludo espera a
 * `guildMemberUpdate`.
 */
export default defineEvent({
    name: Events.GuildMemberAdd,
    async execute(ctx, member) {
        if (member.guild.id !== ctx.config.guildId) return;

        const tasks = [ctx.memberLog.logJoin(member)];
        if (!member.pending) tasks.push(ctx.welcome.greet(member));

        // Las dos tareas son independientes: si falla el log, el saludo sale igual.
        const results = await Promise.allSettled(tasks);
        for (const result of results) {
            if (result.status === "rejected") {
                log.error(
                    `Falló algo al recibir a ${member.id}`,
                    result.reason,
                );
            }
        }
    },
});

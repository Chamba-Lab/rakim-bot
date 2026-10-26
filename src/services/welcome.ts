import type { Client, GuildMember } from "discord.js";

import type { Config } from "../config.js";
import { sendToChannel } from "../lib/channels.js";
import { welcomeMessage } from "../messages.js";

/** Saluda a los miembros nuevos en el canal general. */
export function createWelcome(client: Client, config: Config) {
    // Evita un saludo doble si Discord repite el evento.
    const welcomed = new Set<string>();

    return {
        async greet(member: GuildMember): Promise<void> {
            if (member.user.bot || welcomed.has(member.id)) return;
            welcomed.add(member.id);

            try {
                await sendToChannel(client, config.channels.welcome, {
                    content: welcomeMessage(member.id, config.channels),
                    // Solo se menciona a la persona saludada, nunca @everyone ni roles.
                    allowedMentions: { users: [member.id] },
                });
            } catch (error) {
                welcomed.delete(member.id); // permite reintentar si el envío falló
                throw error;
            }
        },
    };
}

export type Welcome = ReturnType<typeof createWelcome>;

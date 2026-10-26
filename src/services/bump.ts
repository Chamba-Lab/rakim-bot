import type { Client, Message } from "discord.js";

import type { Config } from "../config.js";
import { BumpReminder, isBumpSuccess } from "../lib/bump.js";
import { sendToChannel } from "../lib/channels.js";
import { log } from "../lib/logger.js";
import type { StateStore } from "../lib/state.js";
import { bumpReminderMessage } from "../messages.js";

/**
 * Detecta el bump exitoso de Disboard y avisa cuando termina el enfriamiento.
 * Rakim no ejecuta el comando: un bot no puede invocar los comandos de otro.
 */
export function createBump(client: Client, config: Config, store: StateStore) {
    const cooldownMinutes = Math.round(config.bump.cooldownMs / 60_000);
    const { roleId } = config.bump;

    const reminder = new BumpReminder({
        store,
        cooldownMs: config.bump.cooldownMs,
        send: () =>
            sendToChannel(client, config.channels.bump, {
                content: bumpReminderMessage(roleId, cooldownMinutes),
                // Solo se menciona el rol del bump, si existe (debe ser mencionable).
                allowedMentions: { roles: roleId ? [roleId] : [] },
            }),
    });

    return {
        /** Retoma un aviso pendiente. Se llama con el cliente listo, porque puede venir vencido. */
        start: () => reminder.start(),

        /** Revisa un mensaje del servidor: si es la confirmación de Disboard, programa el aviso. */
        async handleMessage(message: Message): Promise<void> {
            // Embeds y texto de otros bots solo llegan con el intent MessageContent.
            const texts = [
                message.content,
                ...message.embeds.flatMap((embed) => [
                    embed.title,
                    embed.description,
                ]),
            ].filter((text): text is string => Boolean(text));

            const bumped = isBumpSuccess(
                { authorId: message.author.id, texts },
                config.bump,
            );
            if (!bumped) return;

            log.info("Bump detectado; aviso programado");
            await reminder.schedule();
        },
    };
}

export type Bump = ReturnType<typeof createBump>;

import type {
    Client,
    Guild,
    GuildMember,
    Invite,
    PartialGuildMember,
} from "discord.js";

import type { Config } from "../config.js";
import { sendToChannel } from "../lib/channels.js";
import { joinEmbed, leaveEmbed } from "../lib/embeds.js";
import {
    matchUsedInvite,
    type InviteCache,
    type InviteMatch,
    type InviteSnapshot,
} from "../lib/invites.js";
import { log } from "../lib/logger.js";
import { describeMatch } from "../messages.js";

function snapshotOf(invite: Invite): InviteSnapshot {
    return {
        code: invite.code,
        uses: invite.uses ?? 0,
        maxUses: invite.maxUses ?? 0,
        inviterId: invite.inviterId,
        inviterTag: invite.inviter?.tag ?? null,
    };
}

/** Registra entradas y salidas en el canal privado de logs. Solo informativo. */
export function createMemberLog(client: Client, config: Config) {
    // Usos de cada invitación en la última lectura. Sin lectura inicial no se puede comparar:
    // hasta entonces la invitación queda "desconocida".
    let cache: InviteCache | null = null;
    // Las entradas se procesan de una en una para que cada comparación parta de la anterior.
    let queue: Promise<unknown> = Promise.resolve();

    async function readInvites(guild: Guild): Promise<InviteCache | null> {
        try {
            const invites = await guild.invites.fetch();
            return new Map(
                invites.map((invite) => [invite.code, snapshotOf(invite)]),
            );
        } catch (error) {
            log.warn(
                "No se pudieron leer las invitaciones (¿falta el permiso Gestionar servidor?)",
                error,
            );
            return null;
        }
    }

    return {
        /** Primera lectura de invitaciones, al conectar. */
        async init(guild: Guild): Promise<void> {
            cache = await readInvites(guild);
        },

        /**
         * Registra una entrada. Lee las invitaciones de nuevo y compara con la
         * lectura anterior: la que subió de usos es la que usó la persona.
         * (Se lee en cada entrada, así que no hace falta escuchar la creación
         * de invitaciones ni pedir el intent `GuildInvites`.)
         */
        logJoin(member: GuildMember): Promise<void> {
            const task = queue.then(async () => {
                const after = await readInvites(member.guild);
                const match: InviteMatch =
                    cache && after
                        ? matchUsedInvite(cache, after)
                        : { kind: "unknown" };
                if (after) cache = after;

                await sendToChannel(client, config.channels.log, {
                    embeds: [
                        joinEmbed(
                            member,
                            describeMatch(match, config.inviteLabels),
                        ),
                    ],
                    allowedMentions: { parse: [] }, // el log no debe notificar a nadie
                });
            });
            queue = task.catch(() => undefined); // un fallo no bloquea las entradas siguientes
            return task;
        },

        /** Registra una salida. */
        async logLeave(
            member: GuildMember | PartialGuildMember,
        ): Promise<void> {
            await sendToChannel(client, config.channels.log, {
                embeds: [leaveEmbed(member)],
                allowedMentions: { parse: [] },
            });
        },
    };
}

export type MemberLog = ReturnType<typeof createMemberLog>;

/**
 * Todo lo que Rakim escribe en Discord vive aquí, para ajustar el tono o la
 * redacción sin tocar la lógica. Voz de Rakim: breve, seca y cálida; español
 * neutro, tuteo y un solo emoji como máximo por mensaje.
 */
import type { InviteMatch, InviteSnapshot } from "./lib/invites.js";

export interface WelcomeChannels {
    intro: string;
    askFeedback: string;
    serverFeedback: string;
    links: string;
}

/** Borrador del mensaje de bienvenida (el texto final lo define el equipo). */
export function welcomeMessage(
    userId: string,
    channels: WelcomeChannels,
): string {
    return [
        `Te damos la bienvenida a Chamba Lab, <@${userId}>. Soy Rakim. Aquí nadie te apura: es una comunidad tranquila para conectar, inspirarte y crecer en tecnología.`,
        "",
        "Para empezar:",
        `- Cuéntanos de ti en <#${channels.intro}>: tu nombre, de dónde eres, en qué trabajas o qué estudias, y tus hobbies e intereses. Lo que quieras compartir.`,
        `- ¿Quieres feedback de tu portafolio, GitHub, LinkedIn o CV? Pídelo en <#${channels.askFeedback}>.`,
        "- Este canal es donde conversamos día a día.",
        `- Si tienes ideas para mejorar el servidor, déjalas en <#${channels.serverFeedback}>.`,
        `- Las redes y la descripción completa del servidor están en <#${channels.links}>.`,
        "",
        "Pasa por aquí cuando quieras. El café corre por tu cuenta. ☕",
    ].join("\n");
}

/** Aviso de que ya se puede volver a hacer bump. */
export function bumpReminderMessage(
    roleId: string | undefined,
    cooldownMinutes: number,
): string {
    const mention = roleId ? `<@&${roleId}> ` : "";
    return `${mention}Pasaron ${cooldownMinutes} minutos. Toca hacer \`/bump\`.`;
}

/** Textos de los embeds del canal de logs. */
export const logText = {
    joinTitle: (isBot: boolean) =>
        isBot ? "Entró un bot" : "Entró un miembro",
    leaveTitle: (isBot: boolean) =>
        isBot ? "Salió un bot" : "Salió un miembro",
    member: "Miembro",
    id: "ID",
    accountCreated: "Cuenta creada",
    invite: "Invitación",
    joinedAt: "Se unió",
    unknown: "Desconocido",
    roles: "Roles",
    noRoles: "Ninguno",
};

/** Texto legible de una invitación: nombre configurado o código, quién la creó y sus usos. */
export function describeInvite(
    invite: InviteSnapshot,
    labels: Record<string, string>,
): string {
    const name = labels[invite.code];
    const head = name ? `${name} (\`${invite.code}\`)` : `\`${invite.code}\``;
    const by = invite.inviterId ? ` · creada por <@${invite.inviterId}>` : "";
    const uses = ` · ${invite.uses} ${invite.uses === 1 ? "uso" : "usos"}`;
    return head + by + uses;
}

export function describeMatch(
    match: InviteMatch,
    labels: Record<string, string>,
): string {
    switch (match.kind) {
        case "known":
            return describeInvite(match.invite, labels);
        case "ambiguous":
            return `No se pudo determinar. Posibles: ${match.candidates
                .map((invite) => labels[invite.code] ?? `\`${invite.code}\``)
                .join(", ")}`;
        case "unknown":
            return "No se pudo determinar (invitación vanity, enlace de otro tipo o permisos insuficientes)";
    }
}

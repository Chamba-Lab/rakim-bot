import {
    EmbedBuilder,
    type GuildMember,
    type PartialGuildMember,
} from "discord.js";

import { logText } from "../messages.js";

const COLOR_JOIN = 0x57f287;
const COLOR_LEAVE = 0xed4245;

/** Marca de tiempo de Discord: cada persona la ve en su hora local. */
function discordTime(ms: number): string {
    return `<t:${Math.floor(ms / 1000)}:R>`;
}

/** Embed del canal de logs cuando entra alguien; `inviteText` ya viene redactado. */
export function joinEmbed(member: GuildMember, inviteText: string) {
    return new EmbedBuilder()
        .setColor(COLOR_JOIN)
        .setTitle(logText.joinTitle(member.user.bot))
        .setThumbnail(member.user.displayAvatarURL())
        .addFields(
            {
                name: logText.member,
                value: `<@${member.id}> (${member.user.tag})`,
            },
            { name: logText.id, value: member.id, inline: true },
            {
                name: logText.accountCreated,
                value: discordTime(member.user.createdTimestamp),
                inline: true,
            },
            { name: logText.invite, value: inviteText },
        )
        .setTimestamp();
}

/** Embed del canal de logs cuando sale alguien. El miembro puede ser parcial: Discord no siempre lo tiene en caché. */
export function leaveEmbed(member: GuildMember | PartialGuildMember) {
    const roles = member.roles.cache
        .filter((role) => role.id !== member.guild.id) // @everyone no cuenta
        .map((role) => role.name);

    return new EmbedBuilder()
        .setColor(COLOR_LEAVE)
        .setTitle(logText.leaveTitle(member.user.bot))
        .setThumbnail(member.user.displayAvatarURL())
        .addFields(
            {
                name: logText.member,
                value: `<@${member.id}> (${member.user.tag})`,
            },
            { name: logText.id, value: member.id, inline: true },
            {
                name: logText.joinedAt,
                value: member.joinedTimestamp
                    ? discordTime(member.joinedTimestamp)
                    : logText.unknown,
                inline: true,
            },
            {
                name: logText.roles,
                value: roles.length > 0 ? roles.join(", ") : logText.noRoles,
            },
        )
        .setTimestamp();
}

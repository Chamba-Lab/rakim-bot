import { Events } from "discord.js";

import { defineEvent } from "./types.js";

/** Alguien salió del servidor (o lo sacaron): se registra en el log. */
export default defineEvent({
    name: Events.GuildMemberRemove,
    async execute(ctx, member) {
        if (member.guild.id !== ctx.config.guildId) return;
        await ctx.memberLog.logLeave(member);
    },
});

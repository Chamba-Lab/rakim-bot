import { z } from "zod";

const snowflake = z.string().regex(/^\d{17,20}$/, "debe ser un ID de Discord");

const inviteLabels = z.string().transform((raw, ctx) => {
    try {
        return z.record(z.string(), z.string()).parse(JSON.parse(raw));
    } catch {
        ctx.addIssue({
            code: "custom",
            message: 'debe ser un JSON como {"codigo":"nombre"}',
        });
        return z.NEVER;
    }
});

const bumpPattern = z.string().transform((raw, ctx) => {
    try {
        return new RegExp(raw, "i");
    } catch {
        ctx.addIssue({
            code: "custom",
            message: "debe ser una expresión regular válida",
        });
        return z.NEVER;
    }
});

const schema = z.object({
    DISCORD_TOKEN: z.string().min(1),
    GUILD_ID: snowflake,
    WELCOME_CHANNEL_ID: snowflake,
    INTRO_CHANNEL_ID: snowflake,
    ASK_FEEDBACK_CHANNEL_ID: snowflake,
    SERVER_FEEDBACK_CHANNEL_ID: snowflake,
    LINKS_CHANNEL_ID: snowflake,
    LOG_CHANNEL_ID: snowflake,
    BUMP_CHANNEL_ID: snowflake,
    BUMP_ROLE_ID: snowflake.optional(),
    DISBOARD_BOT_ID: snowflake.default("302050872383242240"),
    BUMP_SUCCESS_PATTERN: bumpPattern.default(/bump done/i),
    BUMP_COOLDOWN_MINUTES: z.coerce.number().int().positive().default(120),
    INVITE_LABELS: inviteLabels.default({}),
    STATE_PATH: z.string().min(1).default("data/state.json"),
});

export interface Config {
    token: string;
    guildId: string;
    channels: {
        welcome: string;
        intro: string;
        askFeedback: string;
        serverFeedback: string;
        links: string;
        log: string;
        bump: string;
    };
    bump: {
        roleId: string | undefined;
        disboardBotId: string;
        successPattern: RegExp;
        cooldownMs: number;
    };
    inviteLabels: Record<string, string>;
    statePath: string;
}

/** Lee y valida la configuración del entorno; falla con todos los errores a la vez. */
export function loadConfig(
    env: Record<string, string | undefined> = process.env,
): Config {
    // Una variable vacía (como en .env.example) cuenta como no definida.
    const defined = Object.fromEntries(
        Object.entries(env).filter(([, value]) => value !== ""),
    );
    const result = schema.safeParse(defined);
    if (!result.success) {
        const problems = result.error.issues
            .map((issue) => `- ${issue.path.join(".")}: ${issue.message}`)
            .join("\n");
        throw new Error(`Configuración inválida:\n${problems}`);
    }
    const parsed = result.data;
    return {
        token: parsed.DISCORD_TOKEN,
        guildId: parsed.GUILD_ID,
        channels: {
            welcome: parsed.WELCOME_CHANNEL_ID,
            intro: parsed.INTRO_CHANNEL_ID,
            askFeedback: parsed.ASK_FEEDBACK_CHANNEL_ID,
            serverFeedback: parsed.SERVER_FEEDBACK_CHANNEL_ID,
            links: parsed.LINKS_CHANNEL_ID,
            log: parsed.LOG_CHANNEL_ID,
            bump: parsed.BUMP_CHANNEL_ID,
        },
        bump: {
            roleId: parsed.BUMP_ROLE_ID,
            disboardBotId: parsed.DISBOARD_BOT_ID,
            successPattern: parsed.BUMP_SUCCESS_PATTERN,
            cooldownMs: parsed.BUMP_COOLDOWN_MINUTES * 60_000,
        },
        inviteLabels: parsed.INVITE_LABELS,
        statePath: parsed.STATE_PATH,
    };
}

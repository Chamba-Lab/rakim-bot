import type { Client } from "discord.js";

import type { Config } from "./config.js";
import type { StateStore } from "./lib/state.js";
import { createBump, type Bump } from "./services/bump.js";
import { createMemberLog, type MemberLog } from "./services/memberLog.js";
import { createWelcome, type Welcome } from "./services/welcome.js";

/** Lo que cada evento necesita para trabajar: la configuración y las tres funciones del bot. */
export interface Context {
    config: Config;
    welcome: Welcome;
    memberLog: MemberLog;
    bump: Bump;
}

export function createContext(
    client: Client,
    config: Config,
    store: StateStore,
): Context {
    return {
        config,
        welcome: createWelcome(client, config),
        memberLog: createMemberLog(client, config),
        bump: createBump(client, config, store),
    };
}

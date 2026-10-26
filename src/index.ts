import { Client, GatewayIntentBits, Partials } from "discord.js";

import { loadConfig } from "./config.js";
import { createContext } from "./context.js";
import { registerEvents } from "./events/index.js";
import { log } from "./lib/logger.js";
import { StateStore } from "./lib/state.js";

// Si falta o está mal una variable de entorno, aquí termina el proceso con la lista de errores.
const config = loadConfig();
const store = new StateStore(config.statePath);

// Solo los intents que el bot usa (el porqué de cada uno está en docs/architecture.md).
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds, // servidor, canales y roles
        GatewayIntentBits.GuildMembers, // privilegiado: entradas, salidas y fin de la pantalla de reglas
        GatewayIntentBits.GuildMessages, // mensajes de Disboard
        GatewayIntentBits.MessageContent, // privilegiado: leer el texto de esos mensajes
    ],
    // Permite recibir la salida de miembros que no están en caché.
    partials: [Partials.GuildMember],
});

registerEvents(client, createContext(client, config, store));

// Cierre ordenado cuando el host detiene el proceso.
for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.once(signal, () => {
        log.info(`Recibido ${signal}; cerrando`);
        void client.destroy().then(() => process.exit(0));
    });
}

await client.login(config.token);

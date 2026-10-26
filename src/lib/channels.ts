import type { Client, MessageCreateOptions } from "discord.js";

/**
 * Publica un mensaje en un canal por su ID. Falla con un error claro si el
 * canal no existe o el bot no puede escribir ahí (el que llama decide si
 * registrarlo o dejarlo subir).
 */
export async function sendToChannel(
    client: Client,
    channelId: string,
    message: MessageCreateOptions,
): Promise<void> {
    const channel = await client.channels.fetch(channelId);
    if (!channel?.isSendable()) {
        throw new Error(`El canal ${channelId} no existe o no admite mensajes`);
    }
    await channel.send(message);
}

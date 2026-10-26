import { log } from "./logger.js";
import type { StateStore } from "./state.js";

export interface BumpMessage {
    authorId: string;
    /** Texto del mensaje y de sus embeds (título y descripción). */
    texts: string[];
}

export interface BumpDetection {
    disboardBotId: string;
    successPattern: RegExp;
}

/** ¿Es la confirmación de que Disboard registró un bump? Las respuestas de error (aún en enfriamiento) no cuentan. */
export function isBumpSuccess(
    message: BumpMessage,
    detection: BumpDetection,
): boolean {
    if (message.authorId !== detection.disboardBotId) return false;
    return message.texts.some((text) => detection.successPattern.test(text));
}

interface ReminderDeps {
    store: StateStore;
    cooldownMs: number;
    /** Publica el aviso en Discord. */
    send: () => Promise<void>;
    now?: () => number;
}

/**
 * Recordatorio de bump: tras cada bump programa un aviso para cuando termine
 * el enfriamiento. El momento queda guardado, así que un reinicio del bot no
 * lo pierde.
 */
export class BumpReminder {
    private timer: NodeJS.Timeout | undefined;
    private readonly now: () => number;

    constructor(private readonly deps: ReminderDeps) {
        this.now = deps.now ?? Date.now;
    }

    /** Retoma el aviso pendiente al arrancar; si venció con el bot apagado, avisa de inmediato. */
    start(): void {
        const { dueAt } = this.deps.store.get().bump;
        if (dueAt !== null) this.arm(dueAt);
    }

    /** Se acaba de hacer un bump: el siguiente aviso es dentro de un enfriamiento completo. */
    async schedule(): Promise<void> {
        const dueAt = this.now() + this.deps.cooldownMs;
        const saved = this.deps.store.update((state) => {
            state.bump.dueAt = dueAt;
        });
        this.arm(dueAt);
        await saved;
    }

    /** Cancela el aviso en curso sin borrarlo del estado (el proceso se está cerrando). */
    stop(): void {
        clearTimeout(this.timer);
    }

    private arm(dueAt: number): void {
        clearTimeout(this.timer);
        this.timer = setTimeout(
            () => void this.fire(),
            Math.max(0, dueAt - this.now()),
        );
    }

    private async fire(): Promise<void> {
        // Se limpia antes de avisar: si el envío falla, no se reintenta en bucle.
        const saved = this.deps.store.update((state) => {
            state.bump.dueAt = null;
        });
        try {
            await this.deps.send();
        } catch (error) {
            log.error("No se pudo enviar el recordatorio de bump", error);
        }
        await saved;
    }
}

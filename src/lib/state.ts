import { mkdirSync, readFileSync } from "node:fs";
import { rename, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

import { log } from "./logger.js";

export interface BotState {
    bump: {
        /** Momento (ms desde epoch) en que se puede volver a hacer bump; `null` si no hay aviso pendiente. */
        dueAt: number | null;
    };
}

const EMPTY_STATE: BotState = { bump: { dueAt: null } };

/**
 * Estado persistente del bot en un archivo JSON. Alcanza para un único
 * proceso y unos pocos valores; si crece, se reemplaza por SQLite sin tocar
 * a quien lo usa (ver docs/decisions.md).
 */
export class StateStore {
    private state: BotState;
    private writing: Promise<void> = Promise.resolve();
    private writes = 0;

    constructor(private readonly path: string) {
        this.state = this.read();
    }

    get(): BotState {
        return this.state;
    }

    /** Aplica el cambio en memoria al instante y lo guarda en disco; las escrituras se encolan para no pisarse. */
    update(mutate: (state: BotState) => void): Promise<void> {
        mutate(this.state);
        const snapshot = JSON.stringify(this.state, null, 4);
        // Un nombre único por escritura: dos procesos o instancias no se pisan el archivo temporal.
        const temp = `${this.path}.${process.pid}.${++this.writes}.tmp`;
        this.writing = this.writing
            .then(async () => {
                mkdirSync(dirname(this.path), { recursive: true });
                await writeFile(temp, snapshot, "utf8");
                await rename(temp, this.path);
            })
            // Un fallo al guardar se registra y no frena las escrituras siguientes.
            .catch((error) => log.error("No se pudo guardar el estado", error));
        return this.writing;
    }

    /** Espera a que terminen las escrituras pendientes. */
    flush(): Promise<void> {
        return this.writing;
    }

    private read(): BotState {
        let raw: string;
        try {
            raw = readFileSync(this.path, "utf8");
        } catch (error) {
            if ((error as NodeJS.ErrnoException).code === "ENOENT") {
                return structuredClone(EMPTY_STATE);
            }
            throw error;
        }
        const parsed = JSON.parse(raw) as Partial<BotState>;
        const dueAt = parsed.bump?.dueAt;
        return { bump: { dueAt: typeof dueAt === "number" ? dueAt : null } };
    }
}

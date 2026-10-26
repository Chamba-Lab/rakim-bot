type Level = "info" | "warn" | "error";

function write(level: Level, message: string, error?: unknown): void {
    const line = `${new Date().toISOString()} ${level.toUpperCase()} ${message}`;
    const sink = level === "info" ? console.log : console[level];
    if (error === undefined) sink(line);
    else sink(line, error);
}

export const log = {
    info: (message: string) => write("info", message),
    warn: (message: string, error?: unknown) => write("warn", message, error),
    error: (message: string, error?: unknown) => write("error", message, error),
};

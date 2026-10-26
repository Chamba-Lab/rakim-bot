import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable

from .state import State

log = logging.getLogger("rakim")


def is_bump_success(
    author_id: int,
    texts: list[str],
    disboard_id: int,
    pattern: re.Pattern[str],
) -> bool:
    """¿Es la confirmación de que Disboard registró un bump?

    La respuesta de «espera X minutos» no coincide con el patrón, así que no cuenta.
    """
    return author_id == disboard_id and any(pattern.search(t) for t in texts)


class BumpReminder:
    """Avisa cuando termina el enfriamiento del bump.

    El momento del aviso se guarda en el estado: un reinicio no lo pierde, y si
    venció con el bot apagado, se avisa de inmediato (una sola vez).
    """

    def __init__(
        self,
        state: State,
        cooldown_seconds: float,
        send: Callable[[], Awaitable[None]],
        now: Callable[[], float] = time.time,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self.state = state
        self.cooldown = cooldown_seconds
        self.send = send
        self.now = now
        self.sleep = sleep
        self.task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Retoma el aviso pendiente al arrancar."""
        if self.state.bump_due_at is not None:
            self._arm(self.state.bump_due_at)

    def schedule(self) -> None:
        """Se acaba de hacer un bump: el siguiente aviso es dentro de un enfriamiento."""
        self.state.bump_due_at = self.now() + self.cooldown
        self.state.save()
        self._arm(self.state.bump_due_at)

    def _arm(self, due_at: float) -> None:
        if self.task:
            self.task.cancel()
        self.task = asyncio.create_task(self._wait(due_at))

    async def _wait(self, due_at: float) -> None:
        await self.sleep(max(0.0, due_at - self.now()))
        # Se limpia antes de avisar: si el envío falla, no se reintenta en bucle.
        self.state.bump_due_at = None
        self.state.save()
        try:
            await self.send()
        except Exception:
            log.exception("No se pudo enviar el recordatorio de bump")

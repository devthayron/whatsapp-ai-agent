import asyncio
import logging
import signal

from redis.exceptions import RedisError

from agent.processor import respond_to_user
from cache import debounce
from config import settings
from database.users import get_user_by_id
from integrations.messaging import messaging_service

logger = logging.getLogger(__name__)

POLL_INTERVAL = 0.5
ERROR_BACKOFF = 5
DRAIN_TIMEOUT = 30


def _respond(user_id: int) -> None:
    """Código síncrono (PG, IA, envio de mensagem): roda em thread."""
    user = get_user_by_id(user_id)
    if user:
        respond_to_user(
            user, lambda text: messaging_service.send_message(user.number, text)
        )


async def _process(user_id: int, lease: float) -> None:
    try:
        await asyncio.to_thread(_respond, user_id)
    except Exception:
        # Sem ack: o lease expira e outro worker poderá tentar novamente.
        logger.exception(
            "Erro ao processar debounce | user_id=%s",
            user_id,
        )
        return

    try:
        await debounce.ack(user_id, lease)
    except RedisError:
        logger.exception(
            "Erro ao confirmar debounce | user_id=%s",
            user_id,
        )


async def run(stop: asyncio.Event) -> None:
    logger.info("Worker de debounce iniciado")
    tasks: set[asyncio.Task] = set()

    while not stop.is_set():
        wait = POLL_INTERVAL
        try:
            free = settings.WORKER_CONCURRENCY - len(tasks)
            if free > 0:
                user_ids, lease = await debounce.claim_due(free)
                for user_id in user_ids:
                    task = asyncio.create_task(_process(user_id, lease))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)
        except RedisError:
            logger.exception("Worker sem acesso ao Redis")
            wait = ERROR_BACKOFF

        try:
            await asyncio.wait_for(stop.wait(), timeout=wait)
        except asyncio.TimeoutError:
            pass

    if tasks:  # o que não terminar volta pelo lease
        await asyncio.wait(tasks, timeout=DRAIN_TIMEOUT)

    logger.info("Worker de debounce encerrado")


async def main() -> None:
    """Execução como processo separado: python -m app.worker (Linux/macOS)."""
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await run(stop)


if __name__ == "__main__":
    from logger import setup_logging

    setup_logging()
    asyncio.run(main())

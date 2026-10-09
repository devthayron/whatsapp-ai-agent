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


def _respond(user_id: int) -> bool:
    """
    Código síncrono (PG, IA, envio de mensagem): roda em thread.
    Retorna True se o trabalho terminou (ack) e False se deve tentar de novo.
    """
    user = get_user_by_id(user_id)
    if not user:
        return True

    result = respond_to_user(
        user, lambda text: messaging_service.send_message(user.number, text)
    )
    return not result.get("retry", False)


async def _retry(user_id: int, lease: float) -> None:
    attempts = await debounce.retry(user_id, lease)

    if attempts > 0:
        logger.warning(
            "Nova tentativa agendada | user_id=%s | tentativas=%s",
            user_id,
            attempts,
        )
    elif attempts == 0:
        logger.error("Tentativas esgotadas, descartando | user_id=%s", user_id)
    else:
        logger.debug("Retry ignorado, chegou mensagem nova | user_id=%s", user_id)


async def _process(user_id: int, lease: float) -> None:
    try:
        done = await asyncio.to_thread(_respond, user_id)
    except Exception:
        logger.exception("Erro ao processar debounce | user_id=%s", user_id)
        done = False

    try:
        if done:
            await debounce.ack(user_id, lease)
        else:
            await _retry(user_id, lease)
    except RedisError:
        # Sem ack/retry: o lease expira e outro ciclo reivindica.
        logger.exception("Erro ao confirmar debounce | user_id=%s", user_id)


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

import logging
import time
from datetime import datetime

from redis.exceptions import RedisError

from agent.model import generate_response
from app.schemas.message import MessageReceived, MessageSchema
from app.schemas.user import UserSchema
from cache import debounce
from database.conversations import (
    TIMEZONE,
    get_message_history,
    message_exists,
    save_assistant_message,
    save_user_message,
    timestamp_to_datetime,
)
from database.users import get_or_create_user

logger = logging.getLogger(__name__)

ERROR_MESSAGE = (
    "Desculpe, não consegui processar sua mensagem agora. Tente novamente em instantes."
)
DUPLICATE = {"status": "duplicate", "response": None}


def _ingest(message: MessageReceived):
    """Salva a mensagem do usuário no PostgreSQL. Retorna (user, None) se duplicada."""
    if message_exists(message.external_id):
        logger.info("Mensagem duplicada | external_id=%s", message.external_id)
        return None, None

    user = get_or_create_user(number=message.number, name=message.name)

    saved = save_user_message(
        MessageSchema(
            external_id=message.external_id,
            user_id=user.id,
            role="user",
            content=message.content,
            content_type=message.content_type,
            sent_at=timestamp_to_datetime(
                message.timestamp
                if message.timestamp is not None
                else datetime.now(TIMEZONE)
            ),
        )
    )

    return user, saved


def enqueue_message(message: MessageReceived, send_msg=None) -> dict:
    """Webhook: persiste, agenda o debounce e retorna sem chamar a IA."""
    user, saved = _ingest(message)

    if saved is None:
        return DUPLICATE

    try:
        debounce.schedule(user.id)
        return {"status": "queued", "response": None}

    except RedisError:
        logger.exception("Redis indisponível, respondendo sem debounce")
        return respond_to_user(user, send_msg)


def process_conversation(message: MessageReceived, send_msg=None) -> dict:
    """Fluxo síncrono, sem debounce (/chat/)."""
    user, saved = _ingest(message)

    if saved is None:
        return DUPLICATE

    return respond_to_user(user, send_msg)


def _failed(response: str, retry: bool = False) -> dict:
    """
    retry=True só quando o usuário não recebeu nada. Se algo já foi entregue
    (resposta ou fallback), repetir o processamento duplicaria a mensagem.
    """
    return {"status": "failed", "response": response, "retry": retry}


def respond_to_user(user: UserSchema, send_msg=None) -> dict:
    """Lê o histórico no PostgreSQL, chama a IA, envia e grava a resposta."""
    start = time.monotonic()
    history = get_message_history(user.id)

    try:
        response = generate_response(history)
    except Exception:
        logger.exception("Falha ao gerar resposta da IA | number=%s", user.number)
        fallback_sent = False
        if send_msg:
            try:
                send_msg(ERROR_MESSAGE)
                fallback_sent = True
            except Exception:
                logger.exception("Falha ao enviar fallback | number=%s", user.number)
        # Fallback entregue: fim. Sem entrega, o usuário ficou sem nada.
        return _failed(ERROR_MESSAGE, retry=bool(send_msg) and not fallback_sent)

    if send_msg:
        try:
            send_msg(response)
        except Exception:
            logger.exception("Falha ao enviar resposta | number=%s", user.number)
            # Nada foi entregue nem gravado: seguro repetir.
            return _failed(response, retry=True)

    try:
        save_assistant_message(user.id, response)
    except Exception:
        # Já foi enviada: não repetir, senão o usuário recebe duas vezes.
        logger.exception("Resposta enviada mas não gravada | number=%s", user.number)
        return _failed(response)

    logger.info(
        "Processamento concluído | number=%s | tempo=%.2fs",
        user.number,
        time.monotonic() - start,
    )
    return {"status": "processed", "response": response}

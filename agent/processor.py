import logging
import time
from datetime import datetime

from agent.model import generate_response
from app.schemas.message import MessageReceived, MessageSchema
from database.conversations import (
    TIMEZONE,
    get_message_history,
    message_exists,
    save_conversation,
    timestamp_to_datetime,
)
from database.users import get_or_create_user

logger = logging.getLogger(__name__)

ERROR_MESSAGE = (
    "Desculpe, não consegui processar sua mensagem agora. Tente novamente em instantes."
)


def process_conversation(message: MessageReceived, send_msg=None) -> dict:
    """Processa a conversa recebida, gerando uma resposta usando o modelo de IA.

    Args:
        message: Mensagem recebida e normalizada.
        send_msg: Função para enviar a resposta gerada. Se None, não envia a resposta.

    Returns:
        dict: retorna um dicionário com o status do processamento e a resposta gerada (se houver).
    """

    start = time.monotonic()

    if message_exists(message.external_id):
        logger.info(
            "Mensagem duplicada | number=%s | external_id=%s",
            message.number,
            message.external_id,
        )

        return {
            "status": "duplicate",
            "response": None,
        }

    user = get_or_create_user(number=message.number, name=message.name)

    user_message = MessageSchema(
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

    history = get_message_history(user.id)
    history.append(user_message)

    logger.debug(
        "Contexto recuperado | number=%s | messages=%s", message.number, len(history)
    )

    try:
        response = generate_response(history)

    except Exception:
        logger.exception(
            "Falha ao gerar resposta da IA | number=%s | external_id=%s",
            message.number,
            message.external_id,
        )

        if send_msg is not None:
            try:
                send_msg(ERROR_MESSAGE)
            except Exception:
                logger.exception(
                    "Falha ao enviar fallback | number=%s | external_id=%s",
                    message.number,
                    message.external_id,
                )

        return {
            "status": "failed",
            "response": ERROR_MESSAGE,
        }

    if send_msg is not None:
        try:
            send_msg(response)

        except Exception:
            logger.exception(
                "Falha ao enviar resposta | number=%s | external_id=%s",
                message.number,
                message.external_id,
            )

            return {
                "status": "failed",
                "response": response,
            }

    if not save_conversation(user_message, response):
        logger.error(
            "Resposta gerada mas não gravada | number=%s | external_id=%s",
            message.number,
            message.external_id,
        )

        return {
            "status": "failed",
            "response": response,
        }

    elapsed = time.monotonic() - start

    logger.info(
        "Processamento concluído | number=%s | external_id=%s | tempo=%.2fs",
        message.number,
        message.external_id,
        elapsed,
    )

    return {
        "status": "processed",
        "response": response,
    }

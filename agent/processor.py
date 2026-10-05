import logging
import time

from agent.model import generate_response
from database.conversations import (
    get_message_history,
    message_exists,
    save_conversation,
)
from database.users import get_or_create_user

logger = logging.getLogger(__name__)

ERROR_MESSAGE = (
    "Desculpe, não consegui processar sua mensagem agora. Tente novamente em instantes."
)


def process_conversation(msg, send_msg):
    """
    Processa uma mensagem, gera e envia a resposta e salva a conversa.

    Args:
        msg: Dados normalizados da mensagem.
        send_msg: Função responsável por enviar a mensagem ao usuário.

    Returns:
        "processed", "duplicate" ou "failed".
    """

    start = time.monotonic()
    number = msg["number"]
    external_id = msg["external_id"]

    logger.info(
        "Processando mensagem | number=%s | external_id=%s",
        number,
        external_id,
    )

    if message_exists(external_id):
        logger.info(
            "Mensagem duplicada | number=%s | external_id=%s", number, external_id
        )
        return "duplicate"

    user_id = get_or_create_user(number=number, name=msg["push_name"])

    history = get_message_history(user_id)
    history.append(
        {
            "role": "user",
            "content": msg["content"],
        }
    )

    logger.debug("Contexto recuperado | number=%s | messages=%s", number, len(history))

    try:
        response = generate_response(history)

    except Exception:
        logger.exception(
            "Falha ao gerar resposta da IA | number=%s | external_id=%s",
            number,
            external_id,
        )

        try:
            send_msg(ERROR_MESSAGE)

        except Exception:
            logger.exception(
                "Falha ao enviar fallback | number=%s | external_id=%s",
                number,
                external_id,
            )

        return "failed"

    try:
        send_msg(response)

    except Exception:
        logger.exception(
            "Falha ao enviar resposta | number=%s | external_id=%s",
            number,
            external_id,
        )
        return "failed"

    if not save_conversation(msg, response):
        logger.error(
            "Resposta enviada mas não gravada | number=%s | external_id=%s",
            number,
            external_id,
        )
        return "failed"

    elapsed = time.monotonic() - start

    logger.info(
        "Processamento concluído | number=%s | external_id=%s | tempo=%.2fs",
        number,
        external_id,
        elapsed,
    )

    return "processed"

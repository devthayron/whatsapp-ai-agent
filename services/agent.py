import logging
import time
from services.openai import openai_service
from database.conversations import (
    ensure_history,
    save_message,
    get_openai_history,
)
from database.users import get_or_create_user

logger = logging.getLogger(__name__)

def process_conversation(msg):
    start = time.monotonic()

    logger.info(
        "Processando mensagem recebida | number=%s",
        msg["number"],
    )

    user_id = get_or_create_user(
        number=msg["number"],
        name=msg["push_name"],
    )

    ensure_history(user_id)

    save_message(**msg)

    history = get_openai_history(user_id)

    

    logger.debug(
        "Solicitando resposta da IA | number=%s",
        msg["number"],
    )

    try:
        response = openai_service.generate_response(history)

    except Exception:
        logger.exception(
            "Falha ao gerar resposta da IA | number=%s",
            msg["number"],
        )

        response = (
            "Desculpe, não consegui processar sua mensagem agora. "
            "Tente novamente em instantes."
        )

    save_message(
        number=msg["number"],
        push_name=msg["push_name"],
        from_me=True,
        content=response,
    )

    elapsed = time.monotonic() - start

    logger.info(
        "Processamento da conversa concluído | number=%s | tempo=%.2fs",
        msg["number"],
        elapsed,

    )

    return response
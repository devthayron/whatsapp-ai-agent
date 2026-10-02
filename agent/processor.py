import logging
import time
from typing import Any

from agent.model import generate_response
from database.conversations import get_message_history, save_message
from database.users import get_or_create_user

logger = logging.getLogger(__name__)

ERROR_MESSAGE = (
    "Desculpe, não consegui processar sua mensagem agora. Tente novamente em instantes."
)


def process_conversation(msg: dict[str, Any]) -> str:
    """
    Processa uma mensagem recebida e gera uma resposta com o modelo de IA.

    Args:
        msg: Dados normalizados da mensagem recebida.

    Returns:
        Texto da resposta gerada pela IA.
    """

    start = time.monotonic()
    number = msg["number"]

    logger.info("Processando mensagem recebida | number=%s", number)

    user_id = get_or_create_user(number=number, name=msg["push_name"])

    if not save_message(**msg):
        logger.warning(
            "Mensagem não processada | number=%s | message_id=%s",
            number,
            msg["message_id"],
        )
        return

    history = get_message_history(user_id)

    logger.debug("Solicitando resposta da IA | number=%s", number)

    try:
        response = generate_response(history)

    except Exception:
        logger.exception("Falha ao gerar resposta da IA | number=%s", number)
        response = ERROR_MESSAGE

    save_message(
        number=number,
        push_name=msg["push_name"],
        from_me=True,
        content=response,
    )

    elapsed = time.monotonic() - start

    logger.info(
        "Processamento da conversa concluído | number=%s | tempo=%.2fs", number, elapsed
    )

    return response

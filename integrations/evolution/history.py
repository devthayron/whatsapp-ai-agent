import logging

from database.connection import SessionLocal
from database.conversations import import_history
from database.models import User
from integrations.evolution.client import evolution_service
from integrations.evolution.parser import normalize_message

logger = logging.getLogger(__name__)


def get_history(number):
    """Obtém, normaliza e ordena o histórico da Evolution."""
    try:
        records = evolution_service.get_messages_by_number(number)

    except Exception:
        logger.exception(
            "Erro ao buscar histórico na Evolution API | number=%s",
            number,
        )
        return None

    messages = []

    for record in records:
        message = normalize_message(record)

        if message:
            messages.append(message)

    messages.sort(key=lambda message: message["timestamp"])

    logger.debug(
        "Histórico obtido | number=%s | total_messages=%s",
        number,
        len(messages),
    )

    return messages


def ensure_history(user_id):
    """
    Garante que o histórico inicial do usuário esteja sincronizado.
    """
    with SessionLocal() as session:
        user = session.query(User).filter_by(id=user_id).one()

        if user.history_imported:
            logger.debug(
                "Histórico já sincronizado | number=%s",
                user.number,
            )
            return

        number = user.number

    logger.info(
        "Histórico ainda não sincronizado | number=%s",
        number,
    )

    messages = get_history(number)

    if messages is None:
        logger.warning(
            "Sincronização abortada | number=%s",
            number,
        )
        return

    import_history(user_id, messages)

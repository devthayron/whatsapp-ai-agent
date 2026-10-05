import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from database.connection import SessionLocal
from database.models import Message
from database.users import _get_or_create_user

logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("America/Sao_Paulo")
CONTEXT_MESSAGES_LIMIT = 30


def timestamp_to_datetime(timestamp):
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=TIMEZONE)

    return timestamp


def message_exists(external_id):
    """Só leitura. Usado para descartar retries de mensagens já processadas."""
    if not external_id:
        return False

    with SessionLocal() as session:
        return (
            session.query(Message.id).filter_by(external_id=external_id).first()
            is not None
        )


def save_conversation(msg, response):
    """
    Grava a mensagem do usuário e a resposta numa única transação:
    ou entram as duas, ou nenhuma.
    """
    now = datetime.now(TIMEZONE)
    sent_at = timestamp_to_datetime(msg["timestamp"] or now)

    with SessionLocal() as session:
        try:
            user = _get_or_create_user(session, msg["number"], msg["push_name"])

            session.add_all(
                [
                    Message(
                        external_id=msg["external_id"],
                        user_id=user.id,
                        role="user",
                        content=msg["content"],
                        content_type=msg["content_type"],
                        sent_at=sent_at,
                    ),
                    Message(
                        external_id=None,
                        user_id=user.id,
                        role="assistant",
                        content=response,
                        content_type="text",
                        sent_at=now,
                    ),
                ]
            )

            session.commit()

        except IntegrityError:
            session.rollback()
            logger.warning(
                "Conversa não gravada (violação de unicidade) | "
                "number=%s | external_id=%s",
                msg["number"],
                msg["external_id"],
            )
            return False

    logger.debug(
        "Conversa gravada | number=%s | external_id=%s",
        msg["number"],
        msg["external_id"],
    )

    return True


def get_message_history(user_id, limit=CONTEXT_MESSAGES_LIMIT):
    """
    Retorna as últimas mensagens da conversa em ordem cronológica.

    A ordem vem do id autoincremental (ordem real de gravação).
    """
    with SessionLocal() as session:
        messages = (
            session.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.id.desc())
            .limit(limit)
            .all()
        )

        messages.reverse()

        logger.debug(
            "Histórico recuperado | total_messages=%s",
            len(messages),
        )

        return [
            {
                "role": message.role,
                "content": (message.content or "").strip(),
            }
            for message in messages
        ]

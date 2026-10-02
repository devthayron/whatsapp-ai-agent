import logging
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from database.connection import SessionLocal
from database.models import Message
from database.users import _get_or_create_user

logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("America/Sao_Paulo")
CONTEXT_MESSAGES_LIMIT = 30


def add_message(
    session,
    user,
    message_id,
    role,
    content,
    message_type,
    sent_at,
):
    exists = session.query(Message).filter_by(message_id=message_id).first()

    if exists:
        logger.debug(
            "Mensagem duplicada ignorada | message_id=%s",
            message_id,
        )
        return False

    session.add(
        Message(
            message_id=message_id,
            user_id=user.id,
            role=role,
            content=content,
            message_type=message_type,
            sent_at=sent_at,
        )
    )
    return True


def timestamp_to_datetime(timestamp):
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(
            timestamp,
            tz=TIMEZONE,
        )

    return timestamp


def save_message(
    number,
    push_name,
    from_me,
    content,
    message_id=None,
    message_type="conversation",
    timestamp=None,
):
    message_id = message_id or str(uuid4())

    if timestamp is None:
        timestamp = datetime.now(TIMEZONE)

    sent_at = timestamp_to_datetime(timestamp)
    role = "assistant" if from_me else "user"

    with SessionLocal() as session:
        user = _get_or_create_user(
            session,
            number,
            push_name,
        )

        saved = add_message(
            session=session,
            user=user,
            message_id=message_id,
            role=role,
            content=content,
            message_type=message_type,
            sent_at=sent_at,
        )
        if not saved:
            return False

        try:
            session.commit()

            logger.debug(
                "Mensagem salva | role=%s | number=%s | message_id=%s",
                role,
                number,
                message_id,
            )

        except IntegrityError:
            session.rollback()

            logger.exception(
                "Erro ao salvar mensagem | role=%s | number=%s | message_id=%s",
                role,
                number,
                message_id,
            )

            return False

    return True


def get_message_history(user_id, limit=CONTEXT_MESSAGES_LIMIT):
    """
    Retorna as últimas mensagens da conversa,
    preservando a ordem cronológica.
    """
    with SessionLocal() as session:
        messages = (
            session.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(
                Message.sent_at.desc(),
                Message.id.desc(),
            )
            .limit(limit)
            .all()
        )

        messages.reverse()

        logger.debug("Histórico recuperado | total_messages=%s", len(messages))

        return [
            {
                "role": message.role,
                "content": (message.content or "").strip(),
            }
            for message in messages
        ]

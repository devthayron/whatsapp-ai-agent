import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from app.schemas.message import MessageSchema
from database.connection import SessionLocal
from database.models import Message

logger = logging.getLogger(__name__)

TIMEZONE = ZoneInfo("America/Sao_Paulo")
CONTEXT_MESSAGES_LIMIT = 30


def timestamp_to_datetime(timestamp: float | datetime | None) -> datetime | None:
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=TIMEZONE)

    return timestamp


def message_exists(external_id: str | None) -> bool:
    """Verifica se uma mensagem já foi registrada pelo identificador externo."""
    if not external_id:
        return False

    with SessionLocal() as session:
        return (
            session.query(Message.id).filter_by(external_id=external_id).first()
            is not None
        )


def save_user_message(message: MessageSchema) -> MessageSchema | None:
    """Grava a mensagem recebida. Retorna None se o external_id já existia."""
    with SessionLocal() as session:
        row = Message(**message.model_dump(exclude={"id"}))
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(
                "Mensagem não gravada (unicidade) | user_id=%s | external_id=%s",
                message.user_id,
                message.external_id,
            )
            return None
        return MessageSchema.model_validate(row)


def save_assistant_message(user_id: int, response: str) -> None:
    with SessionLocal() as session:
        session.add(
            Message(
                external_id=None,
                user_id=user_id,
                role="assistant",
                content=response,
                content_type="text",
                sent_at=datetime.now(TIMEZONE),
            )
        )
        session.commit()


def get_message_history(
    user_id: int, limit: int = CONTEXT_MESSAGES_LIMIT
) -> list[MessageSchema]:
    """
    Retorna as últimas mensagens da conversa em ordem cronológica.

    Args:
        user_id: ID do usuário.
        limit: Quantidade máxima de mensagens retornadas.

    Returns:
        Lista de mensagens da conversa.
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

        logger.debug("Histórico recuperado | total_messages=%s", len(messages))

        return [MessageSchema.model_validate(m) for m in messages]

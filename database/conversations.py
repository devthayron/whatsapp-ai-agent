import logging
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from database.connection import SessionLocal
from database.models import Message, User
from database.users import _get_or_create_user
from bot.message_processor import normalize_message
from services.evolution import evolution_service

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

    exists = (
        session.query(Message)
        .filter_by(message_id=message_id)
        .first()
    )

    if exists:
        logger.debug("Mensagem duplicada ignorada | message_id=%s", message_id)
        return

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


def timestamp_to_datetime(timestamp):

    if isinstance(timestamp, int):
        return datetime.fromtimestamp(
            timestamp,
            tz=TIMEZONE,
        )

    return timestamp


def _get_history(number):

    """Obtém, normaliza e ordena cronologicamente o histórico de mensagens da Evolution API."""

    try:
        records = evolution_service.get_messages_by_number(number)

    except Exception:
        logger.exception("Erro ao buscar histórico na Evolution API | number=%s", number)
        return None

    messages = []

    for record in records:

        msg = normalize_message(record)

        if msg:
            messages.append(msg)

    messages.sort(
        key=lambda x: x["timestamp"]
    )

    return messages


def import_history_from_evolution(user_id):
    """
    Importa o histórico de conversas da Evolution API para o banco de dados.

    Executada apenas na primeira sincronização do usuário.
    """
    with SessionLocal() as session:

        user = (
            session.query(User)
            .filter_by(id=user_id)
            .one()
        )
        logger.info("Iniciando importação de histórico | number=%s", user.number)

        messages = _get_history(user.number)

        if messages is None:
            logger.warning("Importação abortada (falha na Evolution API) | number=%s", user.number)
            return

        for msg in messages:

            add_message(
                session=session,
                user=user,
                message_id=msg["message_id"],
                role="assistant" if msg["from_me"] else "user",
                content=msg["content"],
                message_type=msg.get(
                    "message_type",
                    "conversation",
                ),
                sent_at=timestamp_to_datetime(
                    msg["timestamp"]
                ),
            )
        
        user.history_imported = True

        try:
            session.commit()
            logger.info(
                "Histórico importado com sucesso | number=%s | total_messages=%s",
                user.number,
                len(messages),
            )

        except IntegrityError:
            session.rollback()
            logger.exception("Erro ao importar histórico | number=%s", user.number)


def ensure_history(user_id):
    """
    Garante que o histórico do usuário exista no banco de dados.

    Caso ainda não tenha sido importado, realiza a sincronização inicial.
    """

    with SessionLocal() as session:

        user = (
            session.query(User)
            .filter_by(id=user_id)
            .one()
        )

        if not user.history_imported:
            import_history_from_evolution(user.id)

        else:
            logger.debug("Histórico já sincronizado | number=%s", user.number)


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

        add_message(
            session=session,
            user=user,
            message_id=message_id,
            role=role,
            content=content,
            message_type=message_type,
            sent_at=sent_at,
        )


        try:
            session.commit()
            logger.debug("Mensagem salva | role=%s | number=%s | message_id=%s", role, number, message_id,)

        except IntegrityError:
            session.rollback()
            logger.exception("Erro ao salvar mensagem | role=%s | number=%s | message_id=%s", role, number, message_id,)


def get_openai_history(
    user_id,
    limit=CONTEXT_MESSAGES_LIMIT,
):
    """
    Retorna as últimas mensagens no formato esperado pela OpenAI,
    preservando a ordem cronológica da conversa.
    """

    with SessionLocal() as session:

        messages = (
            session.query(Message)
            .filter(
                Message.user_id == user_id
            )
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
                "role": msg.role,
                "content": (
                    f"[{msg.sent_at:%d/%m/%Y %H:%M}] "
                    f"{msg.content}"
                )
            }
            for msg in messages
        ]
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from database.connection import SessionLocal
from database.models import Message, User
from database.users import _get_or_create_user
from bot.message_processor import normalize_message
from services.evolution import evolution_service


TIMEZONE = ZoneInfo("America/Sao_Paulo")
MAX_HISTORY = 30


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


def convert_timestamp(timestamp):

    if isinstance(timestamp, int):
        return datetime.fromtimestamp(
            timestamp,
            tz=TIMEZONE,
        )

    return timestamp


def import_history_from_evolution(user_id):

    with SessionLocal() as session:

        user = (
            session.query(User)
            .filter_by(id=user_id)
            .one()
        )

        try:
            records = evolution_service.get_messages_by_number(
                user.number
            )

        except Exception as e:
            print(f"Erro Evolution {user.number}: {e}")
            return


        messages = []

        for record in records:

            msg = normalize_message(record)

            if msg:
                messages.append(msg)


        # garante ordem cronológica
        messages.sort(
            key=lambda x: x["timestamp"]
        )


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
                sent_at=convert_timestamp(
                    msg["timestamp"]
                ),
            )


        try:
            session.commit()

        except IntegrityError as e:
            session.rollback()
            print(e)


def ensure_history(user_id):

    with SessionLocal() as session:

        exists = (
            session.query(Message.id)
            .filter(
                Message.user_id == user_id
            )
            .first()
        )

    if exists is None:
        import_history_from_evolution(user_id)


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

    sent_at = convert_timestamp(timestamp)


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
            role="assistant" if from_me else "user",
            content=content,
            message_type=message_type,
            sent_at=sent_at,
        )


        try:
            session.commit()

        except IntegrityError as e:
            session.rollback()
            print(e)


def get_openai_history(
    user_id,
    limit=MAX_HISTORY,
):

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


        return [
            {
                "role": msg.role,
                "content": (
                    f"[{msg.sent_at:%d/%m/%Y %H:%M}] "
                    f"{msg.content}"
                ),
            }
            for msg in messages
        ]
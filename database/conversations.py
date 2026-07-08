from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from database.connection import SessionLocal, Base, engine
from database.models import Conversation, User
from services.evolution import evolution_service
from bot.processor import process_message


TIMEZONE = ZoneInfo("America/Sao_Paulo")

MAX_HISTORY = 30


Base.metadata.create_all(bind=engine)



def _add_message(
    session,
    user,
    role,
    content,
    message_type,
    timestamp,
):
    """
    Salva uma mensagem evitando duplicidade.
    """

    exists = (
        session.query(Conversation)
        .filter_by(
            user_id=user.id,
            role=role,
            content=content,
            timestamp=timestamp,
        )
        .first()
    )


    if exists:
        return


    session.add(
        Conversation(
            user_id=user.id,
            role=role,
            content=content,
            message_type=message_type,
            timestamp=timestamp,
        )
    )



def _import_history_from_evolution(session, user):
    """
    Importa mensagens antigas da Evolution API.
    """

    try:
        records = evolution_service.get_messages_by_number(
            user.number
        )

    except Exception as e:
        print(
            f"Falha ao importar histórico {user.number}: {e}"
        )
        return



    for record in records:

        msg = process_message(record)


        if not msg or not msg.get("message"):
            continue



        timestamp = msg.get("timestamp")


        if isinstance(timestamp, int):

            timestamp = datetime.fromtimestamp(
                timestamp,
                tz=TIMEZONE,
            )



        _add_message(
            session=session,
            user=user,
            role=(
                "assistant"
                if msg["from_me"]
                else "user"
            ),
            content=msg["message"],
            message_type=msg.get(
                "message_type",
                "conversation",
            ),
            timestamp=timestamp,
        )



def _get_or_create_user(
    session,
    number,
    name,
):

    user = (
        session.query(User)
        .filter_by(number=number)
        .one_or_none()
    )


    if user is None:

        user = User(
            name=name,
            number=number,
        )

        session.add(user)

        session.flush()


    elif name:

        user.name = name



    has_messages = (
        session.query(Conversation.id)
        .filter(
            Conversation.user_id == user.id
        )
        .first()
    )


    if has_messages is None:

        _import_history_from_evolution(
            session,
            user,
        )


    return user



def save_message(
    number,
    push_name,
    from_me,
    content,
    message_type="text",
    timestamp=None,
):

    with SessionLocal() as session:


        user = _get_or_create_user(
            session,
            number,
            push_name,
        )



        role = (
            "assistant"
            if from_me
            else "user"
        )



        if timestamp is None:

            timestamp = datetime.now(
                TIMEZONE
            )


        elif isinstance(timestamp, int):

            timestamp = datetime.fromtimestamp(
                timestamp,
                tz=TIMEZONE,
            )



        _add_message(
            session=session,
            user=user,
            role=role,
            content=content,
            message_type=message_type,
            timestamp=timestamp,
        )



        try:

            session.commit()


        except IntegrityError:

            session.rollback()



        _ = user.conversations


        return user



def _format_timestamp(date):

    return date.strftime(
        "%d/%m/%Y %H:%M"
    )



def get_openai_history(
    user,
    limit=MAX_HISTORY,
):

    if not user:
        return []



    messages = sorted(
        user.conversations,
        key=lambda m: m.timestamp,
    )[-limit:]



    history = []


    for msg in messages:

        history.append(
            {
                "role": msg.role,
                "content": (
                    f"[{_format_timestamp(msg.timestamp)}] "
                    f"{msg.content}"
                ),
            }
        )


    return history
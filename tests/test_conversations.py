from datetime import datetime

from app.schemas.message import MessageSchema
from database.conversations import (
    TIMEZONE,
    get_message_history,
    message_exists,
    save_conversation,
)
from database.models import Message
from database.users import get_or_create_user


def _user_message(user_id, external_id="evolution_M1", content="oi"):
    return MessageSchema(
        external_id=external_id,
        user_id=user_id,
        role="user",
        content=content,
        content_type="text",
        sent_at=datetime.now(TIMEZONE),
    )


def _user(number="5511999999999"):
    return get_or_create_user(number, "Fulano")


def test_save_conversation_is_atomic(db_session):
    user = _user()

    assert save_conversation(_user_message(user.id), "olá") is True
    # mesmo external_id
    assert save_conversation(_user_message(user.id), "olá de novo") is False

    roles = [m.role for m in db_session.query(Message).order_by(Message.id)]
    assert roles == ["user", "assistant"]  # a segunda tentativa não deixou lixo


def test_message_exists(db_session):
    user = _user()

    assert message_exists("evolution_M1") is False
    save_conversation(_user_message(user.id), "olá")
    assert message_exists("evolution_M1") is True


def test_message_exists_none_is_false(db_session):
    assert message_exists(None) is False


def test_history_returns_message_schemas_in_order(db_session):
    user = _user()
    save_conversation(_user_message(user.id, "evolution_M1", "primeira"), "r1")
    save_conversation(_user_message(user.id, "evolution_M2", "segunda"), "r2")

    history = get_message_history(user.id)

    assert all(isinstance(m, MessageSchema) for m in history)
    assert [m.content for m in history] == ["primeira", "r1", "segunda", "r2"]
    assert [m.role for m in history] == ["user", "assistant", "user", "assistant"]


def test_history_respects_limit(db_session):
    user = _user()
    for i in range(3):
        save_conversation(_user_message(user.id, f"evolution_M{i}", f"msg{i}"), f"r{i}")

    history = get_message_history(user.id, limit=2)

    assert [m.content for m in history] == ["msg2", "r2"]


def test_history_is_isolated_per_user(db_session):
    user = _user("5511900000000")
    other = _user("5511911111111")
    save_conversation(_user_message(user.id), "olá")

    assert get_message_history(other.id) == []

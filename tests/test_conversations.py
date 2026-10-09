from datetime import datetime

from app.schemas.message import MessageSchema
from database.conversations import (
    TIMEZONE,
    get_message_history,
    message_exists,
    save_assistant_message,
    save_user_message,
    timestamp_to_datetime,
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


def _exchange(user_id, external_id, content, reply):
    save_user_message(_user_message(user_id, external_id, content))
    save_assistant_message(user_id, reply)


def test_save_user_message_returns_schema_with_id(db_session):
    user = _user()

    saved = save_user_message(_user_message(user.id))

    assert isinstance(saved, MessageSchema)
    assert saved.id is not None
    assert saved.role == "user"


def test_save_user_message_duplicate_returns_none(db_session):
    user = _user()

    assert save_user_message(_user_message(user.id)) is not None
    assert save_user_message(_user_message(user.id)) is None

    assert db_session.query(Message).count() == 1


def test_save_assistant_message(db_session):
    user = _user()

    save_assistant_message(user.id, "olá")

    row = db_session.query(Message).one()
    assert (row.role, row.content, row.external_id) == ("assistant", "olá", None)


def test_message_exists(db_session):
    user = _user()

    assert message_exists("evolution_M1") is False
    save_user_message(_user_message(user.id))
    assert message_exists("evolution_M1") is True


def test_message_exists_none_is_false(db_session):
    assert message_exists(None) is False


def test_history_returns_message_schemas_in_order(db_session):
    user = _user()
    _exchange(user.id, "evolution_M1", "primeira", "r1")
    _exchange(user.id, "evolution_M2", "segunda", "r2")

    history = get_message_history(user.id)

    assert all(isinstance(m, MessageSchema) for m in history)
    assert [m.content for m in history] == ["primeira", "r1", "segunda", "r2"]
    assert [m.role for m in history] == ["user", "assistant", "user", "assistant"]


def test_history_respects_limit(db_session):
    user = _user()
    for i in range(3):
        _exchange(user.id, f"evolution_M{i}", f"msg{i}", f"r{i}")

    history = get_message_history(user.id, limit=2)

    assert [m.content for m in history] == ["msg2", "r2"]


def test_history_is_isolated_per_user(db_session):
    user = _user("5511900000000")
    other = _user("5511911111111")
    _exchange(user.id, "evolution_M1", "oi", "olá")

    assert get_message_history(other.id) == []


def test_timestamp_to_datetime():
    assert timestamp_to_datetime(None) is None

    converted = timestamp_to_datetime(1710000000)
    assert converted.tzinfo == TIMEZONE

    now = datetime.now(TIMEZONE)
    assert timestamp_to_datetime(now) is now

from database.conversations import (
    get_message_history,
    message_exists,
    save_exchange,
)
from database.models import Message, User


def _msg(**o):
    base = {
        "number": "5511999999999",
        "push_name": "Fulano",
        "content": "oi",
        "message_type": "conversation",
        "message_id": "M1",
        "timestamp": None,
    }
    base.update(o)
    return base


def test_save_exchange_is_atomic(db_session):
    assert save_exchange(_msg(), "olá") is True
    assert save_exchange(_msg(), "olá de novo") is False  # mesmo message_id

    roles = [m.role for m in db_session.query(Message).order_by(Message.id)]
    assert roles == ["user", "assistant"]  # a segunda tentativa não deixou lixo


def test_save_exchange_creates_user(db_session):
    save_exchange(_msg(number="5511977777777", push_name="Novo"), "olá")

    user = db_session.query(User).filter_by(number="5511977777777").one()
    assert user.name == "Novo"


def test_message_exists(db_session):
    assert message_exists("M1") is False
    save_exchange(_msg(), "olá")
    assert message_exists("M1") is True


def test_message_exists_none_is_false(db_session):
    assert message_exists(None) is False


def test_history_follows_insertion_order(db_session):
    save_exchange(_msg(message_id="M1", content="primeira"), "r1")
    save_exchange(_msg(message_id="M2", content="segunda"), "r2")

    user = db_session.query(User).one()
    history = get_message_history(user.id)

    assert [m["content"] for m in history] == ["primeira", "r1", "segunda", "r2"]


def test_history_respects_limit(db_session):
    for i in range(3):
        save_exchange(_msg(message_id=f"M{i}", content=f"msg{i}"), f"r{i}")

    user = db_session.query(User).one()
    history = get_message_history(user.id, limit=2)

    assert [m["content"] for m in history] == ["msg2", "r2"]


def test_empty_history(db_session):
    save_exchange(_msg(number="5511900000000"), "olá")
    other = db_session.query(User).filter_by(number="5511900000000").one()
    db_session.query(Message).delete()
    db_session.commit()

    assert get_message_history(other.id) == []

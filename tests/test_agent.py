import pytest
from redis.exceptions import RedisError

import agent.processor as proc
from agent.processor import (
    ERROR_MESSAGE,
    enqueue_message,
    process_conversation,
    respond_to_user,
)
from app.schemas.message import MessageReceived
from database.models import Message
from database.users import get_or_create_user


def _msg(**overrides):
    base = {
        "external_id": "evolution_MSG1",
        "number": "5511999999999",
        "name": "Fulano",
        "content": "Olá, tudo bem?",
        "content_type": "text",
        "timestamp": None,
    }
    base.update(overrides)
    return MessageReceived(**base)


@pytest.fixture
def ai(monkeypatch):
    """Substitui a IA e registra o histórico recebido."""
    received = []

    def fake(history):
        received.append(list(history))
        return "resposta da IA"

    monkeypatch.setattr(proc, "generate_response", fake)
    return received


def _roles(db_session):
    return [m.role for m in db_session.query(Message).order_by(Message.id)]


def test_success_sends_and_saves_both(db_session, ai):
    sent = []

    result = process_conversation(_msg(), sent.append)

    assert result == {"status": "processed", "response": "resposta da IA"}
    assert sent == ["resposta da IA"]
    assert _roles(db_session) == ["user", "assistant"]


def test_ai_receives_current_message(db_session, ai):
    process_conversation(_msg(content="oi"), lambda t: None)

    last = ai[0][-1]
    assert (last.role, last.content) == ("user", "oi")


def test_history_includes_previous_exchange(db_session, ai):
    process_conversation(
        _msg(external_id="evolution_M1", content="primeira"), lambda t: None
    )
    process_conversation(
        _msg(external_id="evolution_M2", content="segunda"), lambda t: None
    )

    assert [m.content for m in ai[1]] == ["primeira", "resposta da IA", "segunda"]


def test_ai_failure_sends_fallback_and_does_not_retry(db_session, monkeypatch):
    def boom(history):
        raise ConnectionError()

    monkeypatch.setattr(proc, "generate_response", boom)
    sent = []

    result = process_conversation(_msg(), sent.append)

    # fallback entregue: repetir duplicaria a mensagem
    assert result == {"status": "failed", "response": ERROR_MESSAGE, "retry": False}
    assert sent == [ERROR_MESSAGE]
    # a mensagem do usuário já foi gravada; a resposta não
    assert _roles(db_session) == ["user"]


def test_ai_and_fallback_failure_asks_for_retry(db_session, monkeypatch):
    def boom(history):
        raise ConnectionError()

    def send_fails(text):
        raise ConnectionError()

    monkeypatch.setattr(proc, "generate_response", boom)

    result = process_conversation(_msg(), send_fails)

    # o usuário não recebeu nada: seguro repetir
    assert result == {"status": "failed", "response": ERROR_MESSAGE, "retry": True}


def test_send_failure_asks_for_retry_and_retry_delivers(db_session, ai):
    sent, attempts = [], {"n": 0}

    def flaky_send(text):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ConnectionError()
        sent.append(text)

    result = process_conversation(_msg(), flaky_send)

    assert result == {"status": "failed", "response": "resposta da IA", "retry": True}
    assert _roles(db_session) == ["user"]

    # o webhook reenviado é duplicado; o retry real vem do worker
    assert process_conversation(_msg(), flaky_send)["status"] == "duplicate"

    user = get_or_create_user("5511999999999", "Fulano")
    assert respond_to_user(user, flaky_send)["status"] == "processed"
    assert sent == ["resposta da IA"]
    assert _roles(db_session) == ["user", "assistant"]


def test_save_failure_does_not_retry(db_session, ai, monkeypatch):
    def boom(user_id, response):
        raise RuntimeError()

    monkeypatch.setattr(proc, "save_assistant_message", boom)
    sent = []

    result = process_conversation(_msg(), sent.append)

    assert result == {"status": "failed", "response": "resposta da IA", "retry": False}
    assert sent == ["resposta da IA"]  # já entregue: não pode ser repetida


def test_duplicate_is_not_answered_again(db_session, ai):
    sent = []

    first = process_conversation(_msg(), sent.append)
    second = process_conversation(_msg(), sent.append)

    assert first["status"] == "processed"
    assert second == {"status": "duplicate", "response": None}
    assert sent == ["resposta da IA"]
    assert len(ai) == 1


def test_enqueue_schedules_debounce_without_calling_ai(db_session, ai, monkeypatch):
    scheduled = []
    monkeypatch.setattr(proc.debounce, "schedule", scheduled.append)

    result = enqueue_message(_msg())

    assert result == {"status": "queued", "response": None}
    assert len(scheduled) == 1
    assert ai == []
    assert _roles(db_session) == ["user"]


def test_enqueue_duplicate_does_not_schedule(db_session, ai, monkeypatch):
    scheduled = []
    monkeypatch.setattr(proc.debounce, "schedule", scheduled.append)

    enqueue_message(_msg())
    result = enqueue_message(_msg())

    assert result["status"] == "duplicate"
    assert len(scheduled) == 1


def test_enqueue_falls_back_to_direct_reply_when_redis_is_down(
    db_session, ai, monkeypatch
):
    def boom(user_id):
        raise RedisError()

    monkeypatch.setattr(proc.debounce, "schedule", boom)
    sent = []

    result = enqueue_message(_msg(), sent.append)

    assert result["status"] == "processed"
    assert sent == ["resposta da IA"]
    assert _roles(db_session) == ["user", "assistant"]

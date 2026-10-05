import pytest

import agent.processor as proc
from agent.processor import ERROR_MESSAGE, process_conversation
from database.models import Message


def _msg(**overrides):
    base = {
        "number": "5511999999999",
        "push_name": "Fulano",
        "from_me": False,
        "content": "Olá, tudo bem?",
        "message_type": "conversation",
        "message_id": "MSG1",
        "timestamp": None,
    }
    base.update(overrides)
    return base


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

    assert process_conversation(_msg(), send=sent.append) == "processed"

    assert sent == ["resposta da IA"]
    assert _roles(db_session) == ["user", "assistant"]


def test_ai_receives_current_message(db_session, ai):
    process_conversation(_msg(content="oi"), send=lambda t: None)

    assert ai[0][-1] == {"role": "user", "content": "oi"}


def test_history_includes_previous_exchange(db_session, ai):
    process_conversation(_msg(message_id="M1", content="primeira"), send=lambda t: None)
    process_conversation(_msg(message_id="M2", content="segunda"), send=lambda t: None)

    assert [m["content"] for m in ai[1]] == ["primeira", "resposta da IA", "segunda"]


def test_ai_failure_sends_fallback_and_saves_nothing(db_session, monkeypatch):
    def boom(history):
        raise ConnectionError()

    monkeypatch.setattr(proc, "generate_response", boom)
    sent = []

    assert process_conversation(_msg(), send=sent.append) == "failed"

    assert sent == [ERROR_MESSAGE]
    assert db_session.query(Message).count() == 0


def test_send_failure_saves_nothing_and_retry_delivers(db_session, ai):
    sent, attempts = [], {"n": 0}

    def flaky_send(text):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ConnectionError()
        sent.append(text)

    with pytest.raises(ConnectionError):
        process_conversation(_msg(), send=flaky_send)

    assert db_session.query(Message).count() == 0

    assert process_conversation(_msg(), send=flaky_send) == "processed"

    assert sent == ["resposta da IA"]
    assert _roles(db_session) == ["user", "assistant"]


def test_duplicate_is_not_answered_again(db_session, ai):
    sent = []

    process_conversation(_msg(), send=sent.append)
    status = process_conversation(_msg(), send=sent.append)

    assert status == "duplicate"
    assert sent == ["resposta da IA"]
    assert len(ai) == 1

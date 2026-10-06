import pytest

import agent.processor as proc
from agent.processor import ERROR_MESSAGE, process_conversation
from app.schemas.message import MessageReceived
from database.models import Message


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

    assert process_conversation(_msg(), sent.append) == "processed"

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


def test_ai_failure_sends_fallback_and_saves_nothing(db_session, monkeypatch):
    def boom(history):
        raise ConnectionError()

    monkeypatch.setattr(proc, "generate_response", boom)
    sent = []

    assert process_conversation(_msg(), sent.append) == "failed"

    assert sent == [ERROR_MESSAGE]
    assert db_session.query(Message).count() == 0


def test_send_failure_saves_nothing_and_retry_delivers(db_session, ai):
    sent, attempts = [], {"n": 0}

    def flaky_send(text):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ConnectionError()
        sent.append(text)

    assert process_conversation(_msg(), flaky_send) == "failed"
    assert db_session.query(Message).count() == 0

    assert process_conversation(_msg(), flaky_send) == "processed"

    assert sent == ["resposta da IA"]
    assert _roles(db_session) == ["user", "assistant"]


def test_duplicate_is_not_answered_again(db_session, ai):
    sent = []

    process_conversation(_msg(), sent.append)
    status = process_conversation(_msg(), sent.append)

    assert status == "duplicate"
    assert sent == ["resposta da IA"]
    assert len(ai) == 1

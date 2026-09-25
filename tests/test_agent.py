import pytest

import services.agent as agent_module
from services.agent import process_conversation


@pytest.fixture
def mock_dependencies(monkeypatch):
    """Mocka dependências externas e registra chamadas."""
    calls = []

    def fake_get_or_create_user(number, name):
        calls.append(("get_or_create_user", {"number": number, "name": name}))
        return 42

    def fake_ensure_history(user_id):
        calls.append(("ensure_history", {"user_id": user_id}))

    def fake_save_message(**kwargs):
        calls.append(("save_message", kwargs))

    def fake_get_openai_history(user_id):
        calls.append(("get_openai_history", {"user_id": user_id}))
        return [
            {
                "role": "user",
                "content": "[01/01/2024 10:00] oi",
            }
        ]

    def fake_generate_response(history):
        calls.append(("generate_response", {"history": history}))
        return "resposta gerada pela IA"

    monkeypatch.setattr(
        agent_module,
        "get_or_create_user",
        fake_get_or_create_user,
    )
    monkeypatch.setattr(
        agent_module,
        "ensure_history",
        fake_ensure_history,
    )
    monkeypatch.setattr(
        agent_module,
        "save_message",
        fake_save_message,
    )
    monkeypatch.setattr(
        agent_module,
        "get_openai_history",
        fake_get_openai_history,
    )
    monkeypatch.setattr(
        agent_module.openai_service,
        "generate_response",
        fake_generate_response,
    )

    return calls


def _msg(**overrides):
    """Cria mensagem padrão de teste."""
    base = {
        "number": "5511999999999",
        "push_name": "Fulano",
        "from_me": False,
        "content": "Olá, tudo bem?",
        "message_type": "chat",
        "message_id": "MSG1",
        "timestamp": None,
    }

    base.update(overrides)

    return base


# Fluxo normal


def test_process_flow_order(mock_dependencies):
    """Valida ordem do processamento."""
    process_conversation(_msg())

    steps = [call[0] for call in mock_dependencies]

    assert steps == [
        "get_or_create_user",
        "ensure_history",
        "save_message",
        "get_openai_history",
        "generate_response",
        "save_message",
    ]


def test_returns_ai_response(mock_dependencies):
    """Retorna resposta da IA."""
    result = process_conversation(_msg())

    assert result == "resposta gerada pela IA"


def test_creates_user_with_data(mock_dependencies):
    """Cria usuário com dados recebidos."""
    process_conversation(
        _msg(
            number="5511988888888",
            push_name="Ciclana",
        )
    )

    call = next(c for c in mock_dependencies if c[0] == "get_or_create_user")

    assert call[1] == {
        "number": "5511988888888",
        "name": "Ciclana",
    }


def test_saves_user_message(mock_dependencies):
    """Salva mensagem recebida."""
    msg = _msg()

    process_conversation(msg)

    call = [c for c in mock_dependencies if c[0] == "save_message"][0]

    assert call[1] == msg


def test_saves_ai_message(mock_dependencies):
    """Salva resposta da IA."""
    process_conversation(
        _msg(
            number="5511977777777",
            push_name="Beltrano",
        )
    )

    calls = [c for c in mock_dependencies if c[0] == "save_message"]

    reply = calls[1][1]

    assert reply["number"] == "5511977777777"
    assert reply["push_name"] == "Beltrano"
    assert reply["from_me"] is True
    assert reply["content"] == "resposta gerada pela IA"


def test_sends_history_to_ai(mock_dependencies):
    """Envia histórico salvo para IA."""
    process_conversation(_msg())

    call = next(c for c in mock_dependencies if c[0] == "generate_response")

    assert call[1]["history"] == [
        {
            "role": "user",
            "content": "[01/01/2024 10:00] oi",
        }
    ]


# Falha da IA


def test_ai_error_returns_fallback(mock_dependencies, monkeypatch):
    """Retorna fallback quando IA falha."""

    def raise_error(history):
        raise ConnectionError()

    monkeypatch.setattr(
        agent_module.openai_service,
        "generate_response",
        raise_error,
    )

    result = process_conversation(_msg())

    assert result == (
        "Desculpe, não consegui processar sua mensagem agora. "
        "Tente novamente em instantes."
    )


def test_ai_error_saves_fallback(mock_dependencies, monkeypatch):
    """Salva fallback como resposta."""

    def raise_error(history):
        raise TimeoutError()

    monkeypatch.setattr(
        agent_module.openai_service,
        "generate_response",
        raise_error,
    )

    process_conversation(_msg())

    calls = [c for c in mock_dependencies if c[0] == "save_message"]

    assert calls[1][1]["from_me"] is True
    assert "Desculpe" in calls[1][1]["content"]


def test_user_message_saved_before_ai(mock_dependencies, monkeypatch):
    """Mantém mensagem salva antes da IA."""

    def raise_error(history):
        raise RuntimeError()

    monkeypatch.setattr(
        agent_module.openai_service,
        "generate_response",
        raise_error,
    )

    process_conversation(_msg())

    calls = [c for c in mock_dependencies if c[0] == "save_message"]

    assert len(calls) == 2
    assert calls[0][1]["from_me"] is False

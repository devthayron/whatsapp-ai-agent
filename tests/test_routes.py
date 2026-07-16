import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.chat as chat_module
import app.routes.webhook as webhook_module

from app.routes.chat import router as chat_router
from app.routes.webhook import router as webhook_router


@pytest.fixture
def client():
    """Cria app FastAPI para testes."""
    app = FastAPI()

    app.include_router(chat_router)
    app.include_router(webhook_router)

    return TestClient(app)


@pytest.fixture
def mock_chat_dependencies(monkeypatch):
    """Mocka dependências da rota chat."""
    calls = []

    def fake_process_conversation(message):
        calls.append(
            ("process_conversation", message)
        )
        return "resposta simulada"

    def fake_send_message(number, text):
        calls.append(
            (
                "send_message",
                {
                    "number": number,
                    "text": text,
                },
            )
        )

        return {"status": "ok"}

    monkeypatch.setattr(
        chat_module,
        "process_conversation",
        fake_process_conversation,
    )

    monkeypatch.setattr(
        chat_module.evolution_service,
        "send_message",
        fake_send_message,
    )

    return calls


@pytest.fixture
def mock_webhook_dependencies(monkeypatch):
    """Mocka dependências da rota webhook."""
    calls = []

    def fake_process_conversation(message):
        calls.append(
            ("process_conversation", message)
        )
        return "resposta simulada"

    def fake_send_message(number, text):
        calls.append(
            (
                "send_message",
                {
                    "number": number,
                    "text": text,
                },
            )
        )

        return {"status": "ok"}

    monkeypatch.setattr(
        webhook_module,
        "process_conversation",
        fake_process_conversation,
    )

    monkeypatch.setattr(
        webhook_module.evolution_service,
        "send_message",
        fake_send_message,
    )

    return calls


# Chat


def test_chat_returns_response(client, mock_chat_dependencies):
    """Retorna resposta da IA."""
    response = client.post(
        "/chat/",
        json={
            "number": "5511999999999",
            "content": "Oi",
            "push_name": "Fulano",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "resposta simulada"
    }


def test_chat_builds_message(client, mock_chat_dependencies):
    """Monta mensagem corretamente."""
    client.post(
        "/chat/",
        json={
            "number": "5511999999999",
            "content": "Oi",
            "push_name": "Fulano",
        },
    )

    call = next(
        c for c in mock_chat_dependencies
        if c[0] == "process_conversation"
    )

    assert call[1] == {
        "number": "5511999999999",
        "push_name": "Fulano",
        "from_me": False,
        "content": "Oi",
        "message_type": "chat",
        "message_id": None,
        "timestamp": None,
    }


def test_chat_sends_message(client, mock_chat_dependencies):
    """Envia resposta pelo WhatsApp."""
    client.post(
        "/chat/",
        json={
            "number": "5511999999999",
            "content": "Oi",
        },
    )

    call = next(
        c for c in mock_chat_dependencies
        if c[0] == "send_message"
    )

    assert call[1] == {
        "number": "5511999999999",
        "text": "resposta simulada",
    }


def test_chat_without_name(client, mock_chat_dependencies):
    """Aceita nome ausente."""
    response = client.post(
        "/chat/",
        json={
            "number": "5511999999999",
            "content": "Oi",
        },
    )

    assert response.status_code == 200

    call = next(
        c for c in mock_chat_dependencies
        if c[0] == "process_conversation"
    )

    assert call[1]["push_name"] is None


def test_chat_missing_content(client, mock_chat_dependencies):
    """Valida campo obrigatório."""
    response = client.post(
        "/chat/",
        json={
            "number": "5511999999999",
        },
    )

    assert response.status_code == 422

    assert not any(
        c[0] == "process_conversation"
        for c in mock_chat_dependencies
    )


# Webhook


def _payload(
    remote_jid="5511999999999@s.whatsapp.net",
    from_me=False,
    content="Oi",
):
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "id": "MSG1",
                "fromMe": from_me,
                "remoteJid": remote_jid,
            },
            "messageTimestamp": 1710000000,
            "pushName": "Fulano",
            "messageType": "conversation",
            "message": {
                "conversation": content
            },
        },
    }


def test_webhook_ignores_event(client, mock_webhook_dependencies):
    """Ignora eventos inválidos."""
    response = client.post(
        "/webhook/",
        json={
            "event": "connection.update",
            "data": {},
        },
    )

    assert response.json() == {
        "status": "ignored"
    }

    assert mock_webhook_dependencies == []


def test_webhook_ignores_group(client, mock_webhook_dependencies):
    """Ignora mensagens de grupo."""
    response = client.post(
        "/webhook/",
        json=_payload(
            remote_jid="123456789@g.us"
        ),
    )

    assert response.json() == {
        "status": "ignored"
    }

    assert mock_webhook_dependencies == []


def test_webhook_processes_message(client, mock_webhook_dependencies):
    """Processa mensagem válida."""
    response = client.post(
        "/webhook/",
        json=_payload(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "processed"
    }

    process = next(
        c for c in mock_webhook_dependencies
        if c[0] == "process_conversation"
    )

    assert process[1]["number"] == "5511999999999"
    assert process[1]["content"] == "Oi"

    send = next(
        c for c in mock_webhook_dependencies
        if c[0] == "send_message"
    )

    assert send[1] == {
        "number": "5511999999999",
        "text": "resposta simulada",
    }


def test_webhook_ignores_bot_message(client, mock_webhook_dependencies):
    """Ignora mensagens próprias."""
    response = client.post(
        "/webhook/",
        json=_payload(from_me=True),
    )

    assert response.json() == {
        "status": "ignored"
    }

    assert mock_webhook_dependencies == []


def test_webhook_ignores_invalid_message(
    client,
    mock_webhook_dependencies,
    monkeypatch,
):
    """Ignora mensagem não normalizada."""

    monkeypatch.setattr(
        webhook_module,
        "normalize_message",
        lambda x: None,
    )

    response = client.post(
        "/webhook/",
        json=_payload(),
    )

    assert response.json() == {
        "status": "ignored"
    }

    assert mock_webhook_dependencies == []


def test_chat_evolution_error(
    client,
    mock_chat_dependencies,
    monkeypatch,
):
    """Propaga erro do envio."""

    def error(number, text):
        raise Exception("Evolution offline")

    monkeypatch.setattr(
        chat_module.evolution_service,
        "send_message",
        error,
    )

    response = client.post(
        "/chat/",
        json={
            "number": "5511999999999",
            "content": "Oi",
        },
    )

    assert response.status_code == 200
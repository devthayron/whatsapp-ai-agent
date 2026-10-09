import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.chat as chat_module
import app.routes.webhook_evolution as webhook_module
from app.routes.chat import router as chat_router
from app.routes.webhook_evolution import router as webhook_router
from app.schemas.message import MessageReceived
from config import settings
from database.models import Account
from dependencies import verify_token


def _build_app(authenticated: bool) -> TestClient:
    api = FastAPI()
    api.include_router(chat_router)
    api.include_router(webhook_router)

    if authenticated:
        api.dependency_overrides[verify_token] = lambda: Account(
            id=1, email="teste@teste.com", is_active=True
        )

    return TestClient(api)


@pytest.fixture
def client():
    return _build_app(authenticated=True)


@pytest.fixture
def anonymous_client():
    return _build_app(authenticated=False)


@pytest.fixture
def webhook_headers():
    return {"X-Webhook-Secret": settings.WEBHOOK_SECRET}


@pytest.fixture
def mock_chat_dependencies(monkeypatch):
    calls = []

    def fake_process_conversation(message, send_msg=None):
        calls.append(("process_conversation", message))
        return {"status": "processed", "response": "resposta simulada"}

    monkeypatch.setattr(chat_module, "process_conversation", fake_process_conversation)
    return calls


@pytest.fixture
def mock_webhook_dependencies(monkeypatch):
    calls = []

    def fake_enqueue_message(message, send_msg=None):
        calls.append(("enqueue_message", message))
        send_msg("resposta simulada")
        return {"status": "queued", "response": None}

    def fake_send_message(number, text):
        calls.append(("send_message", {"number": number, "text": text}))
        return {"status": "ok"}

    monkeypatch.setattr(webhook_module, "enqueue_message", fake_enqueue_message)
    monkeypatch.setattr(
        webhook_module.evolution_service, "send_message", fake_send_message
    )
    return calls


# Chat

CHAT_BODY = {"number": "5511999999999", "content": "Oi", "name": "Fulano"}


def test_chat_requires_authentication(anonymous_client, mock_chat_dependencies):
    response = anonymous_client.post("/chat/", json=CHAT_BODY)

    assert response.status_code == 401
    assert mock_chat_dependencies == []


def test_chat_returns_response(client, mock_chat_dependencies):
    response = client.post("/chat/", json=CHAT_BODY)

    assert response.status_code == 200
    assert response.json() == {"response": "resposta simulada", "status": "processed"}


def test_chat_passes_message_received(client, mock_chat_dependencies):
    client.post("/chat/", json=CHAT_BODY)

    call = next(c for c in mock_chat_dependencies if c[0] == "process_conversation")

    assert isinstance(call[1], MessageReceived)
    assert call[1] == MessageReceived(
        number="5511999999999", name="Fulano", content="Oi", content_type="text"
    )


def test_chat_without_name(client, mock_chat_dependencies):
    response = client.post("/chat/", json={"number": "5511999999999", "content": "Oi"})

    assert response.status_code == 200
    call = next(c for c in mock_chat_dependencies if c[0] == "process_conversation")
    assert call[1].name is None


def test_chat_missing_content(client, mock_chat_dependencies):
    response = client.post("/chat/", json={"number": "5511999999999"})

    assert response.status_code == 422
    assert mock_chat_dependencies == []


# Webhook


def _payload(remote_jid="5511999999999@s.whatsapp.net", from_me=False, content="Oi"):
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"id": "MSG1", "fromMe": from_me, "remoteJid": remote_jid},
            "messageTimestamp": 1710000000,
            "pushName": "Fulano",
            "messageType": "conversation",
            "message": {"conversation": content},
        },
    }


def test_webhook_rejects_missing_secret(client, mock_webhook_dependencies):
    response = client.post("/webhook/", json=_payload())

    assert response.status_code == 401
    assert mock_webhook_dependencies == []


def test_webhook_rejects_wrong_secret(client, mock_webhook_dependencies):
    response = client.post(
        "/webhook/", json=_payload(), headers={"X-Webhook-Secret": "errado"}
    )

    assert response.status_code == 401
    assert mock_webhook_dependencies == []


def test_webhook_ignores_event(client, mock_webhook_dependencies, webhook_headers):
    response = client.post(
        "/webhook/",
        json={"event": "connection.update", "data": {}},
        headers=webhook_headers,
    )

    assert response.status_code == 200
    assert response.content == b""
    assert mock_webhook_dependencies == []


def test_webhook_ignores_group(client, mock_webhook_dependencies, webhook_headers):
    response = client.post(
        "/webhook/", json=_payload(remote_jid="123456789@g.us"), headers=webhook_headers
    )

    assert response.status_code == 200
    assert mock_webhook_dependencies == []


def test_webhook_processes_message(client, mock_webhook_dependencies, webhook_headers):
    response = client.post("/webhook/", json=_payload(), headers=webhook_headers)

    assert response.status_code == 200
    assert response.content == b""

    enqueue = next(c for c in mock_webhook_dependencies if c[0] == "enqueue_message")
    assert isinstance(enqueue[1], MessageReceived)
    assert enqueue[1].number == "5511999999999"
    assert enqueue[1].content == "Oi"
    assert enqueue[1].external_id == "evolution_MSG1"

    send = next(c for c in mock_webhook_dependencies if c[0] == "send_message")
    assert send[1] == {"number": "5511999999999", "text": "resposta simulada"}


def test_webhook_ignores_bot_message(
    client, mock_webhook_dependencies, webhook_headers
):
    response = client.post(
        "/webhook/", json=_payload(from_me=True), headers=webhook_headers
    )

    assert response.status_code == 200
    assert mock_webhook_dependencies == []


def test_webhook_ignores_invalid_message(
    client, mock_webhook_dependencies, webhook_headers, monkeypatch
):
    monkeypatch.setattr(webhook_module, "normalize_message", lambda x: None)

    response = client.post("/webhook/", json=_payload(), headers=webhook_headers)

    assert response.status_code == 200
    assert mock_webhook_dependencies == []


def test_webhook_ignores_non_text(client, mock_webhook_dependencies, webhook_headers):
    payload = _payload()
    payload["data"]["messageType"] = "audioMessage"
    payload["data"]["message"] = {}

    response = client.post("/webhook/", json=payload, headers=webhook_headers)

    assert response.status_code == 200
    assert mock_webhook_dependencies == []


def test_webhook_duplicate_does_not_send(
    client, mock_webhook_dependencies, webhook_headers, monkeypatch
):
    monkeypatch.setattr(
        webhook_module,
        "enqueue_message",
        lambda msg, send_msg=None: {"status": "duplicate", "response": None},
    )

    response = client.post("/webhook/", json=_payload(), headers=webhook_headers)

    assert response.status_code == 200
    assert not any(c[0] == "send_message" for c in mock_webhook_dependencies)


def test_webhook_returns_500_on_unexpected_error(
    client, mock_webhook_dependencies, webhook_headers, monkeypatch
):
    def boom(msg, send_msg=None):
        raise RuntimeError("falhou")

    monkeypatch.setattr(webhook_module, "enqueue_message", boom)

    response = client.post("/webhook/", json=_payload(), headers=webhook_headers)

    assert response.status_code == 500

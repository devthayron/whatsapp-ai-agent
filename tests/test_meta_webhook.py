import hashlib
import hmac
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.webhook_meta as webhook_module
from app.routes.webhook_meta import router
from config import settings


def _payload(body="Oi", msg_id="wamid.1", status_only=False):
    value = {
        "messaging_product": "whatsapp",
        "metadata": {"phone_number_id": settings.META_PHONE_NUMBER_ID},
        "contacts": [{"profile": {"name": "Fulano"}, "wa_id": "5511999999999"}],
    }

    if status_only:
        value["statuses"] = [{"id": msg_id, "status": "delivered"}]
    else:
        value["messages"] = [
            {
                "from": "5511999999999",
                "id": msg_id,
                "timestamp": "1710000000",
                "type": "text",
                "text": {"body": body},
            }
        ]

    return {
        "object": "whatsapp_business_account",
        "entry": [{"id": "WABA", "changes": [{"field": "messages", "value": value}]}],
    }


def _sign(body: bytes, secret: str | None = None) -> str:
    key = (secret or settings.META_APP_SECRET).encode()
    return "sha256=" + hmac.new(key, body, hashlib.sha256).hexdigest()


def _post(client, payload, signature="valid"):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}

    if signature == "valid":
        headers["X-Hub-Signature-256"] = _sign(body)
    elif signature:
        headers["X-Hub-Signature-256"] = signature

    return client.post("/webhook/meta", content=body, headers=headers)


@pytest.fixture
def client():
    api = FastAPI()
    api.include_router(router)
    return TestClient(api)


@pytest.fixture
def calls(monkeypatch):
    recorded = {"enqueued": [], "sent": []}

    def fake_enqueue(message, send_msg=None):
        recorded["enqueued"].append(message)
        send_msg("resposta simulada")
        return {"status": "queued", "response": None}

    monkeypatch.setattr(webhook_module, "enqueue_message", fake_enqueue)
    monkeypatch.setattr(
        webhook_module.meta_service,
        "send_message",
        lambda number, text: recorded["sent"].append((number, text)),
    )
    return recorded


# Handshake


def test_verify_returns_challenge(client):
    response = client.get(
        "/webhook/meta",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.META_VERIFY_TOKEN,
            "hub.challenge": "123456",
        },
    )

    assert response.status_code == 200
    assert response.text == "123456"


def test_verify_rejects_wrong_token(client):
    response = client.get(
        "/webhook/meta",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "errado",
            "hub.challenge": "123456",
        },
    )

    assert response.status_code == 403


def test_verify_rejects_without_params(client):
    assert client.get("/webhook/meta").status_code == 403


# Eventos


def test_rejects_missing_signature(client, calls):
    response = _post(client, _payload(), signature=None)

    assert response.status_code == 401
    assert calls["enqueued"] == []


def test_rejects_wrong_signature(client, calls):
    response = _post(client, _payload(), signature=_sign(b"{}", "outro-segredo"))

    assert response.status_code == 401
    assert calls["enqueued"] == []


def test_processes_message_and_replies_to_sender(client, calls):
    response = _post(client, _payload())

    assert response.status_code == 200
    assert len(calls["enqueued"]) == 1
    assert calls["enqueued"][0].external_id == "meta_wamid.1"
    assert calls["sent"] == [("5511999999999", "resposta simulada")]


def test_ignores_status_events(client, calls):
    response = _post(client, _payload(status_only=True))

    assert response.status_code == 200
    assert calls["enqueued"] == []


def test_invalid_json_returns_400(client, calls):
    body = b"nao-e-json"
    response = client.post(
        "/webhook/meta", content=body, headers={"X-Hub-Signature-256": _sign(body)}
    )

    assert response.status_code == 400


def test_returns_500_on_unexpected_error(client, monkeypatch):
    def boom(message, send_msg=None):
        raise RuntimeError("falhou")

    monkeypatch.setattr(webhook_module, "enqueue_message", boom)

    assert _post(client, _payload()).status_code == 500

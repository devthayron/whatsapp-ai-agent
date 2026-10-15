import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.chat as chat_module
from app.routes.chat import router as chat_router
from app.schemas.message import MessageReceived
from database.models import Account
from dependencies import verify_token


def _build_app(authenticated: bool) -> TestClient:
    api = FastAPI()
    api.include_router(chat_router)

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
def mock_chat_dependencies(monkeypatch):
    calls = []

    def fake_process_conversation(message, send_msg=None):
        calls.append(("process_conversation", message))
        return {"status": "processed", "response": "resposta simulada"}

    monkeypatch.setattr(chat_module, "process_conversation", fake_process_conversation)
    return calls


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

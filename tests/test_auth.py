import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.auth import router as auth_router
from dependencies import get_session

CREDENTIALS = {"email": "maria@exemplo.com", "password": "senha-forte-123"}


@pytest.fixture
def client(db_session):
    api = FastAPI()
    api.include_router(auth_router)
    api.dependency_overrides[get_session] = lambda: db_session

    client = TestClient(api)
    client.post("/auth/register", json={"name": "Maria", **CREDENTIALS})
    return client


def test_login_sets_httponly_cookie_and_hides_refresh_token(client):
    response = client.post("/auth/login", json=CREDENTIALS)

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" not in body

    cookie = response.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie
    assert "httponly" in cookie
    assert "path=/auth" in cookie


def test_refresh_uses_cookie(client):
    client.post("/auth/login", json=CREDENTIALS)

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_without_cookie_returns_401(client):
    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token ausente"


def test_refresh_rejects_access_token_in_cookie(client):
    access = client.post("/auth/login", json=CREDENTIALS).json()["access_token"]

    client.cookies.clear()
    client.cookies.set("refresh_token", access)

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Tipo de token inválido"


def test_logout_clears_cookie(client):
    client.post("/auth/login", json=CREDENTIALS)

    assert client.post("/auth/logout").status_code == 200

    response = client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token ausente"


def test_me_requires_access_token(client):
    assert client.get("/auth/me").status_code == 401

    access = client.post("/auth/login", json=CREDENTIALS).json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})

    assert response.status_code == 200
    assert response.json()["email"] == CREDENTIALS["email"]

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.auth import router as auth_router
from database.models import Account
from dependencies import get_session, password_hasher

CREDENTIALS = {"email": "maria@exemplo.com", "password": "senha-forte-123"}


@pytest.fixture
def client(db_session):
    api = FastAPI()
    api.include_router(auth_router)
    api.dependency_overrides[get_session] = lambda: db_session

    # O cadastro exige login: a primeira conta nasce direto no banco
    db_session.add(
        Account(
            name="Maria",
            email=CREDENTIALS["email"],
            hashed_password=password_hasher.hash(CREDENTIALS["password"]),
        )
    )
    db_session.commit()

    return TestClient(api)


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


def test_register_requires_authentication(client):
    body = {"email": "novo@exemplo.com", "password": "outra-senha-forte"}

    assert client.post("/auth/register", json=body).status_code == 401

    access = client.post("/auth/login", json=CREDENTIALS).json()["access_token"]
    response = client.post(
        "/auth/register", json=body, headers={"Authorization": f"Bearer {access}"}
    )

    assert response.status_code == 200


def test_register_rejects_short_password(client):
    access = client.post("/auth/login", json=CREDENTIALS).json()["access_token"]

    response = client.post(
        "/auth/register",
        json={"email": "novo@exemplo.com", "password": "curta"},
        headers={"Authorization": f"Bearer {access}"},
    )

    assert response.status_code == 422

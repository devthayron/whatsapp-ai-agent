import os

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("META_ACCESS_TOKEN", "test-meta-token")
os.environ.setdefault("META_PHONE_NUMBER_ID", "100000000000001")
os.environ.setdefault("META_APP_SECRET", "test-meta-app-secret")
os.environ.setdefault("META_VERIFY_TOKEN", "test-meta-verify-token")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes")
# Forçado: os testes nunca podem apontar para o Postgres real
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.models  # noqa: F401  (registra as tabelas no Base)
from database.base import Base


@pytest.fixture
def db_session(monkeypatch):
    """SQLite em memória, isolado por teste."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # garante a mesma conexão (e o mesmo banco)
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    monkeypatch.setattr("database.users.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("database.conversations.SessionLocal", TestingSessionLocal)
    # get_session (autenticação e rotas) também usa o banco de teste
    monkeypatch.setattr("dependencies.SessionLocal", TestingSessionLocal)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

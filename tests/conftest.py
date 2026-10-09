import os

os.environ.setdefault("API_KEY_EVO", "test-key")
os.environ.setdefault("BASE_URL", "http://evolution-test.local")
os.environ.setdefault("INSTANCE", "test-instance")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("WEBHOOK_URL", "http://localhost/webhook/")
os.environ.setdefault("WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
# Forçado: os testes nunca podem apontar para o Postgres real
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.models  # noqa: F401  (registra as tabelas no Base)
from database.connection import Base


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

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

import os

# config.py exige essas variáveis para não lançar RuntimeError no import.
# Como database.conversations importa services.evolution -> config no topo
# do módulo, precisamos garantir valores dummy antes de qualquer import
# de módulo da aplicação nos testes (não afeta o comportamento testado,
# pois HTTP real é sempre mockado).
os.environ.setdefault("API_KEY_EVO", "test-key")
os.environ.setdefault("BASE_URL", "http://evolution-test.local")
os.environ.setdefault("INSTANCE", "test-instance")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base


@pytest.fixture
def db_session(monkeypatch):
    """
    Cria um banco SQLite em memória isolado por teste, cria as tabelas
    e substitui o SessionLocal usado pelos módulos de banco para que
    nenhum teste toque no arquivo data/conversations.db real.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    monkeypatch.setattr("database.users.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("database.conversations.SessionLocal", TestingSessionLocal)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
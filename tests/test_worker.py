import asyncio

import pytest
from redis.exceptions import RedisError

from app import worker
from app.schemas.user import UserSchema

USER = UserSchema(id=1, number="5511999999999")


@pytest.fixture
def calls(monkeypatch):
    calls = []

    async def ack(user_id, lease):
        calls.append("ack")

    async def retry(user_id, lease):
        calls.append("retry")
        return 1

    monkeypatch.setattr(worker.debounce, "ack", ack)
    monkeypatch.setattr(worker.debounce, "retry", retry)
    monkeypatch.setattr(worker, "get_user_by_id", lambda uid: USER)
    return calls


@pytest.mark.parametrize(
    "result, expected",
    [
        ({"status": "processed", "response": "ok"}, "ack"),
        ({"status": "failed", "response": "x", "retry": False}, "ack"),
        ({"status": "failed", "response": "x", "retry": True}, "retry"),
    ],
)
def test_process_decides_between_ack_and_retry(calls, monkeypatch, result, expected):
    monkeypatch.setattr(worker, "respond_to_user", lambda user, send: result)

    asyncio.run(worker._process(1, 123.0))

    assert calls == [expected]


def test_process_unexpected_error_retries(calls, monkeypatch):
    def boom(user, send):
        raise RuntimeError()

    monkeypatch.setattr(worker, "respond_to_user", boom)

    asyncio.run(worker._process(1, 123.0))

    assert calls == ["retry"]


def test_process_unknown_user_acks(calls, monkeypatch):
    monkeypatch.setattr(worker, "get_user_by_id", lambda uid: None)

    asyncio.run(worker._process(1, 123.0))

    assert calls == ["ack"]


def test_process_redis_error_on_ack_is_swallowed(monkeypatch):
    async def ack(user_id, lease):
        raise RedisError()

    monkeypatch.setattr(worker.debounce, "ack", ack)
    monkeypatch.setattr(worker, "get_user_by_id", lambda uid: USER)
    monkeypatch.setattr(
        worker, "respond_to_user", lambda user, send: {"status": "processed"}
    )

    asyncio.run(worker._process(1, 123.0))  # não deve levantar

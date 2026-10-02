from datetime import datetime
from zoneinfo import ZoneInfo

import integrations.evolution.history as evolution_history_module
from database.conversations import (
    TIMEZONE,
    add_message,
    get_message_history,
    import_history,
    save_message,
    timestamp_to_datetime,
)
from database.models import Message, User
from database.users import _get_or_create_user
from integrations.evolution.history import ensure_history, get_history


# A criação de usuários possui testes próprios em test_users.py.
def _create_user(db_session, number="5511999999999", name="Fulano"):
    user = _get_or_create_user(db_session, number, name)
    db_session.commit()
    return user


def test_add_message_inserts_new_message(db_session):
    """
    Adiciona uma nova mensagem quando o message_id é único.
    """
    user = _create_user(db_session)

    add_message(
        session=db_session,
        user=user,
        message_id="MSG1",
        role="user",
        content="oi",
        message_type="conversation",
        sent_at=datetime.now(TIMEZONE),
    )
    db_session.commit()

    saved = db_session.query(Message).filter_by(message_id="MSG1").one()

    assert saved.content == "oi"
    assert saved.user_id == user.id


def test_add_message_ignores_duplicate(db_session):
    """
    Ignora mensagens que possuem o mesmo message_id.
    """
    user = _create_user(db_session)

    for content in ["primeira", "segunda (duplicada)"]:
        add_message(
            session=db_session,
            user=user,
            message_id="MSG-DUP",
            role="user",
            content=content,
            message_type="conversation",
            sent_at=datetime.now(TIMEZONE),
        )
        db_session.commit()

    count = db_session.query(Message).filter_by(message_id="MSG-DUP").count()

    assert count == 1

    saved = db_session.query(Message).filter_by(message_id="MSG-DUP").one()

    assert saved.content == "primeira"


def test_timestamp_to_datetime():
    """
    Converte timestamp Unix para datetime com timezone.
    """
    result = timestamp_to_datetime(1710000000)

    assert isinstance(result, datetime)
    assert result.tzinfo is not None

    assert result == datetime.fromtimestamp(
        1710000000,
        tz=ZoneInfo("America/Sao_Paulo"),
    )


def test_timestamp_keeps_datetime():
    """
    Mantém datetime existente sem modificar.
    """
    now = datetime.now(TIMEZONE)

    assert timestamp_to_datetime(now) is now


def test_save_message_creates_user(db_session):
    """
    Cria usuário automaticamente ao salvar mensagem.
    """
    save_message(
        number="5511977777777",
        push_name="Novo Contato",
        from_me=False,
        content="primeira mensagem",
        message_id="MSG-NEW-USER",
    )

    user = db_session.query(User).filter_by(number="5511977777777").one()

    assert user.name == "Novo Contato"

    message = db_session.query(Message).filter_by(message_id="MSG-NEW-USER").one()

    assert message.role == "user"
    assert message.content == "primeira mensagem"


def test_save_message_default_timestamp(db_session):
    """
    Gera data automaticamente quando timestamp não é informado.
    """
    save_message(
        number="5511988888888",
        push_name="Contato",
        from_me=False,
        content="mensagem sem timestamp",
        message_id="MSG-NO-TIMESTAMP",
    )

    message = db_session.query(Message).filter_by(message_id="MSG-NO-TIMESTAMP").one()

    assert message.sent_at is not None


def test_save_message_bot_role(db_session):
    """
    Define role assistant para mensagens enviadas pelo bot.
    """
    save_message(
        number="5511977777777",
        push_name="Novo Contato",
        from_me=True,
        content="resposta do bot",
        message_id="MSG-BOT-REPLY",
    )

    message = db_session.query(Message).filter_by(message_id="MSG-BOT-REPLY").one()

    assert message.role == "assistant"


def test_save_message_generates_id(db_session):
    """
    Gera identificador quando message_id não é informado.
    """
    save_message(
        number="5511966666666",
        push_name="Alguém",
        from_me=True,
        content="resposta sem id externo",
    )

    message = (
        db_session.query(Message).filter_by(content="resposta sem id externo").one()
    )

    assert message.message_id is not None
    assert message.message_id != ""


def test_history_order(db_session):
    """
    Retorna mensagens na ordem real (cronológica) da conversa.
    """
    user = _create_user(db_session)

    add_message(
        session=db_session,
        user=user,
        message_id="M2",
        role="user",
        content="segunda",
        message_type="conversation",
        sent_at=datetime(
            2024,
            1,
            2,
            tzinfo=TIMEZONE,
        ),
    )

    add_message(
        session=db_session,
        user=user,
        message_id="M1",
        role="user",
        content="primeira",
        message_type="conversation",
        sent_at=datetime(
            2024,
            1,
            1,
            tzinfo=TIMEZONE,
        ),
    )

    db_session.commit()

    history = get_message_history(user.id)

    assert [message["content"].split("] ")[1] for message in history] == [
        "primeira",
        "segunda",
    ]


def test_get_message_history_respects_limit(db_session):
    """
    Retorna apenas a quantidade limite de mensagens.
    """
    user = _create_user(db_session)

    for i in range(5):
        add_message(
            session=db_session,
            user=user,
            message_id=f"M{i}",
            role="user",
            content=f"msg{i}",
            message_type="conversation",
            sent_at=datetime(
                2024,
                1,
                i + 1,
                tzinfo=TIMEZONE,
            ),
        )

    db_session.commit()

    history = get_message_history(
        user.id,
        limit=2,
    )

    assert len(history) == 2

    assert [message["content"].split("] ")[1] for message in history] == [
        "msg3",
        "msg4",
    ]


def test_empty_history(db_session):
    """
    Retorna lista vazia quando usuário não possui histórico.
    """
    user = _create_user(db_session)

    history = get_message_history(user.id)

    assert history == []


def test_history_timestamp_format(db_session):
    """
    Adiciona timestamp no conteúdo do histórico.
    """
    user = _create_user(db_session)

    add_message(
        session=db_session,
        user=user,
        message_id="M1",
        role="user",
        content="oi",
        message_type="conversation",
        sent_at=datetime(
            2024,
            3,
            5,
            14,
            30,
            tzinfo=TIMEZONE,
        ),
    )

    db_session.commit()

    history = get_message_history(user.id)

    assert history[0]["content"] == "[05/03/2024 14:30] oi"
    assert history[0]["role"] == "user"


def test_ensure_history_imports_new_user(db_session, monkeypatch):
    """
    Importa histórico quando usuário ainda não foi sincronizado.
    """
    user = _create_user(db_session)

    assert user.history_imported is False

    monkeypatch.setattr(
        evolution_history_module,
        "get_history",
        lambda number: [],
    )

    imported = {"value": False}

    def fake_import_history(user_id, messages):
        imported["value"] = True

        assert user_id == user.id
        assert messages == []

    monkeypatch.setattr(
        evolution_history_module,
        "import_history",
        fake_import_history,
    )

    ensure_history(user.id)

    assert imported["value"] is True


def test_ensure_history_skips_existing_history(db_session, monkeypatch):
    """
    Não busca nem importa histórico quando ele já foi sincronizado.
    """
    user = _create_user(db_session)

    user.history_imported = True
    db_session.commit()

    called = {"value": False}

    def fake_get_history(number):
        called["value"] = True
        return []

    monkeypatch.setattr(
        evolution_history_module,
        "get_history",
        fake_get_history,
    )

    ensure_history(user.id)

    assert called["value"] is False


def test_get_history_ignores_invalid_messages(monkeypatch):
    """
    Ignora mensagens da Evolution API que não podem ser normalizadas.
    """
    invalid_messages = [
        {
            "key": {},
            "messageType": "conversation",
        }
    ]

    monkeypatch.setattr(
        evolution_history_module.evolution_service,
        "get_messages_by_number",
        lambda number: invalid_messages,
    )

    history = get_history("5511999999999")

    assert history == []


def test_import_history_saves_messages(db_session):
    """
    Persiste mensagens já normalizadas no banco.
    """
    user = _create_user(
        db_session,
        number="5511955555555",
    )

    messages = [
        {
            "message_id": "EVO-1",
            "from_me": False,
            "number": "5511955555555",
            "push_name": "Fulano",
            "content": "mensagem antiga do usuário",
            "message_type": "conversation",
            "timestamp": 1700000000,
        },
        {
            "message_id": "EVO-2",
            "from_me": True,
            "number": "5511955555555",
            "push_name": "Fulano",
            "content": "resposta antiga do bot",
            "message_type": "conversation",
            "timestamp": 1700000100,
        },
    ]

    import_history(user.id, messages)

    saved_messages = (
        db_session.query(Message)
        .filter_by(user_id=user.id)
        .order_by(Message.sent_at)
        .all()
    )

    assert [message.message_id for message in saved_messages] == [
        "EVO-1",
        "EVO-2",
    ]

    assert saved_messages[0].role == "user"
    assert saved_messages[1].role == "assistant"

    db_session.expire_all()

    refreshed = db_session.query(User).filter_by(id=user.id).one()

    assert refreshed.history_imported is True


def test_ensure_history_api_error(db_session, monkeypatch):
    """
    Não conclui sincronização quando a busca do histórico falha.
    """
    user = _create_user(
        db_session,
        number="5511944444444",
    )

    monkeypatch.setattr(
        evolution_history_module,
        "get_history",
        lambda number: None,
    )

    ensure_history(user.id)

    refreshed = db_session.query(User).filter_by(id=user.id).one()

    assert refreshed.history_imported is False

    assert db_session.query(Message).filter_by(user_id=user.id).count() == 0

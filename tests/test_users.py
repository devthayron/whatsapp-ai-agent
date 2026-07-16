from database.models import User
from database.users import _get_or_create_user, get_or_create_user


def test_creates_new_user_when_not_exists(db_session):
    """
    Cria um novo usuário quando o número ainda não existe.
    """
    user = _get_or_create_user(db_session, "5511999999999", "Fulano")

    assert user.id is not None
    assert user.number == "5511999999999"
    assert user.name == "Fulano"


def test_returns_existing_user_without_duplicating(db_session):
    """
    Retorna o usuário existente sem criar um novo registro.
    """
    first = _get_or_create_user(db_session, "5511999999999", "Fulano")
    db_session.commit()

    second = _get_or_create_user(db_session, "5511999999999", "Fulano")

    assert second.id == first.id
    assert db_session.query(User).count() == 1


def test_updates_name_when_new_name_is_different(db_session):
    """
    Atualiza o nome quando um valor diferente é informado.
    """
    _get_or_create_user(db_session, "5511999999999", "Fulano")
    db_session.commit()

    updated = _get_or_create_user(db_session, "5511999999999", "Fulano Silva")

    assert updated.name == "Fulano Silva"


def test_does_not_update_name_when_none(db_session):
    """
    Mantém o nome atual quando nenhum nome é informado.
    """
    _get_or_create_user(db_session, "5511999999999", "Fulano")
    db_session.commit()

    updated = _get_or_create_user(db_session, "5511999999999", None)

    assert updated.name == "Fulano"


def test_get_or_create_user_persists_and_returns_id(db_session):
    """
    Verifica se a função cria o usuário, persiste o registro no banco
    de dados e retorna o identificador do usuário.
    """
    user_id = get_or_create_user("5511988888888", "Ciclana")

    assert isinstance(user_id, int)

    persisted = db_session.query(User).filter_by(id=user_id).one()
    assert persisted.number == "5511988888888"
    assert persisted.name == "Ciclana"
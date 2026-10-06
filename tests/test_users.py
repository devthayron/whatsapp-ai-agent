from app.schemas.user import UserSchema
from database.models import User
from database.users import get_or_create_user


def test_creates_new_user_when_not_exists(db_session):
    user = get_or_create_user("5511999999999", "Fulano")

    assert isinstance(user, UserSchema)
    assert user.id is not None
    assert user.number == "5511999999999"
    assert user.name == "Fulano"


def test_returns_existing_user_without_duplicating(db_session):
    first = get_or_create_user("5511999999999", "Fulano")
    second = get_or_create_user("5511999999999", "Fulano")

    assert second.id == first.id
    assert db_session.query(User).count() == 1


def test_updates_name_when_new_name_is_different(db_session):
    get_or_create_user("5511999999999", "Fulano")

    updated = get_or_create_user("5511999999999", "Fulano Silva")

    assert updated.name == "Fulano Silva"


def test_does_not_update_name_when_none(db_session):
    get_or_create_user("5511999999999", "Fulano")

    updated = get_or_create_user("5511999999999", None)

    assert updated.name == "Fulano"


def test_get_or_create_user_returns_user_schema(db_session):
    user = get_or_create_user("5511988888888", "Ciclana")

    assert isinstance(user, UserSchema)
    assert isinstance(user.id, int)
    assert user.number == "5511988888888"
    assert user.name == "Ciclana"

    persisted = db_session.query(User).filter_by(id=user.id).one()

    assert persisted.number == "5511988888888"

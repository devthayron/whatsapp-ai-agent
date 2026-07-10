from database.connection import SessionLocal
from database.models import User


def _get_or_create_user(
    session,
    number,
    name,
):
    user = (
        session.query(User)
        .filter_by(number=number)
        .one_or_none()
    )

    if user is None:

        user = User(
            name=name,
            number=number,
        )

        session.add(user)
        session.flush()

    elif name:

        user.name = name

    return user


def get_or_create_user(
    number,
    name,
):
    """Retorna o id do usuário."""

    with SessionLocal() as session:

        user = _get_or_create_user(
            session,
            number,
            name,
        )

        session.commit()

        return user.id
import logging

from app.schemas.user import UserSchema
from database.connection import SessionLocal
from database.models import User

logger = logging.getLogger(__name__)


def get_or_create_user(number: str, name: str | None) -> UserSchema:
    """
    Retorna o usuário pelo número, criando-o caso não exista.

    Se o usuário já existir e um novo nome for informado, o nome é atualizado.

    Args:
        number: Número do usuário.
        name: Nome informado pelo contato, se disponível.

    Returns:
        Dados do usuário encontrado ou criado.
    """

    with SessionLocal() as session:
        user = session.query(User).filter_by(number=number).one_or_none()

        if user is None:
            user = User(name=name, number=number)
            session.add(user)
            session.flush()

            logger.info("Novo usuário criado | number=%s", number)

        elif name and name != user.name:
            logger.debug(
                "Nome do usuário atualizado | number=%s | nome_antigo=%s | nome_novo=%s",
                number,
                user.name,
                name,
            )
            user.name = name

        session.commit()

        return UserSchema.model_validate(user)

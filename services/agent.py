from services.openai import openai_service
from database.conversations import (
    ensure_history,
    save_message,
    get_openai_history,
)
from database.users import get_or_create_user


def process_conversation(msg):
    """
    Recebe uma mensagem do usuário e retorna a resposta da IA.
    """
    user_id = get_or_create_user(
        number=msg['number'],
        name=msg['push_name'],
    )

    ensure_history(user_id)

    save_message(**msg)

    history = get_openai_history(user_id)

    response = openai_service.generate_response(history)

    save_message(
        number=msg['number'],
        push_name=msg['push_name'],
        from_me=True,
        content=response,
    )

    return response
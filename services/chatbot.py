from services.openai import openai_service
from storage.conversations import (
    save_message,
    get_openai_history,
)


def reply(
    *,
    number: str,
    push_name: str | None,
    message: str,
    from_me: bool = False,
    timestamp: int | None = None,
) -> str:
    """
    Processa uma conversa com a IA.

    - Salva a mensagem recebida.
    - Monta o histórico.
    - Gera a resposta da IA.
    - Salva a resposta.
    """

    conversation = save_message(
        number=number,
        push_name=push_name,
        from_me=from_me,
        content=message,
        timestamp=timestamp,
    )

    history = get_openai_history(conversation)

    response = openai_service.generate_response(history)

    save_message(
        number=number,
        push_name=push_name,
        from_me=True,
        content=response,
    )

    return response
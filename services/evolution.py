from config import SESSION, URL_GET_MESSAGES


def get_messages(payload: dict | None = None) -> list:
    """Obtém as mensagens da Evolution API."""

    response = SESSION.post(
        URL_GET_MESSAGES,
        json=payload or {},
    )

    response.raise_for_status()

    data = response.json()
    return data["messages"]["records"]
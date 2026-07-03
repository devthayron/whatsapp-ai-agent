from config import SESSION, URL_GET_MESSAGES, URL_SEND_MESSAGES


def get_messages(payload: dict | None = None) -> list:
    """Obtém as mensagens da Evolution API."""

    response = SESSION.post(
        URL_GET_MESSAGES,
        json=payload or {},
    )

    response.raise_for_status()

    data = response.json()
    return data["messages"]["records"]

def send_message(number: str, text: str) -> dict:
    """Envia uma mensagem de texto para um número via Evolution API."""

    payload = {
        "number": f'{number}@s.whatsapp.net',
        "text": text
    }
    
    response = SESSION.post(
        URL_SEND_MESSAGES,
        json=payload,
    )
    if not response.ok:
        print("Resposta da API:", response.text)

    response.raise_for_status()

    return response.json()
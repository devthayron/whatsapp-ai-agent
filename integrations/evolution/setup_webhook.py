import requests

from config import settings


def configure_webhook() -> None:
    url = f"{settings.BASE_URL}/webhook/set/{settings.INSTANCE}"

    payload = {
        "webhook": {
            "enabled": True,
            "url": settings.WEBHOOK_URL,
            "events": ["MESSAGES_UPSERT"],
            "headers": {
                "X-Webhook-Secret": settings.WEBHOOK_SECRET,
            },
            "base64": True,
        }
    }

    headers = {
        "apikey": settings.API_KEY_EVO,
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
    )

    print(response.status_code)
    print(response.text)

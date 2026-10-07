import logging

import requests

from config import settings

logger = logging.getLogger(__name__)

# executar python -m integrations.evolution.setup_webhook


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

    logger.info(
        "Configurando webhook | instance=%s | url=%s",
        settings.INSTANCE,
        settings.WEBHOOK_URL,
    )

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        logger.info(
            "Resposta da configuração do webhook | status=%s", response.status_code
        )

        response.raise_for_status()

    except requests.RequestException:
        logger.exception("Erro ao configurar webhook | instance=%s", settings.INSTANCE)
        raise

    logger.info("Webhook configurado com sucesso")

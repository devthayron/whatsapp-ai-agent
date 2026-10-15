# integrations/meta/client.py
import logging

import requests

from config import settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com"
REQUEST_TIMEOUT = 30


class MetaService:
    """Cliente da WhatsApp Cloud API."""

    def __init__(self):
        self.url = (
            f"{GRAPH_URL}/{settings.META_API_VERSION}"
            f"/{settings.META_PHONE_NUMBER_ID}/messages"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
        )

    def send_message(self, number: str, text: str) -> dict:
        """Envia texto livre (só vale dentro da janela de 24h do usuário)."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        try:
            response = self.session.post(
                self.url, json=payload, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                error = exc.response.json().get("error", {})
            except ValueError:
                error = {}
            logger.error(
                "Meta API erro HTTP | status=%s | code=%s | type=%s",
                exc.response.status_code,
                error.get("code"),
                error.get("type"),
            )
            raise
        except requests.RequestException:
            logger.exception("Erro de comunicação com Meta API")
            raise

        return response.json()


meta_service = MetaService()

import logging

import requests

from config import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
ERROR_RESPONSE_LIMIT = 1000


class EvolutionService:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.instance = settings.INSTANCE

        self.url_send_messages = f"{self.base_url}/message/sendText/{self.instance}"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "apikey": settings.API_KEY_EVO,
                "Content-Type": "application/json",
            }
        )

    def _post(self, url, payload, operation):
        try:
            response = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

        except requests.HTTPError:
            logger.error(
                "Evolution API retornou erro HTTP | operation=%s | status=%s | url=%s | response=%s",
                operation,
                response.status_code,
                url,
                response.text[:ERROR_RESPONSE_LIMIT],
            )
            raise

        except requests.RequestException:
            logger.exception(
                "Erro de comunicação com Evolution API | operation=%s | url=%s",
                operation,
                url,
            )
            raise

        return response

    @staticmethod
    def _get_json(response):
        try:
            return response.json()
        except ValueError:
            logger.error(
                "Evolution API retornou resposta inválida | status=%s | response=%s",
                response.status_code,
                response.text[:ERROR_RESPONSE_LIMIT],
            )
            raise

    def send_message(self, number: str, text: str):
        payload = {
            "number": f"{number}@s.whatsapp.net",
            "text": text,
        }

        response = self._post(
            url=self.url_send_messages,
            payload=payload,
            operation=f"enviar mensagem | number={number}",
        )

        data = self._get_json(response)

        logger.info(
            "Mensagem enviada | number=%s | status=%s",
            number,
            response.status_code,
        )

        return data


evolution_service = EvolutionService()

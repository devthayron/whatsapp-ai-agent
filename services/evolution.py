import logging

import requests

from config import settings

logger = logging.getLogger(__name__)


class EvolutionService:
    def __init__(self):

        self.base_url = settings.BASE_URL
        self.instance = settings.INSTANCE

        self.url_get_messages = f"{self.base_url}/chat/findMessages/{self.instance}"

        self.url_send_messages = f"{self.base_url}/message/sendText/{self.instance}"

        self.session = requests.Session()

        self.session.headers.update(
            {"apikey": settings.API_KEY_EVO, "Content-Type": "application/json"}
        )

    def get_messages(self, page=1):

        payload = {
            "page": page,
        }

        try:
            response = self.session.post(self.url_get_messages, json=payload)

            response.raise_for_status()

        except Exception:
            logger.exception(
                "Erro ao buscar mensagens | url=%s | page=%s",
                self.url_get_messages,
                page,
            )
            raise

        return response.json()["messages"]

    def get_all_messages(self):

        records = []

        page = 1

        while True:
            data = self.get_messages(page)

            records.extend(data["records"])

            if page >= data["pages"]:
                break

            page += 1

        return records

    def get_messages_by_number(self, number: str):

        jid = f"{number}@s.whatsapp.net"

        messages = []

        for field in ["remoteJid", "remoteJidAlt"]:
            page = 1

            while True:
                payload = {
                    "where": {"key": {field: jid}},
                    "page": page,
                }

                try:
                    response = self.session.post(self.url_get_messages, json=payload)

                    response.raise_for_status()

                except Exception:
                    logger.exception(
                        "Erro ao buscar mensagens | number=%s | field=%s", number, field
                    )

                    raise

                data = response.json()["messages"]

                messages.extend(data["records"])

                if page >= data["pages"]:
                    break

                page += 1

        unique = {msg["id"]: msg for msg in messages}

        logger.debug(
            "Mensagens encontradas | number=%s | total=%s", number, len(unique)
        )

        return list(unique.values())

    def send_message(
        self,
        number: str,
        text: str,
    ):

        payload = {"number": f"{number}@s.whatsapp.net", "text": text}

        try:
            response = self.session.post(self.url_send_messages, json=payload)

            response.raise_for_status()

        except Exception:
            logger.exception("Erro ao enviar mensagem | number=%s", number)

            raise

        logger.info("Mensagem enviada | number=%s", number)

        return response.json()


evolution_service = EvolutionService()

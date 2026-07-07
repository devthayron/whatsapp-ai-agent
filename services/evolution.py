from config import (
    SESSION,
    URL_GET_MESSAGES,
    URL_SEND_MESSAGES,
)


class EvolutionService:

    def get_messages(self, payload=None):

        response = SESSION.post(
            URL_GET_MESSAGES,
            json=payload or {},
        )

        response.raise_for_status()

        data = response.json()

        return data["messages"]["records"]

    def get_messages_by_number(self, number: str):

        target = f"{number}@s.whatsapp.net"

        records = self.get_messages()

        return [
            record
            for record in records
            if (
                record.get("key", {}).get("remoteJid") == target
                or record.get("key", {}).get("remoteJidAlt") == target
            )
        ]

    def send_message(
        self,
        number: str,
        text: str,
    ):

        payload = {
            "number": f"{number}@s.whatsapp.net",
            "text": text,
        }

        response = SESSION.post(
            URL_SEND_MESSAGES,
            json=payload,
        )

        response.raise_for_status()

        return response.json()


evolution_service = EvolutionService()
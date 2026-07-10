from config import (
    SESSION,
    URL_GET_MESSAGES,
    URL_SEND_MESSAGES,
)


class EvolutionService:

    def get_messages(self, page=1):

        payload = {
            "page": page,
        }

        response = SESSION.post(
            URL_GET_MESSAGES,
            json=payload,
        )

        response.raise_for_status()

        return response.json()["messages"]


    def get_all_messages(self):

        records = []

        page = 1

        while True:

            data = self.get_messages(page)

            records.extend(
                data["records"]
            )

            if page >= data["pages"]:
                break

            page += 1

        return records


    def get_messages_by_number(self, number: str):

        target = f"{number}@s.whatsapp.net"

        records = self.get_all_messages()

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
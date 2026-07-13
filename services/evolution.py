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
        """Busca todas as mensagens percorrendo as páginas da API."""

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
        """
        Busca mensagens de um contato diretamente pela API.

        Pesquisa usando remoteJid e remoteJidAlt.
        """

        jid = f"{number}@s.whatsapp.net"

        messages = []

        for field in [
            "remoteJid",
            "remoteJidAlt",
        ]:

            page = 1

            while True:

                payload = {
                    "where": {
                        "key": {
                            field: jid
                        }
                    },
                    "page": page,
                }

                response = SESSION.post(
                    URL_GET_MESSAGES,
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()["messages"]

                messages.extend(
                    data["records"]
                )

                if page >= data["pages"]:
                    break

                page += 1


        unique = {
            msg["id"]: msg
            for msg in messages
        }

        return list(unique.values())


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
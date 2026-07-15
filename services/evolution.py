import logging

from config import (
    SESSION,
    URL_GET_MESSAGES,
    URL_SEND_MESSAGES,
)

logger = logging.getLogger(__name__)

class EvolutionService:

    def get_messages(self, page=1):

        payload = {
            "page": page,
        }

        try:
            response = SESSION.post(
                URL_GET_MESSAGES,
                json=payload,
            )

            response.raise_for_status()

        except Exception:
            logger.exception(
                "Erro ao buscar mensagens na Evolution API | url=%s | page=%s",
                URL_GET_MESSAGES,
                page,
            )
            raise

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

                try:
                    response = SESSION.post(
                        URL_GET_MESSAGES,
                        json=payload,
                    )

                    response.raise_for_status()
                except Exception:
                    logger.exception(
                        "Erro ao buscar mensagens por número | number=%s | campo=%s | page=%s",
                        number,
                        field,
                        page,
                    )
                    raise

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

        logger.debug(
            "Mensagens únicas encontradas para o número | number=%s | total=%s",
            number,
            len(unique),
        )

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

        try:
            response = SESSION.post(
                URL_SEND_MESSAGES,
                json=payload,
            )

            response.raise_for_status()
        except Exception:
            logger.exception(
                "Erro ao enviar mensagem via Evolution API | number=%s | url=%s",
                number,
                URL_SEND_MESSAGES,
            )
            raise

        logger.info(
            "Mensagem enviada com sucesso | number=%s",
            number,
        )

        
        return response.json()


evolution_service = EvolutionService()
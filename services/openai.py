import logging
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PROMPT = {
    "id": "pmpt_6a4c03086f2081939978a699ca50ad7d0fe8ed8ab07bf32a",  # ID do prompt configurado no OpenAI Platform
    "version": "3"
}

class OpenAIService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-5.4-nano"

    def generate_response(self, messages: list) -> str:

        logger.debug(
            "Enviando requisição à OpenAI | model=%s | messages=%s",
            self.model,
            len(messages),
        )

        start = time.monotonic()

        try:
            response = self.client.responses.create(
                model=self.model,
                prompt=PROMPT,
                input=messages
            )

        except Exception:
            logger.exception(
                "Erro ao gerar resposta da OpenAI | model=%s",
                self.model,
            )
            raise

        elapsed = time.monotonic() - start

        if response.usage:
            logger.debug(
                "Uso da OpenAI | input_tokens=%s | output_tokens=%s",
                response.usage.input_tokens,
                response.usage.output_tokens,
            )

        logger.info(
            "Resposta da OpenAI gerada | model=%s | tempo=%.2fs",
            self.model,
            elapsed,
        )

        return response.output_text


openai_service = OpenAIService()
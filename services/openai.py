import logging
import time

from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)

PROMPT = {
    "id": "pmpt_6a4c03086f2081939978a699ca50ad7d0fe8ed8ab07bf32a",  # ID do prompt configurado no OpenAI Platform
    "version": "3",
}

instrucao = """
Você é um agente de IA para WhatsApp.

Siga estas regras:
- Responda sempre em português.
- Utilize o histórico apenas para compreender o contexto da conversa.
- Considere datas e horários do histórico como metadados, não como conteúdo.
- Nunca mencione, copie, cite ou faça referência às datas e horários das mensagens.
- Responda apenas ao conteúdo das mensagens, ignorando completamente as marcações de data e hora.
- Seja objetivo, natural e mantenha a continuidade da conversa.
"""


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
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
                instructions=instrucao,
                input=messages,
            )

        except Exception:
            logger.exception("Erro ao gerar resposta da OpenAI | model=%s", self.model)
            raise

        elapsed = time.monotonic() - start

        if response.usage:
            logger.debug(
                "Uso da OpenAI | input_tokens=%s | output_tokens=%s",
                response.usage.input_tokens,
                response.usage.output_tokens,
            )

        logger.info(
            "Resposta da OpenAI gerada | model=%s | tempo=%.2fs", self.model, elapsed
        )

        return response.output_text


openai_service = OpenAIService()

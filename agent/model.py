import logging
import time
from functools import lru_cache
from typing import Any

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage

from agent.prompt import SYSTEM_PROMPT
from config import settings

logger = logging.getLogger(__name__)


# reutiliza o mesmo modelo (não permite trocar o modelo com o app rodando, so se resetar)
@lru_cache(maxsize=1)
def get_model():
    logger.info(
        "Inicializando modelo de IA | provider=%s | model=%s",
        settings.AI_PROVIDER,
        settings.AI_MODEL,
    )

    kwargs = {
        "model": settings.AI_MODEL,
        "model_provider": settings.AI_PROVIDER,
    }

    if settings.AI_PROVIDER == "openai":
        kwargs["api_key"] = settings.OPENAI_API_KEY

    return init_chat_model(**kwargs)


def generate_response(messages: list[dict[str, Any]]) -> str:
    """
    Gera uma resposta usando o modelo de IA configurado.

    Args:
        messages: Lista de mensagens contendo o histórico da conversa.

    Returns:
        Texto gerado pelo modelo de IA.
    """

    model = get_model()

    model_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *messages,
    ]

    logger.debug(
        "Enviando requisição à IA | provider=%s | model=%s | messages=%s",
        settings.AI_PROVIDER,
        settings.AI_MODEL,
        len(model_messages),
    )

    start = time.monotonic()

    try:
        response = model.invoke(model_messages)

    except Exception:
        logger.exception(
            "Erro ao gerar resposta da IA | provider=%s | model=%s",
            settings.AI_PROVIDER,
            settings.AI_MODEL,
        )
        raise

    elapsed = time.monotonic() - start

    usage = getattr(response, "usage_metadata", None)

    if usage:
        logger.debug(
            "Uso da IA | input_tokens=%s | output_tokens=%s",
            usage.get("input_tokens"),
            usage.get("output_tokens"),
        )

    logger.info(
        "Resposta da IA gerada | provider=%s | model=%s | tempo=%.2fs",
        settings.AI_PROVIDER,
        settings.AI_MODEL,
        elapsed,
    )

    return response.text

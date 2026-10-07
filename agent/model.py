import logging
import time
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage

from agent.prompt import SYSTEM_PROMPT
from app.schemas.message import MessageSchema
from config import settings

logger = logging.getLogger(__name__)


# ideia, usar no parametro o ai_provider e o ai_model, para poder usar outros provedores de IA no futuro, como o Anthropic, etc.
@lru_cache(maxsize=1)
def get_model():
    """Retorna a instância cacheada do modelo de IA configurado."""
    logger.debug(
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


def generate_response(history: list[MessageSchema]) -> str:
    """
    Gera uma resposta usando o modelo de IA configurado.

    Args:
        history: Histórico da conversa, incluindo a mensagem atual.

    Returns:
        Texto gerado pelo modelo de IA.
    """

    model = get_model()

    model_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *[
            {"role": message.role, "content": message.content.strip()}
            for message in history
        ],
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

import logging
from typing import Annotated

from fastapi import APIRouter, Body, Header, HTTPException, Response

from agent.processor import process_conversation
from config import settings
from integrations.evolution.client import evolution_service
from integrations.evolution.parser import extract_webhook_message, normalize_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
def webhook(
    payload: Annotated[dict, Body()],
    x_webhook_secret: str | None = Header(default=None),
):
    """
    Recebe o webhook da Evolution API e encaminha mensagens válidas
    para o processamento da conversa.

    O webhook retorna 200 para eventos ignorados ou processados, pois
    a resposta ao usuário é enviada separadamente pela Evolution API.
    Retorna 401 para requisições não autorizadas e 500 em caso de
    erro inesperado durante o processamento.
    """

    if x_webhook_secret != settings.WEBHOOK_SECRET:
        logger.warning("Tentativa de acesso não autorizado ao webhook")
        raise HTTPException(status_code=401, detail="Unauthorized")

    raw_message = extract_webhook_message(payload)

    if not raw_message:
        return Response(status_code=200)

    message = normalize_message(raw_message)

    if not message:
        return Response(status_code=200)

    def send_msg(text):
        return evolution_service.send_message(message.number, text)

    try:
        process_conversation(message, send_msg)
    except Exception:
        logger.exception(
            "Erro inesperado ao processar webhook | number=%s | external_id=%s",
            message.number,
            message.external_id,
        )
        return Response(status_code=500)

    return Response(status_code=200)

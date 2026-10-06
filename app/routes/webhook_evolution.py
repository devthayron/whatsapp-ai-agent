import logging
from typing import Annotated

from fastapi import APIRouter, Body, Response

from agent.processor import process_conversation
from integrations.evolution.client import evolution_service
from integrations.evolution.parser import (
    extract_webhook_message,
    normalize_message,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
def webhook(payload: Annotated[dict, Body()]):
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

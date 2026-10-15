import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from agent.processor import enqueue_message
from config import settings
from integrations.meta.client import meta_service
from integrations.meta.parser import extract_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/meta", tags=["Webhook"])


async def verify_signature(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
) -> bytes:
    """Valida a assinatura HMAC-SHA256 sobre o corpo bruto."""
    body = await request.body()
    expected = (
        "sha256="
        + hmac.new(settings.META_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    )

    if not x_hub_signature_256 or not hmac.compare_digest(
        expected, x_hub_signature_256
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return body


@router.get("")
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Handshake de cadastro do webhook."""
    if (
        hub_mode == "subscribe"
        and hub_challenge is not None
        and hmac.compare_digest(hub_verify_token or "", settings.META_VERIFY_TOKEN)
    ):
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("")
def webhook(raw_body: bytes = Depends(verify_signature)):
    """Extrai as mensagens do evento e as envia para a fila."""
    try:
        payload = json.loads(raw_body)

    except (ValueError, UnicodeDecodeError):
        return Response(status_code=400)

    if not isinstance(payload, dict):
        return Response(status_code=400)

    failed = False
    for message in extract_messages(payload):

        def send_msg(text, number=message.number):
            return meta_service.send_message(number, text)

        try:
            enqueue_message(message, send_msg)

        except Exception:
            failed = True
            logger.exception("Erro ao enfileirar | external_id=%s", message.external_id)

    return Response(status_code=500 if failed else 200)

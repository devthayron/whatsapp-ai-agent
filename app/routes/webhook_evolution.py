from fastapi import APIRouter, Request

from agent.processor import process_conversation
from integrations.evolution.client import evolution_service
from integrations.evolution.parser import extract_webhook_message, normalize_message

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
async def webhook(request: Request):

    payload = await request.json()

    raw_message = extract_webhook_message(payload)

    if not raw_message:
        return {"status": "ignored"}

    msg = normalize_message(raw_message)

    if not msg:
        return {"status": "ignored"}

    response = process_conversation(msg)

    evolution_service.send_message(number=msg["number"], text=response)

    return {"status": "processed"}

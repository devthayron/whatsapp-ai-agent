from fastapi import APIRouter, Body

from agent.processor import process_conversation
from integrations.evolution.client import evolution_service
from integrations.evolution.parser import extract_webhook_message, normalize_message

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
def webhook(payload: dict = Body(...)):

    raw_message = extract_webhook_message(payload)

    msg = normalize_message(raw_message) if raw_message else None

    if not msg:
        return {"status": "ignored"}

    # define a função de envio de mensagens para o Evolution
    def send_msg(text):
        return evolution_service.send_message(msg["number"], text)

    status = process_conversation(msg, send_msg)

    return {"status": status}

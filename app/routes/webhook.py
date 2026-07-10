from fastapi import APIRouter, Request

from bot.message_processor import normalize_message, extract_webhook_message
from services.chatbot import process_conversation
from services.evolution import evolution_service

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
async def webhook(request: Request):

    payload = await request.json()
    # print(payload)
    raw_message = extract_webhook_message(payload)

    if not raw_message:
        return {"status": "ignored"}
    
    msg = normalize_message(raw_message)

    if not msg:
        return {"status": "ignored"}

    response = process_conversation(msg)

    evolution_service.send_message(
        number=msg["number"],
        text=response,
    )

    return {
        "status": "processed"
    }
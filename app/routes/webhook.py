from fastapi import APIRouter, Request

from bot.processor import process_message
from services.chatbot import reply
from services.evolution import evolution_service

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
async def webhook(request: Request):

    payload = await request.json()

    raw_message = payload.get("data") or payload

    if isinstance(raw_message, list):
        raw_message = raw_message[0]

    message = process_message(raw_message)

    if not message:
        return {"status": "ignored"}

    if message["from_me"]:
        return {"status": "ignored"}

    if not message["message"]:
        return {"status": "ignored"}

    response = reply(
        number=message["number"],
        push_name=message["push_name"],
        message=message["message"],
        timestamp=message["timestamp"],
    )

    evolution_service.send_message(
        number=message["number"],
        text=response,
    )

    return {
        "status": "processed"
    }
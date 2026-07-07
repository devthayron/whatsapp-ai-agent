from fastapi import APIRouter

from app.schemas.message import ChatRequest
from services.chatbot import reply
from services.evolution import evolution_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat(data: ChatRequest):

    response = reply(
        number=data.number,
        push_name=data.push_name,
        message=data.message,
    )

    evolution_service.send_message(
        number=data.number,
        text=response,
    )

    return {
        "response": response
    }
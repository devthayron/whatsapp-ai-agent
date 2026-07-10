from fastapi import APIRouter
from app.schemas.message import ChatRequest
from services.chatbot import process_conversation
from services.evolution import evolution_service

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/")
def chat(data: ChatRequest):

    message = {
        "number": data.number,
        "push_name": data.push_name,
        "from_me": False,
        "content": data.content,
        "message_type": "chat",
        "message_id": None,
        "timestamp": None,
    }

    response = process_conversation(message)

    evolution_service.send_message(
        number=data.number,
        text=response,
    )

    return {
        "response": response
    }
import logging

from fastapi import APIRouter

from agent.processor import process_conversation
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat(data: ChatRequest):
    message = {
        "number": data.number,
        "push_name": data.push_name,
        "role": "user",
        "content": data.content,
        "content_type": "text",
        "external_id": None,
        "timestamp": None,
    }

    reply = []

    status = process_conversation(message, send=reply.append)

    logger.info(
        "Requisição de chat processada | number=%s | status=%s",
        data.number,
        status,
    )

    return {
        "status": status,
        "response": reply[0] if reply else None,
    }

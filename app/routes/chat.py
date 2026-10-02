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
        "from_me": False,
        "content": data.content,
        "message_type": "chat",
        "message_id": None,
        "timestamp": None,
    }

    response = process_conversation(message)

    # descomentar as linhas abaixo se quiser enviar a resposta via Evolution API
    # try:
    #     evolution_service.send_message(number=data.number, text=response)
    # except Exception:
    #     logger.exception(
    #         "Falha ao enviar mensagem via Evolution API | number=%s", data.number
    #     )

    return {"response": response}

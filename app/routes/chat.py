from fastapi import APIRouter

from app.schemas.message import ChatRequest
from services.openai import openai_service
from storage.conversations import save_message, get_openai_history

router = APIRouter()


@router.post("/chat")
def chat(data: ChatRequest):

    conversation = save_message(
        number=data.number,
        push_name=data.push_name,
        from_me=False,
        content=data.message,
    )

    # MONTA HISTÓRICO NO FORMATO role/content
    messages = get_openai_history(conversation)

    # IA RESPONDE COM MEMÓRIA COMPLETA
    response = openai_service.generate_response(messages)

    # SALVA RESPOSTA DA IA
    save_message(
        number=data.number,
        push_name=data.push_name,
        from_me=True,
        content=response,
    )

    return {"response": response}
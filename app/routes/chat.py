from fastapi import APIRouter

from agent.processor import process_conversation
from app.schemas.message import MessageReceived

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat(message: MessageReceived):
    return process_conversation(message, send_msg=None)

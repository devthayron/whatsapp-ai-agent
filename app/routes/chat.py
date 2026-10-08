from fastapi import APIRouter, Depends

from agent.processor import process_conversation
from app.schemas.message import MessageReceived
from database.models import Account
from dependencies import verify_token

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat(
    message: MessageReceived,
    current_account: Account = Depends(verify_token),  # noqa: B008
):
    return process_conversation(message, send_msg=None)

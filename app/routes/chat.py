from fastapi import APIRouter, Depends

from agent.processor import process_conversation
from app.schemas.message import MessageReceived
from app.schemas.responses import ChatResponse, ErrorResponse
from database.models import Account
from dependencies import verify_token

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    # Omite campos não retornados (ex.: "retry" fora do status "failed"),
    # mas mantém "response": null quando ele é enviado explicitamente.
    response_model_exclude_unset=True,
    summary="Envia uma mensagem ao agente e recebe a resposta",
    responses={
        401: {"model": ErrorResponse, "description": "Não autenticado"},
        403: {"model": ErrorResponse, "description": "Conta desativada"},
    },
)
def chat(
    message: MessageReceived,
    current_account: Account = Depends(verify_token),  # noqa: B008
):
    """
    Rota de teste e integração: a resposta volta na requisição e não é enviada
    pelo WhatsApp. O HTTP é 200 mesmo quando `status` é `failed`.
    """
    return process_conversation(message, send_msg=None)

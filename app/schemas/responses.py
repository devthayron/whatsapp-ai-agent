from typing import Literal

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class MeResponse(BaseModel):
    id: int
    name: str | None = None
    email: str
    is_active: bool


class StatusResponse(BaseModel):
    status: str


class ChatResponse(BaseModel):
    """
    status:
      - processed: resposta gerada e salva
      - duplicate: external_id já processado (response = null)
      - failed: a IA falhou ou a resposta não foi salva (inclui retry)
    """

    status: Literal["processed", "duplicate", "failed"]
    response: str | None = None
    retry: bool | None = None


class ErrorResponse(BaseModel):
    detail: str

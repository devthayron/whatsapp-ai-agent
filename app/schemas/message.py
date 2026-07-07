from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    number: str
    message: str
    push_name: Optional[str] = None
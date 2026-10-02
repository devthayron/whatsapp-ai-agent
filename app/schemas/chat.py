from pydantic import BaseModel


class ChatRequest(BaseModel):
    number: str
    content: str
    push_name: str | None = None

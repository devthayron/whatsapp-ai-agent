from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MessageReceived(BaseModel):
    external_id: str | None = None
    number: str
    name: str | None = None
    content: str
    content_type: str = "text"
    timestamp: int | float | datetime | None = None


class MessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    external_id: str | None = None
    user_id: int
    role: Literal["user", "assistant"]
    content: str
    content_type: str
    sent_at: datetime

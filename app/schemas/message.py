from datetime import datetime

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
    role: str
    content: str
    content_type: str
    sent_at: datetime

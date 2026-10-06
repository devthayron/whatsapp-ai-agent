from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str | None = None
    number: str

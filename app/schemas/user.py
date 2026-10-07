from pydantic import BaseModel, ConfigDict, EmailStr


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str | None = None
    number: str


class AccountCreate(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str


class AccountLogin(BaseModel):
    email: EmailStr
    password: str

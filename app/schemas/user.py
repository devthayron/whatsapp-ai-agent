from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str | None = None
    number: str


class AccountCreate(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class AccountLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

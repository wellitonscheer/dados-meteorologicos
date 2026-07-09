from pydantic import BaseModel


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class MessageIn(BaseModel):
    text: str
    model: str | None = None  # id do modelo Gemini escolhido; None = usa o padrão


class MessageOut(BaseModel):
    reply: str

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


class MessageOut(BaseModel):
    reply: str

from typing import Literal

from pydantic import BaseModel


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]  # quem falou nesse turno anterior
    text: str


class MessageIn(BaseModel):
    text: str
    model: str | None = None  # id do modelo Gemini escolhido; None = usa o padrão
    # Histórico visível da conversa (turnos anteriores), reenviado a cada mensagem
    # para o modelo ter o contexto completo. Vazio na 1ª mensagem.
    history: list[HistoryItem] = []


class MessageOut(BaseModel):
    reply: str

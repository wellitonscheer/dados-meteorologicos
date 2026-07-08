from fastapi import APIRouter, Depends, HTTPException
from google import genai

from ..models import User
from ..schemas import MessageIn, MessageOut
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])

client = genai.Client()  # lê GEMINI_API_KEY do ambiente automaticamente


@router.post("/message", response_model=MessageOut)
def send_message(
    data: MessageIn,
    _user: User = Depends(get_current_user),
):
    try:
        interaction = client.interactions.create(
            model="gemini-3.5-flash",
            input=data.text,
        )
    except Exception as exc:  # falha ao chamar o Gemini -> erro limpo p/ o front
        raise HTTPException(status_code=502, detail="Erro ao consultar o Gemini") from exc
    return MessageOut(reply=interaction.output_text)

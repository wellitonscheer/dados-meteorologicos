from fastapi import APIRouter, Depends, HTTPException

from ..agent import executar_agente
from ..models import User
from ..schemas import MessageIn, MessageOut
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/message", response_model=MessageOut)
def send_message(
    data: MessageIn,
    _user: User = Depends(get_current_user),
):
    try:
        reply = executar_agente(data.text)
    except Exception as exc:  # falha ao chamar o Gemini -> erro limpo p/ o front
        raise HTTPException(status_code=502, detail="Erro ao consultar o Gemini") from exc
    return MessageOut(reply=reply)

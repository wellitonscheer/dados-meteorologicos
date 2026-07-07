from fastapi import APIRouter, Depends

from ..models import User
from ..schemas import MessageIn, MessageOut
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/message", response_model=MessageOut)
def send_message(
    _data: MessageIn,
    _user: User = Depends(get_current_user),
):
    # Ignora completamente o conteúdo recebido: sempre responde "olá".
    return MessageOut(reply="olá")

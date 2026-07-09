import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..agent import (
    MENSAGEM_ERRO_GENERICO,
    MODELO_PADRAO,
    MODELOS_DISPONIVEIS,
    executar_agente,
    stream_agente,
)
from ..models import User
from ..schemas import MessageIn, MessageOut
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger("app.chat")


@router.get("/models")
def list_models(_user: User = Depends(get_current_user)):
    """Modelos Gemini disponíveis para o chat e qual é o padrão."""
    return {"models": MODELOS_DISPONIVEIS, "default": MODELO_PADRAO}


@router.post("/message", response_model=MessageOut)
def send_message(
    data: MessageIn,
    _user: User = Depends(get_current_user),
):
    try:
        reply = executar_agente(data.text, data.model, data.history)
    except Exception as exc:  # falha ao chamar o Gemini -> erro limpo p/ o front
        logger.exception("Falha ao executar o agente (mensagem=%r)", data.text)
        raise HTTPException(status_code=502, detail="Erro ao consultar o Gemini") from exc
    return MessageOut(reply=reply)


def _sse(evento: dict) -> str:
    """Serializa um evento de domínio como um bloco SSE `data: {json}`."""
    return f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"


@router.post("/message/stream")
def send_message_stream(
    data: MessageIn,
    _user: User = Depends(get_current_user),
):
    """Mesma resposta do /message, porém em streaming (SSE): emite os eventos do
    agente (tools chamadas + pedaços do texto) em tempo real. Qualquer falha
    inesperada vira um evento `erro` final — o stream nunca "quebra seco"."""

    def gerar():
        try:
            for evento in stream_agente(data.text, data.model, data.history):
                yield _sse(evento)
        except Exception:
            logger.exception("Falha no stream do agente (mensagem=%r)", data.text)
            yield _sse({"tipo": "erro", "mensagem": MENSAGEM_ERRO_GENERICO})
            yield _sse({"tipo": "fim"})

    return StreamingResponse(
        gerar(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # evita buffering em proxies
            "Connection": "keep-alive",
        },
    )

"""Loop do agente: conversa com o Gemini executando tools (function calling).

O loop roda em modo *streaming* (Interactions API, `stream=True`) e emite
"eventos de domínio" (dicts) enquanto acontece: tools chamadas (nome + args) e
os pedaços do texto final. Dois consumidores usam o mesmo núcleo:
- `stream_agente` -> alimenta o endpoint SSE (chat ao vivo);
- `executar_agente` -> drena o gerador e devolve a string final (endpoint
  clássico `/api/message` e usos não-streaming).
"""
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai

from .config import GOOGLE_SHEETS_SPREADSHEET_NAME
from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

client = genai.Client()  # lê GEMINI_API_KEY do ambiente automaticamente
logger = logging.getLogger("app.agent")

# Modelos que o usuário pode escolher no chat. O id é o nome exato do modelo na
# API do Gemini (confirmado na doc oficial); o label é o que aparece na tela.
# "Gemini 3 Flash" só existe como preview (não ganhou id estável).
MODELOS_DISPONIVEIS = [
    {"id": "gemini-3.5-flash", "label": "Gemini 3.5 Flash"},
    {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
    {"id": "gemini-2.5-flash-lite", "label": "Gemini 2.5 Flash Lite"},
    {"id": "gemini-3-flash-preview", "label": "Gemini 3 Flash"},
    {"id": "gemini-3.1-flash-lite", "label": "Gemini 3.1 Flash Lite"},
]
MODELO_PADRAO = "gemini-2.5-flash"
_MODELOS_VALIDOS = {m["id"] for m in MODELOS_DISPONIVEIS}

MAX_ITERACOES = 5  # rodadas com tools; depois vem 1 rodada de fechamento sem tools

MENSAGEM_QUOTA = (
    "Estou sem cota da API do Gemini no momento (limite de uso atingido). "
    "Tente novamente daqui a alguns minutos."
)

MENSAGEM_SEM_RESPOSTA = (
    "Não consegui concluir a consulta dentro do limite de etapas. "
    "Tente reformular a pergunta."
)

MENSAGEM_ERRO_GENERICO = (
    "Ocorreu um erro ao consultar o Gemini. Tente novamente em instantes."
)

# Turno de texto acrescentado aos resultados de tool na rodada de fechamento.
# Só omitir as tools não basta: o modelo ainda tenta function calls (chega a
# inventar nomes de tool); com este aviso ele responde em texto com o que tem.
AVISO_FECHAMENTO = {
    "type": "user_input",
    "content": [
        {
            "type": "text",
            "text": (
                "O limite de chamadas de tools desta resposta foi atingido. "
                "Responda agora com as informações que você já tem, "
                "explicando o que faltou."
            ),
        }
    ],
}

SYSTEM_INSTRUCTION = (
    "Você é um assistente de dados meteorológicos para produtores rurais. "
    f"Você tem acesso à planilha '{GOOGLE_SHEETS_SPREADSHEET_NAME}' por duas "
    "tools — buscar_registros (filtra a planilha por um termo e devolve só os "
    "registros que casam) e ler_registros (lista a planilha inteira) —, a uma "
    "segunda planilha com os produtores e suas propriedades pela tool "
    "buscar_propriedades (dados cadastrais, cultura e coordenadas geográficas "
    "exatas de cada propriedade), à previsão do tempo por coordenada pela tool "
    "previsao_tempo, à geocodificação de nomes de lugares pela tool "
    "geocodificar_local (nome de cidade/localidade → coordenadas), e à agenda "
    "do Google Calendar pela tool listar_eventos "
    "(próximos compromissos: título, início, fim, local). Combine as tools "
    "quando fizer sentido. Só afirme dados que vieram das tools; se uma tool "
    "retornar 'erro', explique o problema ao usuário em linguagem simples. "
    "Responda sempre em português."
)

FUSO = ZoneInfo("America/Sao_Paulo")  # mesmo fuso das tools (previsão/agenda)
_DIAS_SEMANA = (
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
)
_MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def _contexto_atual() -> str:
    """Frase com a data/hora atual, calculada a cada mensagem — dá ao modelo a
    referência para 'hoje', 'amanhã', 'fim de semana' etc. Os nomes em PT ficam
    em tuplas porque o locale pt_BR não é garantido no container."""
    agora = datetime.now(FUSO)
    return (
        f"Contexto atual: agora são {agora.hour}h{agora.minute:02d} de "
        f"{_DIAS_SEMANA[agora.weekday()]}, {agora.day} de "
        f"{_MESES[agora.month - 1]} de {agora.year}, no fuso {FUSO} "
        "(horário de Brasília)."
    )


def _executar_tool(nome: str, argumentos: dict):
    """Executa a tool e devolve o objeto de retorno (serializável em JSON).

    Erros esperados/ inesperados viram `{"erro": "..."}` para o modelo explicar
    ao usuário; nunca levanta exceção.
    """
    logger.info("executando tool %s com argumentos %s", nome, argumentos)
    funcao = TOOL_FUNCTIONS.get(nome)
    if funcao is None:
        return {"erro": f"Tool desconhecida: {nome}"}
    try:
        return funcao(**argumentos)
    except Exception as exc:  # erro inesperado vira resultado p/ o modelo explicar
        return {"erro": f"Falha ao executar a tool {nome}: {exc}"}


def _resolver_modelo(modelo: str | None) -> str:
    """Aceita só modelos da allowlist; qualquer outro cai no padrão."""
    if modelo in _MODELOS_VALIDOS:
        return modelo
    if modelo:
        logger.warning("modelo desconhecido %r; usando padrão %s", modelo, MODELO_PADRAO)
    return MODELO_PADRAO


def _e_erro_de_quota(exc: Exception) -> bool:
    """Reconhece o erro de cota (429) do Gemini sem depender da classe privada do SDK."""
    if getattr(exc, "status_code", None) == 429:
        return True
    texto = f"{type(exc).__name__} {exc}".lower()
    return any(t in texto for t in ("429", "resource_exhausted", "quota", "too_many_requests"))


def _chamadas_da_interacao(final):
    """Extrai as function calls de uma interação completa (fonte autoritativa)."""
    passos = getattr(final, "steps", None) or []
    return [
        {"id": s.id, "name": s.name, "args": dict(getattr(s, "arguments", None) or {})}
        for s in passos
        if getattr(s, "type", None) == "function_call"
    ]


def _chamadas_acumuladas(chamadas: dict):
    """Reconstrói as function calls a partir do que foi acumulado no stream.

    Usado quando não veio o evento `interaction.completed` (ex.: turno que
    termina em `requires_action`). Prioriza os args montados via `arguments_delta`.
    """
    resultado = []
    for idx in sorted(chamadas):
        c = chamadas[idx]
        args = c["args"]
        if c["args_str"]:
            try:
                args = json.loads(c["args_str"])
            except ValueError:
                args = c["args"]  # fragmentos ainda incompletos: fica com o inicial
        resultado.append({"id": c["id"], "name": c["name"], "args": args})
    return resultado


def _montar_entrada(historico, texto_usuario: str):
    """Monta o `input` da 1ª chamada ao Gemini a partir do histórico da conversa.

    Sem histórico, devolve a string da mensagem atual (comportamento de sempre).
    Com histórico, devolve a lista de turnos (`user_input` / `model_output`) seguida
    da mensagem atual — assim o modelo recebe o contexto completo da conversa. Os
    shapes seguem a Interactions API; turnos de histórico não exigem ids. Trocar por
    um preâmbulo de texto (caso a API rejeite os turnos) é uma mudança só aqui.
    """
    if not historico:
        return texto_usuario
    entrada = []
    for h in historico:
        tipo = "user_input" if h.role == "user" else "model_output"
        entrada.append({"type": tipo, "content": [{"type": "text", "text": h.text}]})
    entrada.append({"type": "user_input", "content": [{"type": "text", "text": texto_usuario}]})
    return entrada


def _conversar_stream(texto_usuario: str, modelo: str, historico=None):
    """Roda o loop de function calling em streaming, emitindo eventos de domínio.

    Cada item gerado é um dict com uma chave "tipo":
      {"tipo": "tool",     "nome": str, "argumentos": dict}   # tool prestes a rodar
      {"tipo": "tool_fim", "nome": str, "erro": bool}         # tool concluída
      {"tipo": "texto",    "delta": str}                      # pedaço da resposta
      {"tipo": "erro",     "mensagem": str}                   # erro amigável (encerra)
      {"tipo": "fim"}                                         # fim da resposta
    """
    logger.info(
        "chamando Gemini em streaming (modelo=%s, turnos_historico=%d), input=%r",
        modelo, len(historico or []), texto_usuario,
    )
    entrada = _montar_entrada(historico, texto_usuario)
    previous_id = None
    algum_texto = False

    for rodada in range(MAX_ITERACOES + 1):
        # A rodada extra é a de fechamento: os resultados da última rodada de
        # tools (que antes eram descartados) seguem para o modelo com o aviso
        # de limite atingido, e as tools não são reenviadas (`tools` é
        # interaction-scoped), para a resposta sair em texto.
        fechamento = rodada == MAX_ITERACOES
        if fechamento:
            entrada = [*entrada, AVISO_FECHAMENTO]
        kwargs = {
            "model": modelo,
            "input": entrada,
            "stream": True,
        }
        if not fechamento:
            kwargs["tools"] = TOOL_DECLARATIONS
        if previous_id is None:
            # system_instruction é interaction-scoped; no modo stateful o servidor
            # mantém no thread, então só enviamos na 1ª chamada (alinha com a doc).
            kwargs["system_instruction"] = f"{SYSTEM_INSTRUCTION} {_contexto_atual()}"
        else:
            kwargs["previous_interaction_id"] = previous_id

        try:
            stream = client.interactions.create(**kwargs)
        except Exception as exc:
            if _e_erro_de_quota(exc):
                logger.warning("cota do Gemini esgotada (429): %s", exc)
                yield {"tipo": "erro", "mensagem": MENSAGEM_QUOTA}
                return
            raise

        turno_id = previous_id
        final = None
        chamadas = {}  # index -> {"id", "name", "args", "args_str"}
        try:
            for ev in stream:
                tipo = getattr(ev, "event_type", None)
                if tipo == "interaction.created":
                    turno_id = ev.interaction.id
                elif tipo == "interaction.completed":
                    final = ev.interaction
                    turno_id = ev.interaction.id
                elif tipo == "interaction.status_update":
                    turno_id = ev.interaction_id or turno_id
                elif tipo == "step.start":
                    passo = ev.step
                    if getattr(passo, "type", None) == "function_call":
                        chamadas[ev.index] = {
                            "id": passo.id,
                            "name": passo.name,
                            "args": dict(getattr(passo, "arguments", None) or {}),
                            "args_str": "",
                        }
                elif tipo == "step.delta":
                    delta = ev.delta
                    dtipo = getattr(delta, "type", None)
                    if dtipo == "text" and delta.text:
                        algum_texto = True
                        yield {"tipo": "texto", "delta": delta.text}
                    elif dtipo == "arguments_delta":
                        c = chamadas.get(ev.index)
                        if c is not None and delta.arguments:
                            c["args_str"] += delta.arguments
                elif tipo == "error":
                    detalhe = getattr(getattr(ev, "error", None), "message", None)
                    logger.error("evento de erro no stream do Gemini: %s", detalhe)
                    yield {"tipo": "erro", "mensagem": MENSAGEM_ERRO_GENERICO}
                    return
        except Exception as exc:
            if _e_erro_de_quota(exc):
                logger.warning("cota do Gemini esgotada (429) durante o stream: %s", exc)
                yield {"tipo": "erro", "mensagem": MENSAGEM_QUOTA}
                return
            raise
        finally:
            stream.close()  # libera a conexão mesmo em erro/desconexão

        # O stream é a fonte confiável das function calls: `step.start` entrega
        # nome/id e os args chegam via `arguments_delta`. O evento
        # `interaction.completed` de um turno `requires_action` costuma vir com
        # `steps=None` mesmo havendo tool (era a causa do 502), então a interação
        # completa só é usada como último recurso.
        lista = _chamadas_acumuladas(chamadas)
        if not lista and final is not None:
            lista = _chamadas_da_interacao(final)

        # Na rodada de fechamento não há tools declaradas, então qualquer
        # function call remanescente é ignorada e a resposta é o texto emitido.
        if fechamento or not lista:
            if not algum_texto:
                yield {"tipo": "texto", "delta": MENSAGEM_SEM_RESPOSTA}
            yield {"tipo": "fim"}
            return

        resultados = []
        for c in lista:
            yield {"tipo": "tool", "nome": c["name"], "argumentos": c["args"]}
            retorno = _executar_tool(c["name"], c["args"] or {})
            erro = isinstance(retorno, dict) and "erro" in retorno
            yield {"tipo": "tool_fim", "nome": c["name"], "erro": erro}
            resultados.append(
                {
                    "type": "function_result",
                    "name": c["name"],
                    "call_id": c["id"],
                    "result": [
                        {"type": "text", "text": json.dumps(retorno, ensure_ascii=False, default=str)}
                    ],
                }
            )

        entrada = resultados
        previous_id = turno_id


def stream_agente(texto_usuario: str, modelo: str | None = None, historico=None):
    """Versão streaming (para o endpoint SSE): gera os eventos de domínio."""
    return _conversar_stream(texto_usuario, _resolver_modelo(modelo), historico)


def executar_agente(texto_usuario: str, modelo: str | None = None, historico=None) -> str:
    """Drena o stream e devolve a resposta final em texto.

    Converte o erro de cota do Gemini em mensagem amigável; erros inesperados
    propagam (o chat.py devolve 502).
    """
    partes = []
    for ev in _conversar_stream(texto_usuario, _resolver_modelo(modelo), historico):
        if ev["tipo"] == "texto":
            partes.append(ev["delta"])
        elif ev["tipo"] == "erro":
            return ev["mensagem"]
    return "".join(partes) or MENSAGEM_SEM_RESPOSTA

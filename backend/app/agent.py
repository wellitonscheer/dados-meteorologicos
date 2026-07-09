"""Loop do agente: conversa com o Gemini executando tools (function calling)."""
import json
import logging

from google import genai

from .config import GOOGLE_SHEETS_SPREADSHEET_NAME
from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

client = genai.Client()  # lê GEMINI_API_KEY do ambiente automaticamente
logger = logging.getLogger("app.agent")

MODEL = "gemini-2.5-flash"
MAX_ITERACOES = 5  # evita loop infinito de function calls

MENSAGEM_QUOTA = (
    "Estou sem cota da API do Gemini no momento (limite de uso atingido). "
    "Tente novamente daqui a alguns minutos."
)

SYSTEM_INSTRUCTION = (
    "Você é um assistente de dados meteorológicos para produtores rurais. "
    f"Você tem acesso à planilha '{GOOGLE_SHEETS_SPREADSHEET_NAME}' pelas tools "
    "listar_abas e ler_registros, à previsão do tempo por coordenada pela tool "
    "previsao_tempo, e à agenda do Google Calendar pela tool listar_eventos "
    "(próximos compromissos: título, início, fim, local) — combine-as quando "
    "fizer sentido (ex.: localizar o produtor "
    "na planilha e prever o tempo para a região dele). Só afirme dados que vieram "
    "das tools; se uma tool retornar 'erro', explique o problema ao usuário em "
    "linguagem simples. Responda sempre em português e em texto simples"
)


def _executar_tool(nome: str, argumentos: dict) -> str:
    logger.info("executando tool %s com argumentos %s", nome, argumentos)
    funcao = TOOL_FUNCTIONS.get(nome)
    if funcao is None:
        retorno = {"erro": f"Tool desconhecida: {nome}"}
    else:
        try:
            retorno = funcao(**argumentos)
        except Exception as exc:  # erro inesperado vira resultado p/ o modelo explicar
            retorno = {"erro": f"Falha ao executar a tool {nome}: {exc}"}
    return json.dumps(retorno, ensure_ascii=False, default=str)


def _conversar(texto_usuario: str) -> str:
    """Roda o loop de function calling e retorna a resposta final em texto."""
    logger.info("chamando Gemini (modelo=%s), input=%r", MODEL, texto_usuario)
    interaction = client.interactions.create(
        model=MODEL,
        input=texto_usuario,
        tools=TOOL_DECLARATIONS,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    for _ in range(MAX_ITERACOES):
        chamadas = [s for s in interaction.steps if s.type == "function_call"]
        if not chamadas:
            break
        resultados = [
            {
                "type": "function_result",
                "name": chamada.name,
                "call_id": chamada.id,
                "result": [
                    {
                        "type": "text",
                        "text": _executar_tool(chamada.name, chamada.arguments or {}),
                    }
                ],
            }
            for chamada in chamadas
        ]
        interaction = client.interactions.create(
            model=MODEL,
            previous_interaction_id=interaction.id,
            tools=TOOL_DECLARATIONS,
            input=resultados,
        )
    return interaction.output_text or (
        "Não consegui concluir a consulta dentro do limite de etapas. "
        "Tente reformular a pergunta."
    )


def _e_erro_de_quota(exc: Exception) -> bool:
    """Reconhece o erro de cota (429) do Gemini sem depender da classe privada do SDK."""
    if getattr(exc, "status_code", None) == 429:
        return True
    texto = f"{type(exc).__name__} {exc}".lower()
    return any(t in texto for t in ("429", "resource_exhausted", "quota", "too_many_requests"))


def executar_agente(texto_usuario: str) -> str:
    """Converte o erro de cota do Gemini em mensagem amigável; o resto propaga."""
    try:
        return _conversar(texto_usuario)
    except Exception as exc:
        if _e_erro_de_quota(exc):
            logger.warning("cota do Gemini esgotada (429): %s", exc)
            return MENSAGEM_QUOTA
        raise  # erro inesperado -> chat.py devolve 502

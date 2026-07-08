"""Loop do agente: conversa com o Gemini executando tools (function calling)."""
import json

from google import genai

from .config import GOOGLE_SHEETS_SPREADSHEET_NAME
from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

client = genai.Client()  # lê GEMINI_API_KEY do ambiente automaticamente

MODEL = "gemini-2.5-flash"
MAX_ITERACOES = 5  # evita loop infinito de function calls

SYSTEM_INSTRUCTION = (
    "Você é um assistente de dados meteorológicos para produtores rurais. "
    f"Você tem acesso à planilha '{GOOGLE_SHEETS_SPREADSHEET_NAME}' pelas tools "
    "listar_abas e ler_registros, e à previsão do tempo por coordenada pela tool "
    "previsao_tempo — combine-as quando fizer sentido (ex.: localizar o produtor "
    "na planilha e prever o tempo para a região dele). Só afirme dados que vieram "
    "das tools; se uma tool retornar 'erro', explique o problema ao usuário em "
    "linguagem simples. Responda sempre em português e em texto simples, sem "
    "markdown."
)


def _executar_tool(nome: str, argumentos: dict) -> str:
    print(f"[agente] executando tool {nome} com argumentos {argumentos}")
    funcao = TOOL_FUNCTIONS.get(nome)
    if funcao is None:
        retorno = {"erro": f"Tool desconhecida: {nome}"}
    else:
        try:
            retorno = funcao(**argumentos)
        except Exception as exc:  # erro inesperado vira resultado p/ o modelo explicar
            retorno = {"erro": f"Falha ao executar a tool {nome}: {exc}"}
    return json.dumps(retorno, ensure_ascii=False, default=str)


def executar_agente(texto_usuario: str) -> str:
    """Roda o loop de function calling e retorna a resposta final em texto."""
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

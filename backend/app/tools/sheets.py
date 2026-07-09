"""Tool de consulta à planilha de dados climáticos por produtor (Google Sheets).

Consome a infraestrutura genérica de planilhas (_planilha): abre a planilha de
clima na aba configurada e expõe ler_registros (planilha inteira) e
buscar_registros (só as linhas que casam com um termo)."""
from ..config import (
    GOOGLE_SHEETS_SPREADSHEET_NAME,
    GOOGLE_SHEETS_WORKSHEET_NAME,
)
from ._planilha import LIMITE_MAXIMO_REGISTROS, buscar, carregar, normalizar

# Colunas de identificação usadas na busca (normalizadas, sem acento/maiúsculas).
# Restringir a busca a estas colunas evita casar com valores numéricos das
# colunas de clima (ex.: Temperatura "24", Vento "15").
_COLUNAS_BUSCA = ("produtor", "cpf", "estacao", "cidade")


def ler_registros(limite: int = 50):
    """Lê os registros da aba configurada (1ª linha = cabeçalho), com limite de linhas."""
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    registros, erro = carregar(GOOGLE_SHEETS_SPREADSHEET_NAME, GOOGLE_SHEETS_WORKSHEET_NAME)
    if erro is not None:
        return erro
    return {
        "aba": GOOGLE_SHEETS_WORKSHEET_NAME,
        "total_registros": len(registros),
        "registros_retornados": min(len(registros), limite),
        "truncado": len(registros) > limite,
        "registros": registros[:limite],
    }


def buscar_registros(termo: str = "", limite: int = 10):
    """Busca registros cujos campos de identificação (produtor, estação, cidade
    ou CPF) casam com o termo. Ignora acentos/maiúsculas; exige todas as palavras."""
    if not normalizar(termo).strip():
        return {"erro": "Informe um termo de busca (nome do produtor, estação, cidade ou CPF)."}
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    registros, erro = carregar(GOOGLE_SHEETS_SPREADSHEET_NAME, GOOGLE_SHEETS_WORKSHEET_NAME)
    if erro is not None:
        return erro
    return {
        "aba": GOOGLE_SHEETS_WORKSHEET_NAME,
        "termo": termo,
        **buscar(registros, termo, _COLUNAS_BUSCA, limite),
    }


DECLARATIONS = [
    {
        "type": "function",
        "name": "ler_registros",
        "description": (
            "Lê os registros da planilha Google Sheets "
            f"'{GOOGLE_SHEETS_SPREADSHEET_NAME}' (aba configurada pelo sistema). A "
            "primeira linha é tratada como cabeçalho e cada linha seguinte vira um "
            "registro (dicionário coluna -> valor). Retorna no máximo 'limite' "
            "registros e indica se o resultado foi truncado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": (
                        f"Máximo de registros a retornar (padrão 50, teto "
                        f"{LIMITE_MAXIMO_REGISTROS})."
                    ),
                },
            },
        },
    },
    {
        "type": "function",
        "name": "buscar_registros",
        "description": (
            "Localiza o registro de um produtor na planilha "
            f"'{GOOGLE_SHEETS_SPREADSHEET_NAME}' a partir de qualquer dado de "
            "identificação que se conheça dele: o nome do produtor (coluna "
            "Produtor — a busca aceita nome parcial, inclusive só o primeiro "
            "nome), a estação, a cidade ou o CPF. Retorna apenas as linhas que "
            "casam (ignora acentos e maiúsculas; com várias palavras, todas "
            "precisam aparecer no mesmo registro). Bem mais econômico que "
            "ler_registros quando se quer um produtor específico em vez da "
            "planilha inteira. Cada linha traz as condições atuais (temperatura, "
            "umidade, precipitação, vento) e a data da última atualização."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "termo": {
                    "type": "string",
                    "description": (
                        "Texto a procurar nos campos de identificação (produtor, "
                        "estação, cidade ou CPF). Pode conter várias palavras."
                    ),
                },
                "limite": {
                    "type": "integer",
                    "description": (
                        f"Máximo de registros a retornar (padrão 10, teto "
                        f"{LIMITE_MAXIMO_REGISTROS})."
                    ),
                },
            },
            "required": ["termo"],
        },
    },
]

FUNCTIONS = {"ler_registros": ler_registros, "buscar_registros": buscar_registros}

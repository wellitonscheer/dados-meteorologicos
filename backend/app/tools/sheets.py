"""Tools de consulta à planilha Google Sheets (gspread + service account)."""
import gspread

from ..config import GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_SPREADSHEET_NAME

# Cliente criado sob demanda e cacheado: a falta da credencial não pode
# quebrar o import do app (o erro aparece só quando o modelo usa a tool).
_gc = None

LIMITE_MAXIMO_REGISTROS = 200  # teto para não estourar o contexto do modelo

_ERRO_CREDENCIAL = (
    "Arquivo de credenciais da conta de serviço não encontrado em "
    f"'{GOOGLE_SHEETS_CREDENTIALS_FILE}'. Avise o administrador do sistema."
)
_ERRO_PLANILHA = (
    f"Planilha '{GOOGLE_SHEETS_SPREADSHEET_NAME}' não encontrada. Verifique se "
    "ela foi compartilhada com a conta de serviço "
    "dados-sheets@camera-dados-meteorologicos.iam.gserviceaccount.com."
)


def _abrir_planilha():
    global _gc
    if _gc is None:
        _gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_FILE)
    return _gc.open(GOOGLE_SHEETS_SPREADSHEET_NAME)


def listar_abas():
    """Lista as abas da planilha com metadados básicos."""
    try:
        abas = _abrir_planilha().worksheets()
    except FileNotFoundError:
        return {"erro": _ERRO_CREDENCIAL}
    except gspread.SpreadsheetNotFound:
        return {"erro": _ERRO_PLANILHA}
    return {
        "planilha": GOOGLE_SHEETS_SPREADSHEET_NAME,
        "abas": [
            {"nome": ws.title, "linhas": ws.row_count, "colunas": ws.col_count}
            for ws in abas
        ],
    }


def ler_registros(nome_aba: str, limite: int = 50):
    """Lê os registros de uma aba (1ª linha = cabeçalho), com limite de linhas."""
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    try:
        registros = _abrir_planilha().worksheet(nome_aba).get_all_records()
    except FileNotFoundError:
        return {"erro": _ERRO_CREDENCIAL}
    except gspread.SpreadsheetNotFound:
        return {"erro": _ERRO_PLANILHA}
    except gspread.WorksheetNotFound:
        return {
            "erro": (
                f"A aba '{nome_aba}' não existe na planilha. "
                "Use a tool listar_abas para ver os nomes disponíveis."
            )
        }
    return {
        "aba": nome_aba,
        "total_registros": len(registros),
        "registros_retornados": min(len(registros), limite),
        "truncado": len(registros) > limite,
        "registros": registros[:limite],
    }


DECLARATIONS = [
    {
        "type": "function",
        "name": "listar_abas",
        "description": (
            "Lista as abas (worksheets) da planilha Google Sheets "
            f"'{GOOGLE_SHEETS_SPREADSHEET_NAME}', com nome, número de linhas e de "
            "colunas de cada aba. Use primeiro, para descobrir o nome exato da aba "
            "antes de ler registros."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "ler_registros",
        "description": (
            "Lê os registros de uma aba da planilha "
            f"'{GOOGLE_SHEETS_SPREADSHEET_NAME}'. A primeira linha da aba é tratada "
            "como cabeçalho e cada linha seguinte vira um registro (dicionário "
            "coluna -> valor). Retorna no máximo 'limite' registros e indica se o "
            "resultado foi truncado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nome_aba": {
                    "type": "string",
                    "description": "Nome exato da aba, como retornado por listar_abas.",
                },
                "limite": {
                    "type": "integer",
                    "description": (
                        f"Máximo de registros a retornar (padrão 50, teto "
                        f"{LIMITE_MAXIMO_REGISTROS})."
                    ),
                },
            },
            "required": ["nome_aba"],
        },
    },
]

FUNCTIONS = {"listar_abas": listar_abas, "ler_registros": ler_registros}

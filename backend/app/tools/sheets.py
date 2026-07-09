"""Tool de consulta à planilha Google Sheets (gspread + service account)."""
import gspread

from ..config import (
    GOOGLE_SHEETS_CREDENTIALS_FILE,
    GOOGLE_SHEETS_SPREADSHEET_NAME,
    GOOGLE_SHEETS_WORKSHEET_NAME,
)

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
_ERRO_ABA = (
    f"A aba '{GOOGLE_SHEETS_WORKSHEET_NAME}' não existe na planilha. Verifique o "
    "nome configurado em GOOGLE_SHEETS_WORKSHEET_NAME. Avise o administrador."
)


def _abrir_planilha():
    global _gc
    if _gc is None:
        _gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_FILE)
    return _gc.open(GOOGLE_SHEETS_SPREADSHEET_NAME)


def ler_registros(limite: int = 50):
    """Lê os registros da aba configurada (1ª linha = cabeçalho), com limite de linhas."""
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    try:
        aba = _abrir_planilha().worksheet(GOOGLE_SHEETS_WORKSHEET_NAME)
        registros = aba.get_all_records()
    except FileNotFoundError:
        return {"erro": _ERRO_CREDENCIAL}
    except gspread.SpreadsheetNotFound:
        return {"erro": _ERRO_PLANILHA}
    except gspread.WorksheetNotFound:
        return {"erro": _ERRO_ABA}
    return {
        "aba": GOOGLE_SHEETS_WORKSHEET_NAME,
        "total_registros": len(registros),
        "registros_retornados": min(len(registros), limite),
        "truncado": len(registros) > limite,
        "registros": registros[:limite],
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
]

FUNCTIONS = {"ler_registros": ler_registros}

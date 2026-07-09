"""Tool de consulta à planilha Google Sheets (gspread + service account)."""
import re
import unicodedata

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

# Colunas de identificação usadas na busca (normalizadas, sem acento/maiúsculas).
# Restringir a busca a estas colunas evita casar com valores numéricos das
# colunas de clima (ex.: Temperatura "24", Vento "15").
_COLUNAS_BUSCA = ("produtor", "cpf", "estacao", "cidade")


def _normalizar(texto):
    """Remove acentos e caixa: 'João' -> 'joao', 'Estação' -> 'estacao'."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.casefold()


def _texto_busca(registro):
    """Concatena (normalizado) só os campos de identificação do registro."""
    partes = [v for k, v in registro.items() if _normalizar(k).strip() in _COLUNAS_BUSCA]
    if not partes:  # cabeçalhos inesperados: cai para todas as colunas
        partes = list(registro.values())
    return _normalizar(" ".join(str(p) for p in partes))


def _token_casa(token, alvo, alvo_digitos):
    """Casa um token por substring; se tiver dígitos, tenta também só os dígitos
    (para CPF: '11122233344' casa com '111.222.333-44' e vice-versa)."""
    if token in alvo:
        return True
    digitos = re.sub(r"\D", "", token)
    return bool(digitos) and digitos in alvo_digitos


def _abrir_planilha():
    global _gc
    if _gc is None:
        _gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_FILE)
    return _gc.open(GOOGLE_SHEETS_SPREADSHEET_NAME)


def _carregar_registros():
    """Abre a aba e devolve (registros, None) ou (None, {"erro": ...})."""
    try:
        aba = _abrir_planilha().worksheet(GOOGLE_SHEETS_WORKSHEET_NAME)
        return aba.get_all_records(), None
    except FileNotFoundError:
        return None, {"erro": _ERRO_CREDENCIAL}
    except gspread.SpreadsheetNotFound:
        return None, {"erro": _ERRO_PLANILHA}
    except gspread.WorksheetNotFound:
        return None, {"erro": _ERRO_ABA}


def ler_registros(limite: int = 50):
    """Lê os registros da aba configurada (1ª linha = cabeçalho), com limite de linhas."""
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    registros, erro = _carregar_registros()
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
    termo_norm = _normalizar(termo).strip()
    if not termo_norm:
        return {"erro": "Informe um termo de busca (nome do produtor, estação, cidade ou CPF)."}
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    registros, erro = _carregar_registros()
    if erro is not None:
        return erro

    tokens = termo_norm.split()
    encontrados = []
    for reg in registros:
        alvo = _texto_busca(reg)
        alvo_digitos = re.sub(r"\D", "", alvo)
        if all(_token_casa(tk, alvo, alvo_digitos) for tk in tokens):
            encontrados.append(reg)

    return {
        "aba": GOOGLE_SHEETS_WORKSHEET_NAME,
        "termo": termo,
        "total_encontrados": len(encontrados),
        "registros_retornados": min(len(encontrados), limite),
        "truncado": len(encontrados) > limite,
        "registros": encontrados[:limite],
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

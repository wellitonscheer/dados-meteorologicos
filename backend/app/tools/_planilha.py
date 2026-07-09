"""Infraestrutura compartilhada de acesso a planilhas Google Sheets.

Módulo utilitário (prefixo '_' = não é módulo de tool; o tools/__init__.py não
o importa como tool). Concentra o que as tools de planilha têm em comum: um
único cliente gspread cacheado (a mesma conta de serviço abre qualquer planilha
compartilhada com ela) e as funções genéricas de carga, normalização e busca
por termo. Cada tool que consome este módulo passa o nome da planilha, o nome da
aba e as colunas de identificação que quer pesquisar.
"""
import re
import unicodedata

import gspread

from ..config import GOOGLE_SHEETS_CREDENTIALS_FILE

# Cliente criado sob demanda e cacheado, compartilhado por todas as planilhas: a
# falta da credencial não pode quebrar o import do app (o erro aparece só quando
# o modelo usa a tool). Uma mesma conta de serviço abre várias planilhas.
_gc = None

LIMITE_MAXIMO_REGISTROS = 200  # teto para não estourar o contexto do modelo

# E-mail da conta de serviço, citado nos erros para orientar quem for
# compartilhar a planilha com a conta.
_CONTA_SERVICO = "dados-sheets@camera-dados-meteorologicos.iam.gserviceaccount.com"

_ERRO_CREDENCIAL = (
    "Arquivo de credenciais da conta de serviço não encontrado em "
    f"'{GOOGLE_SHEETS_CREDENTIALS_FILE}'. Avise o administrador do sistema."
)


def normalizar(texto):
    """Remove acentos e caixa: 'João' -> 'joao', 'Estação' -> 'estacao'."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.casefold()


def texto_busca(registro, colunas):
    """Concatena (normalizado) só os campos de identificação do registro.

    'colunas' são os cabeçalhos de identificação já normalizados (sem acento/
    maiúsculas); restringir a busca a eles evita casar com valores numéricos de
    outras colunas (clima, área, coordenadas)."""
    partes = [v for k, v in registro.items() if normalizar(k).strip() in colunas]
    if not partes:  # cabeçalhos inesperados: cai para todas as colunas
        partes = list(registro.values())
    return normalizar(" ".join(str(p) for p in partes))


def token_casa(token, alvo, alvo_digitos):
    """Casa um token por substring; se tiver dígitos, tenta também só os dígitos
    (para CPF: '11122233344' casa com '111.222.333-44' e vice-versa)."""
    if token in alvo:
        return True
    digitos = re.sub(r"\D", "", token)
    return bool(digitos) and digitos in alvo_digitos


def _abrir(nome_planilha):
    global _gc
    if _gc is None:
        _gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_FILE)
    return _gc.open(nome_planilha)


def carregar(nome_planilha, nome_aba, nome_var_aba="GOOGLE_SHEETS_WORKSHEET_NAME"):
    """Abre a aba pedida e devolve (registros, None) ou (None, {"erro": ...}).

    As mensagens de erro são montadas com os nomes recebidos, para servir a
    qualquer planilha/aba. 'nome_var_aba' é a env var citada na dica de correção
    quando a aba não existe."""
    try:
        aba = _abrir(nome_planilha).worksheet(nome_aba)
        return aba.get_all_records(), None
    except FileNotFoundError:
        return None, {"erro": _ERRO_CREDENCIAL}
    except gspread.SpreadsheetNotFound:
        return None, {
            "erro": (
                f"Planilha '{nome_planilha}' não encontrada. Verifique se ela foi "
                f"compartilhada com a conta de serviço {_CONTA_SERVICO}."
            )
        }
    except gspread.WorksheetNotFound:
        return None, {
            "erro": (
                f"A aba '{nome_aba}' não existe na planilha. Verifique o nome "
                f"configurado em {nome_var_aba}. Avise o administrador."
            )
        }


def buscar(registros, termo, colunas, limite):
    """Filtra 'registros' pelos que casam com 'termo' nas 'colunas' de
    identificação. Ignora acentos/maiúsculas; com várias palavras, todas
    precisam aparecer no mesmo registro. Devolve o dicionário de resultado SEM
    chaves de identificação da planilha — cada tool acrescenta as suas."""
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    tokens = normalizar(termo).strip().split()
    encontrados = []
    for reg in registros:
        alvo = texto_busca(reg, colunas)
        alvo_digitos = re.sub(r"\D", "", alvo)
        if all(token_casa(tk, alvo, alvo_digitos) for tk in tokens):
            encontrados.append(reg)
    return {
        "total_encontrados": len(encontrados),
        "registros_retornados": min(len(encontrados), limite),
        "truncado": len(encontrados) > limite,
        "registros": encontrados[:limite],
    }

"""Tool de consulta à planilha de produtores e suas propriedades (Google Sheets).

Consome a infraestrutura genérica de planilhas (_planilha) para pesquisar a
planilha 'Produtores Propriedades', que reúne, por produtor, os dados
cadastrais e de localização de cada propriedade — inclusive as coordenadas
geográficas exatas (latitude/longitude) de cada uma."""
from ..config import (
    GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME,
    GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME,
)
from ._planilha import LIMITE_MAXIMO_REGISTROS, buscar, carregar, normalizar

# Colunas pesquisáveis (cabeçalhos normalizados): note "nome da propriedade"
# para o cabeçalho "Nome da Propriedade" e "cultura principal" para "Cultura
# Principal" — coluna de texto, então entra na busca (ex.: filtrar por "soja").
# Ficam de fora apenas as colunas numéricas (área, latitude, longitude), para a
# busca não casar com dígitos de coordenadas.
_COLUNAS_BUSCA = ("produtor", "cpf", "nome da propriedade", "cidade", "cultura principal")


def buscar_propriedades(termo: str = "", limite: int = 10):
    """Busca propriedades cujos campos pesquisáveis (produtor, nome da
    propriedade, cidade, cultura principal ou CPF) casam com o termo. Ignora
    acentos/maiúsculas; exige todas as palavras."""
    if not normalizar(termo).strip():
        return {
            "erro": (
                "Informe um termo de busca (nome do produtor, nome da "
                "propriedade, cidade, cultura ou CPF)."
            )
        }
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    registros, erro = carregar(
        GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME,
        GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME,
        "GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME",
    )
    if erro is not None:
        return erro
    return {
        "aba": GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME,
        "termo": termo,
        **buscar(registros, termo, _COLUNAS_BUSCA, limite),
    }


def ler_propriedades(limite: int = 50):
    """Lê o cadastro completo de produtores e propriedades (1ª linha =
    cabeçalho), com limite de linhas."""
    limite = max(1, min(int(limite), LIMITE_MAXIMO_REGISTROS))
    registros, erro = carregar(
        GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME,
        GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME,
        "GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME",
    )
    if erro is not None:
        return erro
    return {
        "aba": GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME,
        "total_registros": len(registros),
        "registros_retornados": min(len(registros), limite),
        "truncado": len(registros) > limite,
        "registros": registros[:limite],
    }


DECLARATIONS = [
    {
        "type": "function",
        "name": "buscar_propriedades",
        "description": (
            "Localiza propriedades rurais na planilha "
            f"'{GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME}' a partir de qualquer "
            "campo pesquisável: o nome do produtor (coluna Produtor — a busca "
            "aceita nome parcial, inclusive só o primeiro nome), o nome da "
            "propriedade, a cidade, a cultura principal ou o CPF. Retorna apenas "
            "as linhas que casam (ignora acentos e maiúsculas; com várias "
            "palavras, todas precisam aparecer no mesmo registro). Cada linha "
            "traz o produtor, o CPF, o nome da propriedade, a cidade, a área em "
            "hectares, a cultura principal e as coordenadas geográficas exatas da "
            "propriedade (latitude e longitude em graus decimais). Bem mais "
            "econômico que ler a planilha inteira quando se quer uma propriedade, "
            "um produtor ou uma cultura específicos."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "termo": {
                    "type": "string",
                    "description": (
                        "Texto a procurar nos campos pesquisáveis (produtor, "
                        "nome da propriedade, cidade, cultura principal ou CPF). "
                        "Pode conter várias palavras."
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
    {
        "type": "function",
        "name": "ler_propriedades",
        "description": (
            "Lê os registros da planilha Google Sheets "
            f"'{GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME}' (aba configurada "
            "pelo sistema) — o cadastro completo de produtores e propriedades. A "
            "primeira linha é tratada como cabeçalho e cada linha seguinte vira "
            "um registro (dicionário coluna -> valor). Retorna no máximo 'limite' "
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

FUNCTIONS = {
    "buscar_propriedades": buscar_propriedades,
    "ler_propriedades": ler_propriedades,
}

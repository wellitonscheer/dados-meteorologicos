"""Tool de geocodificação de nomes de lugares (Geocoding API do Open-Meteo).

Converte o nome de um lugar (cidade, vila, localidade) em coordenadas
geográficas. Usa a Geocoding API do Open-Meteo (dados do GeoNames), gratuita e
sem chave para uso não comercial. A resposta é resumida ao essencial (nome,
coordenadas, estado e país) para não estourar o contexto do modelo.
"""
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
QUANTIDADE_MAXIMA = 10
# A API só pesquisa pelo nome (qualificar com estado/país no termo zera os
# resultados) e o filtro countryCode dela age depois do ranking global — inútil
# para nomes ambíguos. Por isso o filtro de país é aplicado aqui: busca-se uma
# lista grande e filtra-se pelo country_code de cada resultado.
_QUANTIDADE_BRUTA_COM_FILTRO = 100


def geocodificar_local(nome: str = "", quantidade: int = 5, codigo_pais: str = ""):
    """Busca lugares pelo nome e devolve os candidatos com latitude/longitude.

    'codigo_pais' (ISO-3166 alpha-2, ex.: 'BR') restringe os resultados a um
    país; vazio devolve o ranking global da API."""
    if not str(nome).strip():
        return {"erro": "Informe o nome do lugar a geocodificar."}
    quantidade = max(1, min(int(quantidade), QUANTIDADE_MAXIMA))
    codigo_pais = str(codigo_pais).strip().upper()

    try:
        resposta = requests.get(
            GEOCODING_URL,
            params={
                "name": nome,
                "count": _QUANTIDADE_BRUTA_COM_FILTRO if codigo_pais else quantidade,
                "language": "pt",
                "format": "json",
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        return {"erro": f"Falha de rede ao consultar a geocodificação: {exc}"}

    if resposta.status_code != 200:
        return {"erro": f"API de geocodificação indisponível (HTTP {resposta.status_code})."}

    resultados = resposta.json().get("results") or []
    if codigo_pais:
        resultados = [r for r in resultados if r.get("country_code") == codigo_pais]
    lugares = [
        {
            "nome": r.get("name"),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "estado": r.get("admin1"),
            "pais": r.get("country"),
        }
        for r in resultados[:quantidade]
    ]
    resultado = {"nome_buscado": nome, "total": len(lugares), "lugares": lugares}
    if codigo_pais:
        resultado["codigo_pais"] = codigo_pais
    return resultado


DECLARATIONS = [
    {
        "type": "function",
        "name": "geocodificar_local",
        "description": (
            "Converte o nome de um lugar (cidade, vila ou localidade) em "
            "coordenadas geográficas: retorna os lugares que casam com o nome, "
            "cada um com a latitude e a longitude em graus decimais, o estado e "
            "o país, em ordem de relevância (dados do GeoNames, via Open-Meteo). "
            "A busca é global e só pelo nome — nomes de lugar comuns existem em "
            "vários países, e o filtro por país é o parâmetro codigo_pais (não "
            "adianta acrescentar estado/país ao nome)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {
                    "type": "string",
                    "description": (
                        "Nome do lugar a procurar (ex.: nome de uma cidade), sem "
                        "qualificadores de estado ou país."
                    ),
                },
                "quantidade": {
                    "type": "integer",
                    "description": (
                        f"Máximo de lugares a retornar (padrão 5, teto {QUANTIDADE_MAXIMA})."
                    ),
                },
                "codigo_pais": {
                    "type": "string",
                    "description": (
                        "Código ISO-3166 alpha-2 do país ao qual restringir os "
                        "resultados (ex.: 'BR'). Vazio busca no mundo todo."
                    ),
                },
            },
            "required": ["nome"],
        },
    },
]

FUNCTIONS = {"geocodificar_local": geocodificar_local}

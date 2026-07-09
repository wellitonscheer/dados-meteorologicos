"""Tool de previsão do tempo (Point Forecast API do Windy).

Busca as cinco informações mais úteis para produtores rurais: temperatura
(estresse térmico/geada), precipitação (plantio/colheita/irrigação), vento e
rajadas (pulverização/acamamento), umidade relativa (doenças fúngicas) e
ponto de orvalho (geada/molhamento foliar). A resposta crua da API é
3-horária; a tool resume por dia para não estourar o contexto do modelo.
"""
import math
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from ..config import WINDY_API_KEY

WINDY_URL = "https://api.windy.com/api/point-forecast/v2"
MODELO = "gfs"  # único modelo global com boa cobertura do Brasil
FUSO = ZoneInfo("America/Sao_Paulo")
DIAS_MAXIMO = 7


def _min(valores):
    return min(valores) if valores else None


def _max(valores):
    return max(valores) if valores else None


def _media(valores):
    return round(sum(valores) / len(valores), 1) if valores else None


def _item(serie, indice):
    return serie[indice] if indice < len(serie) else None


def previsao_tempo(latitude: float, longitude: float, dias: int = 3):
    """Resumo diário da previsão do tempo para um ponto (latitude/longitude)."""
    latitude, longitude = float(latitude), float(longitude)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return {
            "erro": (
                "Coordenadas inválidas: latitude deve estar entre -90 e 90 e "
                "longitude entre -180 e 180."
            )
        }
    dias = max(1, min(int(dias), DIAS_MAXIMO))

    try:
        resposta = requests.post(
            WINDY_URL,
            json={
                "lat": latitude,
                "lon": longitude,
                "model": MODELO,
                "parameters": ["temp", "precip", "wind", "windGust", "rh", "dewpoint"],
                "levels": ["surface"],
                "key": WINDY_API_KEY,
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        return {"erro": f"Falha de rede ao consultar a API do Windy: {exc}"}

    if resposta.status_code == 204:
        return {
            "erro": (
                "O modelo meteorológico não tem os parâmetros solicitados para "
                "este ponto."
            )
        }
    if resposta.status_code == 400:
        return {
            "erro": (
                "Requisição rejeitada pela API do Windy — chave WINDY_API_KEY "
                "inválida ou parâmetros malformados. Avise o administrador."
            )
        }
    if resposta.status_code != 200:
        return {"erro": f"API do Windy indisponível (HTTP {resposta.status_code})."}

    dados = resposta.json()
    temp = dados.get("temp-surface", [])
    precip = dados.get("past3hprecip-surface", [])
    vento_u = dados.get("wind_u-surface", [])
    vento_v = dados.get("wind_v-surface", [])
    rajada = dados.get("gust-surface", [])
    umidade = dados.get("rh-surface", [])
    orvalho = dados.get("dewpoint-surface", [])

    # Agrupa os pontos 3-horários por dia no fuso local, ignorando nulos.
    por_dia = defaultdict(lambda: defaultdict(list))
    for i, ts_ms in enumerate(dados.get("ts", [])):
        valores = por_dia[datetime.fromtimestamp(ts_ms / 1000, tz=FUSO).date().isoformat()]
        if (t := _item(temp, i)) is not None:
            valores["temp_c"].append(t - 273.15)
        if (p := _item(precip, i)) is not None:
            valores["precip_mm"].append(p)
        u, v = _item(vento_u, i), _item(vento_v, i)
        if u is not None and v is not None:
            valores["vento_kmh"].append(math.hypot(u, v) * 3.6)
        if (r := _item(rajada, i)) is not None:
            valores["rajada_kmh"].append(r * 3.6)
        if (h := _item(umidade, i)) is not None:
            valores["umidade_pct"].append(h)
        if (o := _item(orvalho, i)) is not None:
            valores["orvalho_c"].append(o - 273.15)

    previsao_diaria = []
    for dia in sorted(por_dia)[:dias]:
        v = por_dia[dia]
        temp_min, temp_max = _min(v["temp_c"]), _max(v["temp_c"])
        rajada_max = _max(v["rajada_kmh"])
        orvalho_min = _min(v["orvalho_c"])
        umidade_min, umidade_max = _min(v["umidade_pct"]), _max(v["umidade_pct"])
        previsao_diaria.append(
            {
                "data": dia,
                "temp_min_c": round(temp_min, 1) if temp_min is not None else None,
                "temp_max_c": round(temp_max, 1) if temp_max is not None else None,
                "precipitacao_total_mm": round(sum(v["precip_mm"]), 1),
                "vento_medio_kmh": _media(v["vento_kmh"]),
                "vento_max_kmh": round(m, 1) if (m := _max(v["vento_kmh"])) is not None else None,
                "rajada_max_kmh": round(rajada_max, 1) if rajada_max is not None else None,
                "umidade_relativa_min_pct": round(umidade_min) if umidade_min is not None else None,
                "umidade_relativa_max_pct": round(umidade_max) if umidade_max is not None else None,
                "ponto_orvalho_min_c": round(orvalho_min, 1) if orvalho_min is not None else None,
            }
        )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "modelo": MODELO,
        "fuso": str(FUSO),
        "previsao_diaria": previsao_diaria,
    }


DECLARATIONS = [
    {
        "type": "function",
        "name": "previsao_tempo",
        "description": (
            "Busca a previsão do tempo (modelo GFS, via Windy) para uma "
            "coordenada, resumida por dia: temperatura mínima/máxima, "
            "precipitação total, vento médio/máximo e rajadas, umidade relativa "
            "e ponto de orvalho. Útil para decisões do produtor rural: risco de "
            "geada (temperatura e ponto de orvalho baixos), janela de "
            "pulverização (vento e umidade), doenças fúngicas (umidade alta) e "
            "janela de plantio/colheita (chuva). Requer a latitude e a longitude "
            "do ponto em graus decimais."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude em graus decimais (Sul é negativo).",
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude em graus decimais (Oeste é negativo).",
                },
                "dias": {
                    "type": "integer",
                    "description": (
                        f"Quantos dias de previsão retornar (padrão 3, teto {DIAS_MAXIMO})."
                    ),
                },
            },
            "required": ["latitude", "longitude"],
        },
    },
]

FUNCTIONS = {"previsao_tempo": previsao_tempo}

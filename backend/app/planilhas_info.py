"""Fonte única de verdade sobre as planilhas conectadas ao agente.

Consumida em dois lugares:
- `agent.py` -> `bloco_esquema()` entra no system instruction (o modelo conhece
  as colunas de antemão e não gasta rodadas explorando a planilha);
- `routers/chat.py` -> `GET /api/planilhas` alimenta a sidebar do frontend.

Os nomes vêm da config (mesma origem usada pelas tools); URL, colunas e linhas
de exemplo são fixos deste projeto de exemplo — se a planilha real mudar,
atualize aqui.
"""
from .config import (
    GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME,
    GOOGLE_SHEETS_SPREADSHEET_NAME,
)

PLANILHAS = [
    {
        "id": "clima",
        "nome": GOOGLE_SHEETS_SPREADSHEET_NAME,
        "descricao": (
            "Condições meteorológicas atuais registradas na estação de cada produtor."
        ),
        "url": (
            "https://docs.google.com/spreadsheets/d/"
            "1lxozu1py-6vrzkG2dsgNKt4a8gJU69lDmuZ7ZFrGjks/edit?usp=sharing"
        ),
        "tools": ["buscar_registros", "ler_registros"],
        "colunas": [
            "Produtor",
            "CPF",
            "Estação",
            "Temperatura (°C)",
            "Umidade (%)",
            "Precipitação (mm)",
            "Vento (km/h)",
            "Cidade",
            "Data da Última Atualização",
        ],
        "observacoes": (
            "CPF no formato 000.000.000-00; datas no formato DD/MM/AAAA; "
            "números com ponto decimal."
        ),
        "exemplos": [
            ["João Silva", "111.222.333-44", "Estação Sítio Esperança",
             "24.5", "65", "12", "15", "Porto Alegre", "10/07/2026"],
            ["Maria Oliveira", "222.333.444-55", "Estação Fazenda Sol Nascente",
             "26.1", "58", "0", "12", "Caxias do Sul", "09/07/2026"],
            ["Pedro Souza", "333.444.555-66", "Estação Chácara das Flores",
             "22.8", "72", "5.5", "8", "Pelotas", "10/07/2026"],
        ],
    },
    {
        "id": "propriedades",
        "nome": GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME,
        "descricao": (
            "Cadastro dos produtores e suas propriedades: cidade, área, "
            "cultura principal e coordenadas."
        ),
        "url": (
            "https://docs.google.com/spreadsheets/d/"
            "1xPeV2J9J3Va0SABLarL36iaZhXiSZrLO2BvKtq1PLss/edit?usp=sharing"
        ),
        "tools": ["buscar_propriedades"],
        "colunas": [
            "Produtor",
            "CPF",
            "Nome da Propriedade",
            "Cidade",
            "Área (ha)",
            "Cultura Principal",
            "Latitude",
            "Longitude",
        ],
        "observacoes": "área em hectares; latitude e longitude em graus decimais.",
        "exemplos": [
            ["João Silva", "111.222.333-44", "Sítio Esperança", "Porto Alegre",
             "50", "Soja", "-30.0346", "-51.2177"],
            ["Maria Oliveira", "222.333.444-55", "Fazenda Sol Nascente",
             "Caxias do Sul", "120", "Uva", "-29.1683", "-51.1794"],
            ["Pedro Souza", "333.444.555-66", "Chácara das Flores", "Pelotas",
             "30", "Arroz", "-31.7719", "-52.3425"],
        ],
    },
]


def bloco_esquema() -> str:
    """Bloco factual de esquema para o system instruction do agente.

    Só colunas, formatos e a relação entre as planilhas — sem as linhas de
    exemplo: valores reais no prompt fariam o modelo responder dado congelado
    sem chamar a tool.
    """
    linhas = ["Esquema das planilhas conectadas (cabeçalhos exatos das colunas):"]
    for p in PLANILHAS:
        linhas.append(
            f"Planilha '{p['nome']}' (tools: {', '.join(p['tools'])}) — colunas: "
            f"{'; '.join(p['colunas'])}. Formatos: {p['observacoes']}"
        )
    linhas.append("As duas planilhas se relacionam pelas colunas Produtor e CPF.")
    return " ".join(linhas)

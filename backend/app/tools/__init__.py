"""Registry das tools do agente.

Contrato de cada módulo de tool:
- DECLARATIONS: lista de declarações no formato da Interactions API
  ({"type": "function", "name": ..., "description": ..., "parameters": {...}})
- FUNCTIONS: dict nome -> callable; o callable recebe os argumentos da
  function call como kwargs e retorna um objeto serializável em JSON.
  Erros esperados devem virar {"erro": "..."} para o modelo explicar ao
  usuário; erros inesperados são capturados pelo loop do agente.

Para adicionar uma tool nova: criar o módulo com DECLARATIONS/FUNCTIONS e
somá-lo nas linhas abaixo (nomes de função precisam ser únicos entre módulos).
"""
from . import calendar_agenda, geocodificacao, propriedades, sheets, windy

TOOL_DECLARATIONS = [
    *sheets.DECLARATIONS,
    *propriedades.DECLARATIONS,
    *geocodificacao.DECLARATIONS,
    *windy.DECLARATIONS,
    *calendar_agenda.DECLARATIONS,
]
TOOL_FUNCTIONS = {
    **sheets.FUNCTIONS,
    **propriedades.FUNCTIONS,
    **geocodificacao.FUNCTIONS,
    **windy.FUNCTIONS,
    **calendar_agenda.FUNCTIONS,
}

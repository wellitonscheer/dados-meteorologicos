"""Tool de consulta ao Google Calendar (somente leitura, service account).

Reaproveita a MESMA credencial de service account do Sheets. A agenda alvo
precisa estar compartilhada com o e-mail da conta de serviço (permissão de
leitura) e ter seu ID configurado em GOOGLE_CALENDAR_ID.
"""
import datetime
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import GOOGLE_CALENDAR_ID, GOOGLE_SHEETS_CREDENTIALS_FILE

# Escopo mais restrito que ainda lista eventos (não expõe config do calendário).
SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]
FUSO = ZoneInfo("America/Sao_Paulo")

DIAS_MAXIMO = 60  # teto da janela de busca
RESULTADOS_MAXIMO = 50  # teto de eventos p/ não estourar o contexto do modelo

# Serviço criado sob demanda e cacheado: a falta da credencial não pode
# quebrar o import do app (o erro aparece só quando o modelo usa a tool).
_service = None

_ERRO_CREDENCIAL = (
    "Arquivo de credenciais da conta de serviço não encontrado em "
    f"'{GOOGLE_SHEETS_CREDENTIALS_FILE}'. Avise o administrador do sistema."
)
_ERRO_SEM_CALENDARIO = (
    "Nenhuma agenda configurada (GOOGLE_CALENDAR_ID vazio). "
    "Avise o administrador do sistema."
)
_ERRO_ACESSO = (
    "Agenda não encontrada ou sem permissão de acesso. Verifique se o "
    "GOOGLE_CALENDAR_ID está correto e se a agenda foi compartilhada, com "
    "permissão de leitura, com a conta de serviço "
    "dados-sheets@camera-dados-meteorologicos.iam.gserviceaccount.com."
)


def _servico():
    global _service
    if _service is None:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES
        )
        # cache_discovery=False evita o warning de file_cache com google-auth.
        _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _service


def listar_eventos(dias: int = 7, max_resultados: int = 20):
    """Lista os próximos eventos da agenda entre agora e agora + `dias`."""
    if not GOOGLE_CALENDAR_ID:
        return {"erro": _ERRO_SEM_CALENDARIO}

    dias = max(1, min(int(dias), DIAS_MAXIMO))
    max_resultados = max(1, min(int(max_resultados), RESULTADOS_MAXIMO))

    agora = datetime.datetime.now(FUSO)  # tz-aware -> isoformat com offset
    time_min = agora.isoformat()  # ex.: 2026-07-08T09:00:00-03:00
    time_max = (agora + datetime.timedelta(days=dias)).isoformat()

    try:
        service = _servico()
    except FileNotFoundError:
        return {"erro": _ERRO_CREDENCIAL}

    eventos = []
    page_token = None
    try:
        while len(eventos) < max_resultados:
            resp = (
                service.events()
                .list(
                    calendarId=GOOGLE_CALENDAR_ID,  # nunca 'primary' com service account
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,  # expande recorrências
                    orderBy="startTime",  # exige singleEvents=True
                    maxResults=min(250, max_resultados - len(eventos)),
                    pageToken=page_token,
                    timeZone="America/Sao_Paulo",
                )
                .execute()
            )
            for ev in resp.get("items", []):
                inicio, fim = ev.get("start", {}), ev.get("end", {})
                eventos.append(
                    {
                        "titulo": ev.get("summary", "(sem título)"),
                        # com hora -> dateTime; dia inteiro -> date (YYYY-MM-DD)
                        "inicio": inicio.get("dateTime", inicio.get("date")),
                        "fim": fim.get("dateTime", fim.get("date")),
                        "dia_inteiro": "date" in inicio,
                        "local": ev.get("location"),
                        "link": ev.get("htmlLink"),
                        "status": ev.get("status"),
                    }
                )
                if len(eventos) >= max_resultados:
                    break
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    except HttpError as exc:
        if exc.resp.status in (403, 404):
            return {"erro": _ERRO_ACESSO}
        return {"erro": f"Falha na Google Calendar API (HTTP {exc.resp.status})."}

    return {
        "calendario": GOOGLE_CALENDAR_ID,
        "fuso": str(FUSO),
        "janela_dias": dias,
        "total_eventos": len(eventos),
        "eventos": eventos,
    }


DECLARATIONS = [
    {
        "type": "function",
        "name": "listar_eventos",
        "description": (
            "Lista os próximos compromissos/eventos da agenda do Google Calendar "
            "configurada, do momento atual até 'dias' à frente, em ordem "
            "cronológica. Cada evento traz título, início, fim, se é de dia "
            "inteiro (nesse caso 'fim' é exclusivo — o dia seguinte ao último), "
            "local, link e status (fuso America/Sao_Paulo). Use para perguntas "
            "sobre agenda, compromissos, reuniões, prazos e datas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "dias": {
                    "type": "integer",
                    "description": (
                        f"Janela de dias a partir de agora (padrão 7, teto {DIAS_MAXIMO})."
                    ),
                },
                "max_resultados": {
                    "type": "integer",
                    "description": (
                        f"Máximo de eventos a retornar (padrão 20, teto {RESULTADOS_MAXIMO})."
                    ),
                },
            },
        },
    },
]

FUNCTIONS = {"listar_eventos": listar_eventos}

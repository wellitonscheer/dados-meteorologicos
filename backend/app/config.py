import os

# URL de conexão do Postgres. O default aponta para o serviço "db" do docker-compose.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/app",
)

# Ambiente de execução: "development" (default) ou "production". Em produção o
# app exige segredos fortes no startup (ver validar_producao no fim do arquivo).
APP_ENV = os.getenv("APP_ENV", "development")
IS_PROD = APP_ENV == "production"

# Chave para assinar os tokens JWT. Em produção deve vir do ambiente.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Origem do frontend liberada no CORS.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Hosts aceitos no header Host (TrustedHostMiddleware). Em produção, o domínio
# público do túnel. Lista separada por vírgula; "*" (default) libera todos.
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]

# Usuário semeado no startup.
SEED_USERNAME = os.getenv("SEED_USERNAME", "admin")
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "admin")

# Integração com Google Sheets (tools do agente). O JSON da conta de serviço é
# montado no container pelo docker-compose (read-only) — nunca commitá-lo.
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_SHEETS_CREDENTIALS_FILE",
    "/secrets/google-service-account.json",
)
GOOGLE_SHEETS_SPREADSHEET_NAME = os.getenv(
    "GOOGLE_SHEETS_SPREADSHEET_NAME",
    "Dados Climáticos por Produtor",
)
# Nome da aba (worksheet) lida pelo agente. Fixo por configuração para o modelo
# não precisar descobri-lo — evita uma chamada extra ao modelo por consulta.
GOOGLE_SHEETS_WORKSHEET_NAME = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Sheet1")

# Segunda planilha: produtores e suas propriedades (dados cadastrais, cultura e
# coordenadas exatas). Usa a MESMA conta de serviço/credencial da planilha de
# clima — a planilha precisa estar compartilhada com essa conta.
GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME = os.getenv(
    "GOOGLE_SHEETS_PROPRIEDADES_SPREADSHEET_NAME",
    "Produtores Propriedades",
)
GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME = os.getenv(
    "GOOGLE_SHEETS_PROPRIEDADES_WORKSHEET_NAME",
    "Sheet1",
)

# Chave da Point Forecast API do Windy (tool de previsão do tempo).
WINDY_API_KEY = os.getenv("WINDY_API_KEY", "")

# Agenda do Google Calendar lida pela tool do agente (reutiliza a MESMA
# credencial de service account do Sheets). Vazio = tool responde erro amigável.
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")


# Valores que jamais podem ir a produção (defaults de desenvolvimento).
_SECRET_KEYS_INSEGURAS = {"", "dev-secret-change-me"}
_SENHAS_SEED_INSEGURAS = {"", "admin"}


def validar_producao() -> None:
    """Aborta o startup se, em APP_ENV=production, segredos ainda estiverem nos
    defaults inseguros. Em desenvolvimento não faz nada (admin/admin continua ok)."""
    if not IS_PROD:
        return
    erros = []
    if SECRET_KEY in _SECRET_KEYS_INSEGURAS:
        erros.append(
            "SECRET_KEY está no default inseguro — gere uma forte: "
            "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    if SEED_PASSWORD in _SENHAS_SEED_INSEGURAS:
        erros.append("SEED_PASSWORD está no default (admin) — defina uma senha forte.")
    if erros:
        raise RuntimeError(
            "Configuração insegura para APP_ENV=production:\n  - " + "\n  - ".join(erros)
        )

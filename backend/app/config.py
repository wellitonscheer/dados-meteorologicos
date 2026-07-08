import os

# URL de conexão do Postgres. O default aponta para o serviço "db" do docker-compose.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/app",
)

# Chave para assinar os tokens JWT. Em produção deve vir do ambiente.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Origem do frontend liberada no CORS.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

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

# Chave da Point Forecast API do Windy (tool de previsão do tempo).
WINDY_API_KEY = os.getenv("WINDY_API_KEY", "")

# Agenda do Google Calendar lida pela tool do agente (reutiliza a MESMA
# credencial de service account do Sheets). Vazio = tool responde erro amigável.
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

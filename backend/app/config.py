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

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .config import ALLOWED_HOSTS, FRONTEND_ORIGIN, IS_PROD, validar_producao
from .database import Base, SessionLocal, engine
from .logging_config import configurar_logging
from .ratelimit import limiter
from .routers import auth, chat
from .seed import seed_default_user

configurar_logging()
logger = logging.getLogger("app.startup")


def wait_for_db(max_tries: int = 30, delay: float = 1.0) -> None:
    """Espera o Postgres aceitar conexões (ele pode subir depois do backend)."""
    for attempt in range(1, max_tries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            logger.warning("banco indisponível, tentativa %d/%d...", attempt, max_tries)
            time.sleep(delay)
    raise RuntimeError("Não foi possível conectar ao banco de dados")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validar_producao()  # aborta se segredos default em APP_ENV=production
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_user(db)
    finally:
        db.close()
    logger.info("pronto")
    yield


# Em produção, fecha a documentação interativa (Swagger/ReDoc/OpenAPI).
_docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None} if IS_PROD else {}
app = FastAPI(title="CRUD simples - Login e Chat", lifespan=lifespan, **_docs_kwargs)

# Rate limiting (slowapi): o decorator @limiter.limit nas rotas levanta
# RateLimitExceeded, tratado aqui como 429.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Só aceita requests cujo Host esteja na allowlist (no-op quando ALLOWED_HOSTS=["*"]).
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    """Headers de segurança básicos em toda resposta."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if IS_PROD:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

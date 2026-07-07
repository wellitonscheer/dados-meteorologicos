import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .config import FRONTEND_ORIGIN
from .database import Base, SessionLocal, engine
from .routers import auth, chat
from .seed import seed_default_user


def wait_for_db(max_tries: int = 30, delay: float = 1.0) -> None:
    """Espera o Postgres aceitar conexões (ele pode subir depois do backend)."""
    for attempt in range(1, max_tries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            print(f"[startup] banco indisponível, tentativa {attempt}/{max_tries}...")
            time.sleep(delay)
    raise RuntimeError("Não foi possível conectar ao banco de dados")


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_user(db)
    finally:
        db.close()
    print("[startup] pronto")
    yield


app = FastAPI(title="CRUD simples - Login e Chat", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

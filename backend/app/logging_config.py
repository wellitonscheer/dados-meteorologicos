"""Configuração central de logging: arquivo persistente + console.

Grava em LOG_DIR (default /logs, montado no host via docker-compose em ./logs),
para os logs sobreviverem a restarts e serem fáceis de ver (basta abrir
./logs/backend.log ou rodar `tail -f logs/backend.log`). O mesmo formato vai
para o stdout, então `docker compose logs backend` continua funcionando.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.getenv("LOG_DIR", "/logs")
LOG_FILE = os.path.join(LOG_DIR, "backend.log")
_FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Loggers do uvicorn espelhados no arquivo (inclui a linha de acesso do 502).
# Só os filhos que emitem de fato — anexar também no pai "uvicorn" duplicaria
# cada registro de "uvicorn.error" (ele propaga para o pai).
_LOGGERS_UVICORN = ("uvicorn.error", "uvicorn.access")


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Instala handlers de arquivo (rotativo) e console. Idempotente."""
    os.makedirs(LOG_DIR, exist_ok=True)
    formatter = logging.Formatter(_FORMATO)

    root = logging.getLogger()
    root.setLevel(nivel)
    # O --reload reimporta o módulo; não duplicar handlers no mesmo processo.
    if any(getattr(h, "_app_handler", False) for h in root.handlers):
        return

    arquivo = RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    arquivo.setFormatter(formatter)
    arquivo._app_handler = True  # marca p/ o guard acima

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console._app_handler = True

    root.addHandler(arquivo)
    root.addHandler(console)

    # Manda os logs do uvicorn para o MESMO arquivo (handler compartilhado).
    for nome in _LOGGERS_UVICORN:
        logging.getLogger(nome).addHandler(arquivo)

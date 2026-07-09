"""Rate limiting compartilhado (slowapi). O limiter fica num módulo próprio para
main.py e os routers importarem sem ciclo de import."""

from fastapi import Request
from slowapi import Limiter


def _client_ip(request: Request) -> str:
    """IP do cliente para a chave do rate limit. Atrás de um túnel/proxy, o IP
    real vem num header encaminhado (Cloudflare usa CF-Connecting-IP; genérico é
    o 1º de X-Forwarded-For). Sem proxy, cai no request.client."""
    encaminhado = request.headers.get("cf-connecting-ip") or request.headers.get(
        "x-forwarded-for", ""
    )
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "anonimo"


limiter = Limiter(key_func=_client_ip)

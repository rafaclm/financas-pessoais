"""
Middleware global de autenticacao.
Protege TODAS as rotas /api/v1/* exceto as publicas.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from app.services.auth import decodificar_token


# Rotas que NAO exigem autenticacao (publicas)
ROTAS_PUBLICAS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/",
    "/health",
}


def eh_rota_publica(path: str) -> bool:
    """Retorna True se a rota NAO exige autenticacao."""
    # Rotas exatas
    if path in ROTAS_PUBLICAS:
        return True
    # Rotas que começam com prefixo publico
    prefixos_publicos = ["/docs", "/openapi", "/redoc"]
    for prefixo in prefixos_publicos:
        if path.startswith(prefixo):
            return True
    return False


async def middleware_auth(request: Request, call_next):
    """
    Middleware que valida token JWT em todas as rotas privadas.
    Deixa passar apenas rotas publicas (login, register, docs).
    """
    path = request.url.path

    # Rotas publicas — deixa passar sem validar
    if eh_rota_publica(path):
        return await call_next(request)

    # OPTIONS (CORS preflight) — deixa passar
    if request.method == "OPTIONS":
        return await call_next(request)

    # Valida token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning(f"Requisicao sem token: {request.method} {path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Token de autenticacao ausente"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.replace("Bearer ", "")
    try:
        payload = decodificar_token(token)
        # Injeta usuario_id no request (para uso opcional nos endpoints)
        request.state.usuario_id = int(payload.get("sub"))
        request.state.email = payload.get("email")
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers or {},
        )
    except Exception as e:
        logger.error(f"Erro ao validar token: {e}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Token invalido"},
        )

    # Token valido — continua
    return await call_next(request)
"""
Middleware global de autenticacao.
Protege TODAS as rotas /api/v1/* exceto as publicas.
Inclui headers CORS nas respostas de erro (senao o navegador
mostra 'CORS error' ao inves de '401 - faca login').
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from app.core.config import settings
from app.services.auth import decodificar_token


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
    if path in ROTAS_PUBLICAS:
        return True
    prefixos_publicos = ["/docs", "/openapi", "/redoc"]
    for prefixo in prefixos_publicos:
        if path.startswith(prefixo):
            return True
    return False


def _resposta_erro_com_cors(request: Request, status_code: int, detail: str) -> JSONResponse:
    """
    Cria resposta de erro JA COM headers CORS.
    Isso evita que o navegador mostre 'CORS error' quando na
    verdade e um 401 (token expirado/ausente).
    """
    origin = request.headers.get("origin", "")
    headers = {
        "WWW-Authenticate": "Bearer",
    }
    # Se a origem esta na lista permitida, adiciona headers CORS
    if origin in settings.cors_list:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=headers,
    )


async def middleware_auth(request: Request, call_next):
    """Middleware que valida token JWT em todas as rotas privadas."""
    path = request.url.path

    if eh_rota_publica(path):
        return await call_next(request)

    if request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning(f"Requisicao sem token: {request.method} {path}")
        return _resposta_erro_com_cors(
            request, status.HTTP_401_UNAUTHORIZED,
            "Token de autenticacao ausente"
        )

    token = auth_header.replace("Bearer ", "")
    try:
        payload = decodificar_token(token)
        request.state.usuario_id = int(payload.get("sub"))
        request.state.email = payload.get("email")
    except HTTPException as e:
        return _resposta_erro_com_cors(
            request, e.status_code, e.detail
        )
    except Exception as e:
        logger.error(f"Erro ao validar token: {e}")
        return _resposta_erro_com_cors(
            request, status.HTTP_401_UNAUTHORIZED,
            "Token invalido"
        )

    return await call_next(request)
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.auth import decodificar_token, obter_usuario_por_id
from app.infrastructure.db.models import Usuario


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_usuario_logado(
    db: DbSession,
    token: str | None = Depends(oauth2_scheme)
) -> Usuario:
    """Dependencia que exige autenticacao. Retorna o Usuario logado."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decodificar_token(token)
    usuario_id = int(payload.get("sub"))
    usuario = obter_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado",
        )
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )
    return usuario


UsuarioLogado = Annotated[Usuario, Depends(get_usuario_logado)]
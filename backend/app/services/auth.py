"""
Service de autenticacao com JWT + bcrypt.
"""
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from loguru import logger
from app.core.config import settings
from app.infrastructure.db.models import Usuario


def gerar_hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha (irreversivel)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Verifica se a senha bate com o hash."""
    try:
        return bcrypt.checkpw(
            senha.encode("utf-8"),
            hash_armazenado.encode("utf-8")
        )
    except Exception:
        return False


def criar_token(usuario_id: int, email: str) -> tuple:
    """Cria token JWT com validade configurada."""
    expira_em_dias = settings.jwt_expire_days
    exp = datetime.now(timezone.utc) + timedelta(days=expira_em_dias)
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "exp": exp,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expira_em_dias


def decodificar_token(token: str) -> dict:
    """Decodifica JWT. Lanca HTTPException se invalido."""
    try:
        payload = jwt.decode(
            token, settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token invalido: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def registrar_usuario(
    db: Session, email: str, nome: str, senha: str, codigo_cadastro: str
) -> Usuario:
    """Cria um novo usuario. Valida codigo de cadastro."""
    if not settings.codigo_cadastro:
        raise HTTPException(
            status_code=500,
            detail="Sistema mal configurado (CODIGO_CADASTRO nao definido)"
        )
    if codigo_cadastro != settings.codigo_cadastro:
        logger.warning(f"Tentativa de cadastro com codigo invalido: {email}")
        raise HTTPException(status_code=403, detail="Codigo de cadastro invalido")

    existe = db.scalar(select(Usuario).where(Usuario.email == email.lower()))
    if existe:
        raise HTTPException(status_code=409, detail="E-mail ja cadastrado")

    total_usuarios = db.scalar(select(Usuario.id).limit(1))
    eh_primeiro = total_usuarios is None

    novo = Usuario(
        email=email.lower(),
        nome=nome,
        senha_hash=gerar_hash_senha(senha),
        ativo=True,
        admin=eh_primeiro,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    logger.info(f"Novo usuario registrado: {email} (admin: {eh_primeiro})")
    return novo


def autenticar_usuario(db: Session, email: str, senha: str) -> Usuario:
    """Autentica usuario. Retorna o objeto Usuario ou lanca HTTPException."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == email.lower()))
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha invalidos")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Conta desativada")

    if not verificar_senha(senha, usuario.senha_hash):
        logger.warning(f"Senha invalida para: {email}")
        raise HTTPException(status_code=401, detail="E-mail ou senha invalidos")

    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(usuario)
    logger.info(f"Login bem-sucedido: {email}")
    return usuario


def obter_usuario_por_id(db: Session, usuario_id: int):
    """Busca usuario pelo ID. Retorna Usuario ou None."""
    return db.get(Usuario, usuario_id)


def alterar_senha(
    db: Session, usuario: Usuario, senha_atual: str, senha_nova: str
) -> None:
    """Altera a senha do usuario logado."""
    if not verificar_senha(senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")

    usuario.senha_hash = gerar_hash_senha(senha_nova)
    db.commit()
    logger.info(f"Senha alterada para: {usuario.email}")
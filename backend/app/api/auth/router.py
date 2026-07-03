from fastapi import APIRouter, Depends, status
from app.api.deps import DbSession, UsuarioLogado
from app.schemas.auth import (
    RegisterPayload, LoginPayload, TokenResposta,
    UsuarioOut, TrocarSenhaPayload
)
from app.services.auth import (
    registrar_usuario, autenticar_usuario,
    criar_token, alterar_senha
)

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


@router.post("/register", response_model=TokenResposta,
             status_code=status.HTTP_201_CREATED)
def register(payload: RegisterPayload, db: DbSession):
    """Registra um novo usuario. Requer codigo de cadastro."""
    usuario = registrar_usuario(
        db, payload.email, payload.nome, payload.senha, payload.codigo_cadastro
    )
    token, dias = criar_token(usuario.id, usuario.email)
    return TokenResposta(
        access_token=token,
        expires_in_days=dias,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post("/login", response_model=TokenResposta)
def login(payload: LoginPayload, db: DbSession):
    """Autentica usuario e retorna JWT."""
    usuario = autenticar_usuario(db, payload.email, payload.senha)
    token, dias = criar_token(usuario.id, usuario.email)
    return TokenResposta(
        access_token=token,
        expires_in_days=dias,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioOut)
def obter_perfil(usuario: UsuarioLogado):
    """Retorna dados do usuario logado."""
    return usuario


@router.post("/alterar-senha", status_code=status.HTTP_204_NO_CONTENT)
def trocar_senha(
    payload: TrocarSenhaPayload,
    db: DbSession,
    usuario: UsuarioLogado,
):
    """Altera a senha do usuario logado."""
    alterar_senha(db, usuario, payload.senha_atual, payload.senha_nova)
from datetime import datetime
from pydantic import EmailStr, Field, field_validator
from app.schemas.common import ORMBase, TimestampSchema


class UsuarioBase(ORMBase):
    email: EmailStr
    nome: str = Field(min_length=2, max_length=100)


class RegisterPayload(UsuarioBase):
    senha: str = Field(min_length=8)
    codigo_cadastro: str = Field(min_length=1)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no minimo 8 caracteres")
        if not any(c.isalpha() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 letra")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 numero")
        return v


class LoginPayload(ORMBase):
    email: EmailStr
    senha: str


class TrocarSenhaPayload(ORMBase):
    senha_atual: str
    senha_nova: str = Field(min_length=8)

    @field_validator("senha_nova")
    @classmethod
    def validar_senha_nova(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no minimo 8 caracteres")
        if not any(c.isalpha() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 letra")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 numero")
        return v


class UsuarioOut(UsuarioBase, TimestampSchema):
    id: int
    ativo: bool
    admin: bool
    ultimo_login: datetime | None = None


class TokenResposta(ORMBase):
    access_token: str
    token_type: str = "bearer"
    expires_in_days: int
    usuario: UsuarioOut
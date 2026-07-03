from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class InstituicaoBase(ORMBase):
    nome: str = Field(min_length=1, max_length=80)
    tipo: str = Field(pattern="^(banco|corretora|exchange|outro)$")
    pais: str = Field(default="BR", min_length=2, max_length=2)


class InstituicaoCreate(InstituicaoBase):
    pass


class InstituicaoUpdate(ORMBase):
    nome: str | None = None
    tipo: str | None = None
    pais: str | None = None
    ativo: int | None = None


class InstituicaoOut(InstituicaoBase, TimestampSchema):
    id: int
    ativo: int
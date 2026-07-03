from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class ContaBase(ORMBase):
    nome: str = Field(min_length=1, max_length=80)
    instituicao_id: int
    tipo: str = Field(default="corrente", pattern="^(corrente|investimento|internacional|outro)$")
    moeda: str = Field(default="BRL", pattern="^(BRL|USD)$")


class ContaCreate(ContaBase):
    pass


class ContaUpdate(ORMBase):
    nome: str | None = None
    instituicao_id: int | None = None
    tipo: str | None = None
    moeda: str | None = None
    ativo: int | None = None


class ContaOut(ContaBase, TimestampSchema):
    id: int
    ativo: int
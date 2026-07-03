from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class PagamentoCartaoBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    cartao_id: int
    conta_id: int
    valor: float = Field(gt=0)
    descricao: str | None = None


class PagamentoCartaoCreate(PagamentoCartaoBase):
    pass


class PagamentoCartaoUpdate(ORMBase):
    ano_id: int | None = None
    mes: int | None = Field(default=None, ge=1, le=12)
    cartao_id: int | None = None
    conta_id: int | None = None
    valor: float | None = Field(default=None, gt=0)
    descricao: str | None = None


class PagamentoCartaoOut(PagamentoCartaoBase, TimestampSchema):
    id: int
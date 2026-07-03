from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class CartaoBase(ORMBase):
    nome: str = Field(min_length=1, max_length=80)
    instituicao_id: int
    conta_pagamento_id: int | None = None
    dia_fechamento: int = Field(ge=1, le=31)
    dia_vencimento: int = Field(ge=1, le=31)


class CartaoCreate(CartaoBase):
    pass


class CartaoUpdate(ORMBase):
    nome: str | None = None
    instituicao_id: int | None = None
    conta_pagamento_id: int | None = None
    dia_fechamento: int | None = None
    dia_vencimento: int | None = None
    ativo: int | None = None


class CartaoOut(CartaoBase, TimestampSchema):
    id: int
    ativo: int
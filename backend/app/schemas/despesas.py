from pydantic import Field, model_validator
from app.schemas.common import ORMBase, TimestampSchema


class DespesaBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    categoria_id: int
    origem_tipo: str = Field(pattern="^(conta|cartao)$")
    conta_id: int | None = None
    cartao_id: int | None = None
    valor: float = Field(gt=0)
    descricao: str | None = None
    recorrente: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def validar_origem(self):
        if self.origem_tipo == "conta" and not self.conta_id:
            raise ValueError("Quando origem_tipo='conta', conta_id é obrigatório")
        if self.origem_tipo == "cartao" and not self.cartao_id:
            raise ValueError("Quando origem_tipo='cartao', cartao_id é obrigatório")
        return self


class DespesaCreate(DespesaBase):
    pass


class DespesaUpdate(ORMBase):
    ano_id: int | None = None
    mes: int | None = Field(default=None, ge=1, le=12)
    categoria_id: int | None = None
    origem_tipo: str | None = None
    conta_id: int | None = None
    cartao_id: int | None = None
    valor: float | None = Field(default=None, gt=0)
    descricao: str | None = None
    recorrente: int | None = None


class DespesaOut(DespesaBase, TimestampSchema):
    id: int
    auto_pagamento_cartao: int = 0
    pagamento_cartao_id: int | None = None
    replicado_de_id: int | None = None
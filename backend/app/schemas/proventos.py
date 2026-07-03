from datetime import date
from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class ProventoBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    data: date
    ativo_id: int
    tipo: str = Field(pattern="^(dividendo|jcp|rendimento|juros_cripto|outro)$")
    valor_bruto: float = Field(gt=0)
    valor_liquido: float = Field(gt=0)
    moeda: str = Field(pattern="^(BRL|USD)$")
    cotacao_usd_brl: float | None = Field(default=None, gt=0)
    conta_id: int | None = None
    descricao: str | None = None
    # 🆕 Quantidade de cotas (opcional)
    quantidade_cotas: float | None = Field(default=None, gt=0)


class ProventoCreate(ProventoBase):
    pass


class ProventoUpdate(ORMBase):
    ano_id: int | None = None
    mes: int | None = Field(default=None, ge=1, le=12)
    data: date | None = None
    ativo_id: int | None = None
    tipo: str | None = None
    valor_bruto: float | None = Field(default=None, gt=0)
    valor_liquido: float | None = Field(default=None, gt=0)
    moeda: str | None = None
    cotacao_usd_brl: float | None = None
    conta_id: int | None = None
    descricao: str | None = None
    quantidade_cotas: float | None = None


class ProventoOut(ProventoBase, TimestampSchema):
    id: int
    valor_liquido_brl: float
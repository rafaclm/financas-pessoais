from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class SaldoContaBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    conta_id: int
    saldo: float = Field(ge=0)
    cotacao_usd_brl: float | None = Field(default=None, gt=0)


class SaldoContaCreate(SaldoContaBase):
    pass


class SaldoContaUpdate(ORMBase):
    saldo: float | None = Field(default=None, ge=0)
    cotacao_usd_brl: float | None = None


class SaldoContaOut(SaldoContaBase, TimestampSchema):
    id: int
    saldo_brl: float
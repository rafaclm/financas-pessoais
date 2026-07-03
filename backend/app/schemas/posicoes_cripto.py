from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class PosicaoCriptoBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    ativo_id: int
    quantidade: float = Field(ge=0)
    saldo_brl: float = Field(ge=0)
    cotacao_usd_brl: float | None = Field(default=None, gt=0)


class PosicaoCriptoCreate(PosicaoCriptoBase):
    pass


class PosicaoCriptoUpdate(ORMBase):
    quantidade: float | None = Field(default=None, ge=0)
    saldo_brl: float | None = Field(default=None, ge=0)
    cotacao_usd_brl: float | None = None


class PosicaoCriptoOut(PosicaoCriptoBase, TimestampSchema):
    id: int
    saldo_usd: float
    variacao_pct: float | None = None
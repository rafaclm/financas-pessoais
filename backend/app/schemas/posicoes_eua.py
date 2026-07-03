from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class PosicaoEUABase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    ativo_id: int
    quantidade: float = Field(ge=0)
    preco_medio_usd: float = Field(ge=0)
    cotacao_fechamento_usd: float = Field(ge=0)
    cotacao_usd_brl: float | None = Field(default=None, gt=0)


class PosicaoEUACreate(PosicaoEUABase):
    pass


class PosicaoEUAUpdate(ORMBase):
    quantidade: float | None = Field(default=None, ge=0)
    preco_medio_usd: float | None = Field(default=None, ge=0)
    cotacao_fechamento_usd: float | None = Field(default=None, ge=0)
    cotacao_usd_brl: float | None = None


class PosicaoEUAOut(PosicaoEUABase, TimestampSchema):
    id: int
    valor_total_usd: float
    valor_total_brl: float
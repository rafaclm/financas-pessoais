from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class PosicaoBRBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    ativo_id: int
    quantidade: float = Field(ge=0)
    preco_medio: float = Field(ge=0)
    cotacao_fechamento: float = Field(ge=0)


class PosicaoBRCreate(PosicaoBRBase):
    pass


class PosicaoBRUpdate(ORMBase):
    quantidade: float | None = Field(default=None, ge=0)
    preco_medio: float | None = Field(default=None, ge=0)
    cotacao_fechamento: float | None = Field(default=None, ge=0)


class PosicaoBROut(PosicaoBRBase, TimestampSchema):
    id: int
    valor_total: float


class PrecoMedioSugerido(ORMBase):
    ativo_id: int
    quantidade_acumulada: float
    preco_medio_sugerido: float
    total_aportes: int
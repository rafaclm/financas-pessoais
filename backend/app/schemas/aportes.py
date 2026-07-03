from datetime import date
from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class AporteBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    data: date
    ativo_id: int
    tipo_operacao: str = Field(pattern="^(compra|venda)$")
    quantidade: float = Field(gt=0)
    preco_unitario: float = Field(gt=0)
    taxas: float = Field(default=0, ge=0)
    moeda: str = Field(pattern="^(BRL|USD)$")
    # 🆕 Conta opcional
    conta_id: int | None = None
    descricao: str | None = None
    cotacao_usd_brl: float | None = Field(default=None, gt=0)


class AporteCreate(AporteBase):
    pass


class AporteUpdate(ORMBase):
    ano_id: int | None = None
    mes: int | None = Field(default=None, ge=1, le=12)
    data: date | None = None
    ativo_id: int | None = None
    tipo_operacao: str | None = None
    quantidade: float | None = Field(default=None, gt=0)
    preco_unitario: float | None = Field(default=None, gt=0)
    taxas: float | None = Field(default=None, ge=0)
    moeda: str | None = None
    cotacao_usd_brl: float | None = None
    conta_id: int | None = None
    descricao: str | None = None


class AporteOut(AporteBase, TimestampSchema):
    id: int
    valor_total: float
    valor_total_brl: float
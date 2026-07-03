from datetime import date
from pydantic import Field, computed_field
from app.schemas.common import ORMBase, TimestampSchema


class CombustivelBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    data: date  # 🆕 Data do abastecimento (obrigatório)
    litros: float = Field(gt=0)
    valor_total: float = Field(gt=0)
    posto: str | None = None
    veiculo: str | None = None
    conta_id: int | None = None
    cartao_id: int | None = None


class CombustivelCreate(CombustivelBase):
    pass


class CombustivelUpdate(ORMBase):
    ano_id: int | None = None
    mes: int | None = Field(default=None, ge=1, le=12)
    data: date | None = None
    litros: float | None = Field(default=None, gt=0)
    valor_total: float | None = Field(default=None, gt=0)
    posto: str | None = None
    veiculo: str | None = None
    conta_id: int | None = None
    cartao_id: int | None = None


class CombustivelOut(CombustivelBase, TimestampSchema):
    id: int

    @computed_field
    @property
    def preco_litro(self) -> float:
        return round(self.valor_total / self.litros, 4) if self.litros else 0
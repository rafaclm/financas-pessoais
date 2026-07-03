from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class AnoBase(ORMBase):
    ano: int = Field(ge=1900, le=2100)
    saldo_inicial: float = 0
    observacao: str | None = None


class AnoCreate(AnoBase):
    pass


class AnoUpdate(ORMBase):
    saldo_inicial: float | None = None
    observacao: str | None = None
    ativo: int | None = None


class AnoOut(AnoBase, TimestampSchema):
    id: int
    ativo: int
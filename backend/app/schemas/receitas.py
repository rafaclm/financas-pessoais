from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class ReceitaBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    categoria_id: int
    conta_id: int
    valor: float = Field(gt=0)
    descricao: str | None = None
    recorrente: int = Field(default=0, ge=0, le=1)


class ReceitaCreate(ReceitaBase):
    pass


class ReceitaUpdate(ORMBase):
    ano_id: int | None = None
    mes: int | None = Field(default=None, ge=1, le=12)
    categoria_id: int | None = None
    conta_id: int | None = None
    valor: float | None = Field(default=None, gt=0)
    descricao: str | None = None
    recorrente: int | None = None


class ReceitaOut(ReceitaBase, TimestampSchema):
    id: int
    replicado_de_id: int | None = None
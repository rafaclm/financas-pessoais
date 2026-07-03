from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class ProdutoBase(ORMBase):
    nome: str = Field(min_length=1, max_length=120)
    categoria: str = Field(pattern="^(renda_fixa|previdencia|fgts|fundo|outro)$")
    instituicao_id: int
    moeda: str = Field(default="BRL", pattern="^(BRL|USD)$")


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(ORMBase):
    nome: str | None = None
    categoria: str | None = None
    instituicao_id: int | None = None
    moeda: str | None = None
    ativo: int | None = None


class ProdutoOut(ProdutoBase, TimestampSchema):
    id: int
    ativo: int
from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


# ===== Despesas =====
class CategoriaDespesaBase(ORMBase):
    nome: str = Field(min_length=1, max_length=60)
    tipo: str = Field(default="variavel", pattern="^(fixa|variavel)$")
    essencial: int = Field(default=0, ge=0, le=1)
    cor: str | None = Field(default="#888888", max_length=7)
    icone: str | None = None


class CategoriaDespesaCreate(CategoriaDespesaBase):
    pass


class CategoriaDespesaUpdate(ORMBase):
    nome: str | None = None
    tipo: str | None = None
    essencial: int | None = None
    cor: str | None = None
    icone: str | None = None
    ativo: int | None = None


class CategoriaDespesaOut(CategoriaDespesaBase, TimestampSchema):
    id: int
    ativo: int


# ===== Receitas =====
class CategoriaReceitaBase(ORMBase):
    nome: str = Field(min_length=1, max_length=60)
    recorrencia: str = Field(default="eventual", pattern="^(recorrente|eventual)$")
    cor: str | None = "#28a745"


class CategoriaReceitaCreate(CategoriaReceitaBase):
    pass


class CategoriaReceitaUpdate(ORMBase):
    nome: str | None = None
    recorrencia: str | None = None
    cor: str | None = None
    ativo: int | None = None


class CategoriaReceitaOut(CategoriaReceitaBase, TimestampSchema):
    id: int
    ativo: int
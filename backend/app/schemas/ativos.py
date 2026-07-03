from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class AtivoBase(ORMBase):
    ticker: str = Field(min_length=1, max_length=20)
    nome: str = Field(min_length=1, max_length=120)
    tipo: str = Field(pattern="^(acao_br|bdr|fii|fiagro|etf_br|acao_eua|etf_eua|reit|cripto)$")
    mercado: str = Field(pattern="^(B3|NYSE|NASDAQ|CRIPTO)$")
    geografia: str = Field(pattern="^(BR|EUA|GLOBAL)$")
    classe: str = Field(pattern="^(acao|etf|fii|fiagro|reit|cripto)$")
    moeda: str = Field(pattern="^(BRL|USD)$")
    setor: str | None = None


class AtivoCreate(AtivoBase):
    pass


class AtivoUpdate(ORMBase):
    ticker: str | None = None
    nome: str | None = None
    tipo: str | None = None
    mercado: str | None = None
    geografia: str | None = None
    classe: str | None = None
    moeda: str | None = None
    setor: str | None = None
    ativo: int | None = None


class AtivoOut(AtivoBase, TimestampSchema):
    id: int
    ativo: int
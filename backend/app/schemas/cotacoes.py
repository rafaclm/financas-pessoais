from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class CotacaoCambioBase(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    par: str = Field(default="USDBRL", max_length=7)
    cotacao: float = Field(gt=0)
    fonte: str = Field(default="manual", max_length=40)


class CotacaoCambioCreate(CotacaoCambioBase):
    pass


class CotacaoCambioUpdate(ORMBase):
    cotacao: float | None = Field(default=None, gt=0)
    fonte: str | None = None


class CotacaoCambioOut(CotacaoCambioBase, TimestampSchema):
    id: int


class AtualizarCotacaoBCB(ORMBase):
    """Payload para atualização automática via BCB."""
    ano_id: int
    mes: int = Field(ge=1, le=12)
    par: str = Field(default="USDBRL")
from pydantic import Field
from app.schemas.common import ORMBase


class ReplicarMesAnterior(ORMBase):
    ano_id: int
    mes: int = Field(ge=1, le=12)
    force: bool = False  # sobrescrever se já houver dados


class ResultadoReplicacao(ORMBase):
    replicados: int
    origem_total: int
    mensagem: str
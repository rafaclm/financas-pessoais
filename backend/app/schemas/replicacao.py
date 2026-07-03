from pydantic import Field
from app.schemas.common import ORMBase


class ReplicarLancamentos(ORMBase):
    ano_origem_id: int
    mes_origem: int = Field(ge=1, le=12)
    ano_destino_id: int
    mes_destino: int = Field(ge=1, le=12)
    replicar_receitas: bool = True
    replicar_despesas: bool = True
    apenas_recorrentes: bool = True
    force: bool = False  # sobrescrever se já houver no destino


class ResultadoReplicacao(ORMBase):
    receitas_replicadas: int
    despesas_replicadas: int
    receitas_origem_total: int
    despesas_origem_total: int
    mensagem: str
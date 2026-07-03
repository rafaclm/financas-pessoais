from datetime import datetime
from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


class PosicaoAtualOut(ORMBase):
    id: int
    ativo_id: int
    ticker: str
    nome: str
    geografia: str
    classe: str
    moeda: str

    quantidade: float
    quantidade_comprada_total: float
    quantidade_vendida_total: float
    custo_total: float
    custo_total_brl: float

    preco_medio: float
    preco_medio_calculado: float
    preco_medio_manual: float | None
    preco_medio_eh_manual: int

    cotacao_atual: float | None
    cotacao_atual_data: datetime | None
    cotacao_fonte: str | None
    cotacao_usd_brl: float | None
    valor_atual_brl: float

    # Rentabilidades
    rentabilidade_pct: float | None  # apenas ganho de capital
    rentabilidade_total_pct: float | None  # 🆕 capital + proventos

    # Proventos
    proventos_totais_brl: float
    yield_on_cost_pct: float | None

    # Preco teto
    preco_teto: float | None
    margem_aporte_pct: float | None
    acima_do_teto: bool


class PrecoMedioManualPayload(ORMBase):
    preco_medio_manual: float = Field(gt=0)


class PrecoTetoPayload(ORMBase):
    preco_teto: float = Field(gt=0)


class ResultadoAtualizacaoCotacoes(ORMBase):
    atualizados: int
    falhas: int
    total: int
    mensagem: str
    detalhes: list[dict]


class ResultadoRecalculo(ORMBase):
    ativos_processados: int
    aportes_processados: int
    mensagem: str
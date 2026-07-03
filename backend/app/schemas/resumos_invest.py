from app.schemas.common import ORMBase


class ResumoMensalAportes(ORMBase):
    mes: int
    total_brl: float
    qtd_operacoes: int
    qtd_compras: int
    qtd_vendas: int
    total_compras_brl: float
    total_vendas_brl: float


class ResumoPorAtivo(ORMBase):
    ativo_id: int
    ticker: str
    nome: str
    qtd_operacoes: int
    total_brl: float
    quantidade_acumulada: float | None = None


class ResumoMensalProventos(ORMBase):
    mes: int
    total_brl: float
    qtd: int


class ResumoProventosPorAtivo(ORMBase):
    ativo_id: int
    ticker: str
    nome: str
    qtd: int
    total_brl: float


class ResumoAnualProventos(ORMBase):
    total_acumulado_brl: float
    media_mensal_brl: float
    maior_mes: int | None
    maior_valor: float
    qtd_total: int
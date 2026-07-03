from datetime import datetime
from app.schemas.common import ORMBase


class PontoEvolucao(ORMBase):
    ano: int
    mes: int
    label: str
    patrimonio_total: float


class FatiaCarteira(ORMBase):
    categoria: str
    valor: float
    cor: str


class MesReceitaDespesa(ORMBase):
    label: str
    receitas: float
    despesas: float
    saldo: float


class MesProvento(ORMBase):
    label: str
    total: float


class DashboardKPIs(ORMBase):
    patrimonio_total: float
    variacao_mes_pct: float | None
    proventos_mes: float
    distribuicao_brl_pct: float
    distribuicao_usd_pct: float


# 🆕 NOVOS SCHEMAS

class ComparativoAnual(ORMBase):
    """Totais consolidados de um ano."""
    ano: int
    receitas: float
    despesas: float
    saldo: float
    proventos: float


class PontoSaldoInvestimentos(ORMBase):
    """Um ponto na evolução de saldos de investimentos."""
    label: str
    renda_fixa: float
    previdencia: float
    fgts: float
    cripto: float
    rv_br: float
    rv_eua: float


class PontoDistribuicaoMensal(ORMBase):
    """Distribuição BR/EUA/Cripto em um mês."""
    label: str
    rv_br: float
    rv_eua: float
    cripto: float


class DashboardDados(ORMBase):
    timestamp: datetime
    kpis: DashboardKPIs
    evolucao_patrimonial: list[PontoEvolucao]
    distribuicao_carteira: list[FatiaCarteira]
    receitas_despesas: list[MesReceitaDespesa]
    renda_passiva: list[MesProvento]
    # 🆕
    comparativo_anual: list[ComparativoAnual]
    saldo_investimentos: list[PontoSaldoInvestimentos]
    distribuicao_mensal: list[PontoDistribuicaoMensal]
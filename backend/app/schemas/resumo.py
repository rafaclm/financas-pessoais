from app.schemas.common import ORMBase


class PeriodoInfo(ORMBase):
    ano_id: int
    ano: int
    mes: int


class TotaisMes(ORMBase):
    receitas: float
    despesas: float
    saldo: float
    combustivel: float
    cartoes_total: float
    aportes_brl: float
    aportes_usd: float
    aportes_usd_em_brl: float
    proventos_brl: float
    proventos_usd: float
    proventos_usd_em_brl: float


class ContadoresMes(ORMBase):
    qtd_receitas: int
    qtd_despesas: int
    qtd_combustivel: int
    qtd_aportes: int
    qtd_proventos: int


class CategoriaDestaque(ORMBase):
    id: int
    nome: str
    valor: float
    percentual_despesas: float


class AtivoDestaque(ORMBase):
    id: int
    ticker: str
    valor_brl: float


class DestaquesMes(ORMBase):
    categoria_maior_gasto: CategoriaDestaque | None = None
    ativo_maior_aporte: AtivoDestaque | None = None


class VariacaoComparativa(ORMBase):
    valor_atual: float
    valor_anterior: float
    variacao_pct: float


class ComparativoMesAnterior(ORMBase):
    receitas: VariacaoComparativa
    despesas: VariacaoComparativa
    saldo: VariacaoComparativa


class ResumoMensal(ORMBase):
    periodo: PeriodoInfo
    totais: TotaisMes
    contadores: ContadoresMes
    destaques: DestaquesMes
    comparativo_mes_anterior: ComparativoMesAnterior | None = None
    cotacao_usd_brl_utilizada: float | None = None
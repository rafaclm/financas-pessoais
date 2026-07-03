from app.schemas.common import ORMBase


# ===================== M21 - Consolidação Renda Variável =====================

class ItemPorClasse(ORMBase):
    classe: str
    valor_brl: float
    percentual_carteira: float
    qtd_ativos: int


class ItemPorGeografia(ORMBase):
    geografia: str
    valor_brl: float
    percentual_carteira: float
    qtd_ativos: int


class ItemPorAtivo(ORMBase):
    ativo_id: int
    ticker: str
    nome: str
    classe: str
    geografia: str
    valor_brl: float
    percentual_carteira: float


class ConsolidacaoRV(ORMBase):
    periodo: dict  # {ano_id, ano, mes}
    total_brl: float
    total_br_brl: float
    total_eua_brl: float
    total_cripto_brl: float
    por_geografia: list[ItemPorGeografia]
    por_classe: list[ItemPorClasse]
    por_ativo: list[ItemPorAtivo]


# ===================== M22 - Consolidação Patrimonial =====================

class ComponentePatrimonio(ORMBase):
    """Cada bloco do patrimônio (contas, RF, previdência, FII...)."""
    categoria: str
    label: str
    valor_brl: float
    percentual_total: float
    cor: str | None = None


class VariacaoPatrimonial(ORMBase):
    valor_atual: float
    valor_referencia: float
    diferenca: float
    variacao_pct: float


class ConsolidacaoPatrimonial(ORMBase):
    periodo: dict
    patrimonio_total: float

    # Componentes do patrimônio
    componentes: list[ComponentePatrimonio]

    # Totais agrupados
    total_liquidez: float          # contas correntes (BRL+USD em BRL)
    total_renda_fixa: float         # produtos RF + previdência + FGTS + fundos
    total_renda_variavel: float    # BR + EUA (em BRL)
    total_cripto: float

    # Comparativos
    variacao_mes_anterior: VariacaoPatrimonial | None = None
    variacao_ano_anterior: VariacaoPatrimonial | None = None

    # Distribuição percentual
    pct_liquidez: float
    pct_renda_fixa: float
    pct_renda_variavel: float
    pct_cripto: float
    pct_brl: float
    pct_usd: float

    # Cotação utilizada
    cotacao_usd_brl: float | None = None
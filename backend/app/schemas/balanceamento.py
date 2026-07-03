from datetime import datetime
from pydantic import Field
from app.schemas.common import ORMBase, TimestampSchema


# ===================== CONFIGURAÇÕES =====================

class BalanceamentoGeografiaBase(ORMBase):
    geografia: str = Field(pattern="^(BR|EUA|GLOBAL)$")
    percentual_alvo: float = Field(ge=0, le=100)
    ativo: int = Field(default=1, ge=0, le=1)


class BalanceamentoGeografiaCreate(BalanceamentoGeografiaBase):
    pass


class BalanceamentoGeografiaUpdate(ORMBase):
    percentual_alvo: float | None = Field(default=None, ge=0, le=100)
    ativo: int | None = None


class BalanceamentoGeografiaOut(BalanceamentoGeografiaBase, TimestampSchema):
    id: int


class BalanceamentoClasseBase(ORMBase):
    geografia: str = Field(pattern="^(BR|EUA|GLOBAL)$")
    classe: str = Field(pattern="^(acao|etf|fii|fiagro|reit|cripto)$")
    percentual_alvo: float = Field(ge=0, le=100)
    ativo: int = Field(default=1, ge=0, le=1)


class BalanceamentoClasseCreate(BalanceamentoClasseBase):
    pass


class BalanceamentoClasseUpdate(ORMBase):
    percentual_alvo: float | None = Field(default=None, ge=0, le=100)
    ativo: int | None = None


class BalanceamentoClasseOut(BalanceamentoClasseBase, TimestampSchema):
    id: int


class BalanceamentoAtivoBase(ORMBase):
    ativo_id: int
    percentual_alvo_carteira: float = Field(ge=0, le=100)
    ativo: int = Field(default=1, ge=0, le=1)


class BalanceamentoAtivoCreate(BalanceamentoAtivoBase):
    pass


class BalanceamentoAtivoUpdate(ORMBase):
    percentual_alvo_carteira: float | None = Field(default=None, ge=0, le=100)
    ativo: int | None = None


class BalanceamentoAtivoOut(BalanceamentoAtivoBase, TimestampSchema):
    id: int


# ===================== ANÁLISE =====================

class ItemBalanceamentoGeografia(ORMBase):
    geografia: str
    valor_alocado_brl: float
    percentual_atual: float
    percentual_alvo: float | None
    gap_pct: float | None
    aporte_sugerido_brl: float | None
    status: str


class ItemBalanceamentoClasse(ORMBase):
    geografia: str
    classe: str
    valor_alocado_brl: float
    percentual_atual: float
    percentual_alvo: float | None
    gap_pct: float | None
    aporte_sugerido_brl: float | None
    status: str


class ItemBalanceamentoAtivo(ORMBase):
    ativo_id: int
    ticker: str
    nome: str
    classe: str
    geografia: str
    valor_alocado_brl: float
    percentual_atual: float
    percentual_alvo: float | None
    gap_pct: float | None
    aporte_sugerido_brl: float | None
    status: str
    ultima_cotacao_em: datetime | None = None


class AtivoSemCotacao(ORMBase):
    ticker: str
    motivo: str


class AnaliseBalanceamento(ORMBase):
    calculado_em: datetime
    total_rv_brl: float
    cotacao_usd_brl: float | None
    qtd_ativos_com_posicao: int
    qtd_ativos_sem_cotacao: int
    ativos_sem_cotacao: list[AtivoSemCotacao]
    por_geografia: list[ItemBalanceamentoGeografia]
    por_classe: list[ItemBalanceamentoClasse]
    por_ativo: list[ItemBalanceamentoAtivo]
    soma_alvos_geografia: float
    soma_alvos_classe_por_geo: dict[str, float]
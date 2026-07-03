from sqlalchemy import (
    Integer, String, Numeric, ForeignKey, UniqueConstraint, CheckConstraint, Text, Date, DateTime, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date as _date, datetime
from app.infrastructure.db.base import Base, TimestampMixin


# ===================== M01 =====================
class Ano(Base, TimestampMixin):
    __tablename__ = "anos"
    __table_args__ = (UniqueConstraint("ano", name="uq_anos_ano"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_inicial: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)


class CategoriaDespesa(Base, TimestampMixin):
    __tablename__ = "categorias_despesas"
    __table_args__ = (UniqueConstraint("nome", name="uq_cat_desp_nome"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), default="variavel", nullable=False)
    essencial: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cor: Mapped[str | None] = mapped_column(String(7), default="#888888")
    icone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class CategoriaReceita(Base, TimestampMixin):
    __tablename__ = "categorias_receitas"
    __table_args__ = (UniqueConstraint("nome", name="uq_cat_rec_nome"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    recorrencia: Mapped[str] = mapped_column(String(15), default="eventual", nullable=False)
    cor: Mapped[str | None] = mapped_column(String(7), default="#28a745")
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Instituicao(Base, TimestampMixin):
    __tablename__ = "instituicoes"
    __table_args__ = (UniqueConstraint("nome", name="uq_inst_nome"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    pais: Mapped[str] = mapped_column(String(2), default="BR", nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    contas: Mapped[list["Conta"]] = relationship(back_populates="instituicao")
    cartoes: Mapped[list["Cartao"]] = relationship(back_populates="instituicao")


class Conta(Base, TimestampMixin):
    __tablename__ = "contas"
    __table_args__ = (UniqueConstraint("nome", name="uq_contas_nome"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    instituicao_id: Mapped[int] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default="corrente", nullable=False)
    moeda: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    instituicao: Mapped["Instituicao"] = relationship(back_populates="contas")


class Cartao(Base, TimestampMixin):
    __tablename__ = "cartoes"
    __table_args__ = (
        UniqueConstraint("nome", name="uq_cartoes_nome"),
        CheckConstraint("dia_fechamento BETWEEN 1 AND 31", name="ck_cartoes_fechamento"),
        CheckConstraint("dia_vencimento BETWEEN 1 AND 31", name="ck_cartoes_vencimento"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    instituicao_id: Mapped[int] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    conta_pagamento_id: Mapped[int | None] = mapped_column(ForeignKey("contas.id"), nullable=True)
    dia_fechamento: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    instituicao: Mapped["Instituicao"] = relationship(back_populates="cartoes")


class ProdutoInvestimento(Base, TimestampMixin):
    __tablename__ = "produtos_investimento"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    categoria: Mapped[str] = mapped_column(String(20), nullable=False)
    instituicao_id: Mapped[int] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    moeda: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Ativo(Base, TimestampMixin):
    __tablename__ = "ativos"
    __table_args__ = (UniqueConstraint("ticker", name="uq_ativos_ticker"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    mercado: Mapped[str] = mapped_column(String(15), nullable=False)
    geografia: Mapped[str] = mapped_column(String(10), nullable=False)
    classe: Mapped[str] = mapped_column(String(15), nullable=False)
    moeda: Mapped[str] = mapped_column(String(3), nullable=False)
    setor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class LancamentoReceita(Base, TimestampMixin):
    __tablename__ = "lancamentos_receitas"
    __table_args__ = (
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_rec_mes"),
        CheckConstraint("valor > 0", name="ck_rec_valor"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias_receitas.id"), nullable=False)
    conta_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recorrente: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replicado_de_id: Mapped[int | None] = mapped_column(
        ForeignKey("lancamentos_receitas.id"), nullable=True
    )


class LancamentoDespesa(Base, TimestampMixin):
    __tablename__ = "lancamentos_despesas"
    __table_args__ = (
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_desp_mes"),
        CheckConstraint("valor > 0", name="ck_desp_valor"),
        CheckConstraint(
            "(origem_tipo = 'conta' AND conta_id IS NOT NULL) OR "
            "(origem_tipo = 'cartao' AND cartao_id IS NOT NULL)",
            name="ck_desp_origem"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias_despesas.id"), nullable=False)
    origem_tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    conta_id: Mapped[int | None] = mapped_column(ForeignKey("contas.id"), nullable=True)
    cartao_id: Mapped[int | None] = mapped_column(ForeignKey("cartoes.id"), nullable=True)
    valor: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recorrente: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    auto_pagamento_cartao: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pagamento_cartao_id: Mapped[int | None] = mapped_column(
        ForeignKey("pagamentos_cartao.id"), nullable=True
    )
    replicado_de_id: Mapped[int | None] = mapped_column(
        ForeignKey("lancamentos_despesas.id"), nullable=True
    )


class LancamentoCombustivel(Base, TimestampMixin):
    __tablename__ = "lancamentos_combustivel"
    __table_args__ = (
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_comb_mes"),
        CheckConstraint("litros > 0", name="ck_comb_litros"),
        CheckConstraint("valor_total > 0", name="ck_comb_valor"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[_date] = mapped_column(Date, nullable=False)
    litros: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    posto: Mapped[str | None] = mapped_column(String(80), nullable=True)
    veiculo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    conta_id: Mapped[int | None] = mapped_column(ForeignKey("contas.id"), nullable=True)
    cartao_id: Mapped[int | None] = mapped_column(ForeignKey("cartoes.id"), nullable=True)


class PagamentoCartao(Base, TimestampMixin):
    __tablename__ = "pagamentos_cartao"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "cartao_id", name="uq_pag_cartao_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_pag_mes"),
        CheckConstraint("valor > 0", name="ck_pag_valor"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    cartao_id: Mapped[int] = mapped_column(ForeignKey("cartoes.id"), nullable=False)
    conta_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(200), nullable=True)


class AporteBolsa(Base, TimestampMixin):
    __tablename__ = "aportes_bolsa"
    __table_args__ = (
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_apor_mes"),
        CheckConstraint("quantidade > 0", name="ck_apor_qtd"),
        CheckConstraint("preco_unitario > 0", name="ck_apor_preco"),
        CheckConstraint("tipo_operacao IN ('compra', 'venda')", name="ck_apor_tipo"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[_date] = mapped_column(Date, nullable=False)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    tipo_operacao: Mapped[str] = mapped_column(String(10), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    taxas: Mapped[float] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    moeda: Mapped[str] = mapped_column(String(3), nullable=False)
    cotacao_usd_brl: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    valor_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    valor_total_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    conta_id: Mapped[int | None] = mapped_column(ForeignKey("contas.id"), nullable=True)
    descricao: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Provento(Base, TimestampMixin):
    __tablename__ = "proventos"
    __table_args__ = (
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_prov_mes"),
        CheckConstraint(
            "tipo IN ('dividendo', 'jcp', 'rendimento', 'juros_cripto', 'outro')",
            name="ck_prov_tipo"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[_date] = mapped_column(Date, nullable=False)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_bruto: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    valor_liquido: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    moeda: Mapped[str] = mapped_column(String(3), nullable=False)
    cotacao_usd_brl: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    valor_liquido_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    conta_id: Mapped[int | None] = mapped_column(ForeignKey("contas.id"), nullable=True)
    descricao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantidade_cotas: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)


class SaldoConta(Base, TimestampMixin):
    __tablename__ = "saldos_contas"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "conta_id", name="uq_saldo_conta_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_saldo_conta_mes"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    conta_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    saldo: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cotacao_usd_brl: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    saldo_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class SaldoInvestimento(Base, TimestampMixin):
    __tablename__ = "saldos_investimentos"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "produto_id", name="uq_saldo_inv_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_saldo_inv_mes"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos_investimento.id"), nullable=False)
    saldo: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cotacao_usd_brl: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    saldo_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class PosicaoCripto(Base, TimestampMixin):
    __tablename__ = "posicoes_cripto"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "ativo_id", name="uq_cripto_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_cripto_mes"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    saldo_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cotacao_usd_brl: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    saldo_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    variacao_pct: Mapped[float | None] = mapped_column(Numeric(7, 4), nullable=True)


class PosicaoAtivoBR(Base, TimestampMixin):
    __tablename__ = "posicoes_ativos_br"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "ativo_id", name="uq_br_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_br_mes"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    preco_medio: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cotacao_fechamento: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    valor_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class PosicaoAtivoEUA(Base, TimestampMixin):
    __tablename__ = "posicoes_ativos_eua"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "ativo_id", name="uq_eua_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_eua_mes"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    preco_medio_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cotacao_fechamento_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cotacao_usd_brl: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    valor_total_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    valor_total_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class CotacaoCambio(Base, TimestampMixin):
    __tablename__ = "cotacoes_cambio"
    __table_args__ = (
        UniqueConstraint("ano_id", "mes", "par", name="uq_cambio_periodo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_cambio_mes"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ano_id: Mapped[int] = mapped_column(ForeignKey("anos.id"), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    par: Mapped[str] = mapped_column(String(7), default="USDBRL", nullable=False)
    cotacao: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    fonte: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)


class BalanceamentoGeografia(Base, TimestampMixin):
    __tablename__ = "balanceamento_config_geografia"
    __table_args__ = (
        UniqueConstraint("geografia", name="uq_balanc_geo"),
        CheckConstraint("percentual_alvo >= 0 AND percentual_alvo <= 100", name="ck_balanc_geo_pct"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    geografia: Mapped[str] = mapped_column(String(10), nullable=False)
    percentual_alvo: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class BalanceamentoClasse(Base, TimestampMixin):
    __tablename__ = "balanceamento_config_classe"
    __table_args__ = (
        UniqueConstraint("geografia", "classe", name="uq_balanc_classe"),
        CheckConstraint("percentual_alvo >= 0 AND percentual_alvo <= 100", name="ck_balanc_classe_pct"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    geografia: Mapped[str] = mapped_column(String(10), nullable=False)
    classe: Mapped[str] = mapped_column(String(15), nullable=False)
    percentual_alvo: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class BalanceamentoAtivo(Base, TimestampMixin):
    __tablename__ = "balanceamento_config_ativo"
    __table_args__ = (
        UniqueConstraint("ativo_id", name="uq_balanc_ativo"),
        CheckConstraint(
            "percentual_alvo_carteira >= 0 AND percentual_alvo_carteira <= 100",
            name="ck_balanc_ativo_pct"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    percentual_alvo_carteira: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    ativo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class PosicaoAtualAtivo(Base, TimestampMixin):
    __tablename__ = "posicao_atual_ativo"
    __table_args__ = (UniqueConstraint("ativo_id", name="uq_posicao_atual_ativo"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativos.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    quantidade_comprada_total: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    quantidade_vendida_total: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    custo_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    preco_medio: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    preco_medio_manual: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    preco_medio_eh_manual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cotacao_atual: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    cotacao_atual_data: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cotacao_fonte: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cotacao_usd_brl: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    valor_atual_brl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    preco_teto: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)


# ============================================================
# 🆕 USUARIOS (Autenticacao)
# ============================================================
class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("email", name="uq_usuarios_email"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
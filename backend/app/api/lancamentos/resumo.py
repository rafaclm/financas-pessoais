from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from app.api.deps import DbSession
from app.infrastructure.db.models import (
    Ano, LancamentoReceita, LancamentoDespesa, LancamentoCombustivel,
    PagamentoCartao, AporteBolsa, Provento, CategoriaDespesa, Ativo
)
from app.schemas.resumo import (
    ResumoMensal, PeriodoInfo, TotaisMes, ContadoresMes,
    DestaquesMes, CategoriaDestaque, AtivoDestaque,
    ComparativoMesAnterior, VariacaoComparativa
)
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/resumo-mensal", tags=["Resumo Mensal"])


def _mes_anterior(ano_obj: Ano, mes: int, db) -> tuple[int | None, int | None]:
    """Retorna (ano_id, mes) do mês anterior."""
    if mes == 1:
        ano_ant = db.scalar(select(Ano).where(Ano.ano == ano_obj.ano - 1))
        if not ano_ant:
            return None, None
        return ano_ant.id, 12
    return ano_obj.id, mes - 1


def _calcular_totais(db, ano_id: int, mes: int) -> tuple[TotaisMes, ContadoresMes]:
    # Receitas
    rec_total = db.scalar(
        select(func.coalesce(func.sum(LancamentoReceita.valor), 0))
        .where(LancamentoReceita.ano_id == ano_id, LancamentoReceita.mes == mes)
    ) or 0
    rec_qtd = db.scalar(
        select(func.count(LancamentoReceita.id))
        .where(LancamentoReceita.ano_id == ano_id, LancamentoReceita.mes == mes)
    ) or 0

    # Despesas
    desp_total = db.scalar(
        select(func.coalesce(func.sum(LancamentoDespesa.valor), 0))
        .where(LancamentoDespesa.ano_id == ano_id, LancamentoDespesa.mes == mes)
    ) or 0
    desp_qtd = db.scalar(
        select(func.count(LancamentoDespesa.id))
        .where(LancamentoDespesa.ano_id == ano_id, LancamentoDespesa.mes == mes)
    ) or 0

    # Combustível
    comb_total = db.scalar(
        select(func.coalesce(func.sum(LancamentoCombustivel.valor_total), 0))
        .where(LancamentoCombustivel.ano_id == ano_id, LancamentoCombustivel.mes == mes)
    ) or 0
    comb_qtd = db.scalar(
        select(func.count(LancamentoCombustivel.id))
        .where(LancamentoCombustivel.ano_id == ano_id, LancamentoCombustivel.mes == mes)
    ) or 0

    # Pagamentos de cartão
    cart_total = db.scalar(
        select(func.coalesce(func.sum(PagamentoCartao.valor), 0))
        .where(PagamentoCartao.ano_id == ano_id, PagamentoCartao.mes == mes)
    ) or 0

    # Aportes
    aportes_brl = db.scalar(
        select(func.coalesce(func.sum(AporteBolsa.valor_total), 0))
        .where(AporteBolsa.ano_id == ano_id, AporteBolsa.mes == mes,
               AporteBolsa.moeda == "BRL")
    ) or 0
    aportes_usd = db.scalar(
        select(func.coalesce(func.sum(AporteBolsa.valor_total), 0))
        .where(AporteBolsa.ano_id == ano_id, AporteBolsa.mes == mes,
               AporteBolsa.moeda == "USD")
    ) or 0
    aportes_usd_brl = db.scalar(
        select(func.coalesce(func.sum(AporteBolsa.valor_total_brl), 0))
        .where(AporteBolsa.ano_id == ano_id, AporteBolsa.mes == mes,
               AporteBolsa.moeda == "USD")
    ) or 0
    aportes_qtd = db.scalar(
        select(func.count(AporteBolsa.id))
        .where(AporteBolsa.ano_id == ano_id, AporteBolsa.mes == mes)
    ) or 0

    # Proventos
    prov_brl = db.scalar(
        select(func.coalesce(func.sum(Provento.valor_liquido), 0))
        .where(Provento.ano_id == ano_id, Provento.mes == mes,
               Provento.moeda == "BRL")
    ) or 0
    prov_usd = db.scalar(
        select(func.coalesce(func.sum(Provento.valor_liquido), 0))
        .where(Provento.ano_id == ano_id, Provento.mes == mes,
               Provento.moeda == "USD")
    ) or 0
    prov_usd_brl = db.scalar(
        select(func.coalesce(func.sum(Provento.valor_liquido_brl), 0))
        .where(Provento.ano_id == ano_id, Provento.mes == mes,
               Provento.moeda == "USD")
    ) or 0
    prov_qtd = db.scalar(
        select(func.count(Provento.id))
        .where(Provento.ano_id == ano_id, Provento.mes == mes)
    ) or 0

    totais = TotaisMes(
        receitas=float(rec_total),
        despesas=float(desp_total),
        saldo=float(rec_total) - float(desp_total),
        combustivel=float(comb_total),
        cartoes_total=float(cart_total),
        aportes_brl=float(aportes_brl),
        aportes_usd=float(aportes_usd),
        aportes_usd_em_brl=float(aportes_usd_brl),
        proventos_brl=float(prov_brl),
        proventos_usd=float(prov_usd),
        proventos_usd_em_brl=float(prov_usd_brl),
    )
    contadores = ContadoresMes(
        qtd_receitas=rec_qtd,
        qtd_despesas=desp_qtd,
        qtd_combustivel=comb_qtd,
        qtd_aportes=aportes_qtd,
        qtd_proventos=prov_qtd,
    )
    return totais, contadores


def _calcular_destaques(db, ano_id: int, mes: int, total_despesas: float) -> DestaquesMes:
    # Categoria com maior gasto
    cat_top = db.execute(
        select(
            CategoriaDespesa.id,
            CategoriaDespesa.nome,
            func.sum(LancamentoDespesa.valor).label("total"),
        )
        .join(LancamentoDespesa, LancamentoDespesa.categoria_id == CategoriaDespesa.id)
        .where(LancamentoDespesa.ano_id == ano_id, LancamentoDespesa.mes == mes)
        .group_by(CategoriaDespesa.id, CategoriaDespesa.nome)
        .order_by(func.sum(LancamentoDespesa.valor).desc())
        .limit(1)
    ).first()

    cat_destaque = None
    if cat_top:
        cat_destaque = CategoriaDestaque(
            id=cat_top.id,
            nome=cat_top.nome,
            valor=float(cat_top.total),
            percentual_despesas=(
                round(float(cat_top.total) / total_despesas * 100, 2)
                if total_despesas else 0
            ),
        )

    # Ativo com maior aporte
    ativo_top = db.execute(
        select(
            Ativo.id, Ativo.ticker,
            func.sum(AporteBolsa.valor_total_brl).label("total"),
        )
        .join(AporteBolsa, AporteBolsa.ativo_id == Ativo.id)
        .where(AporteBolsa.ano_id == ano_id, AporteBolsa.mes == mes,
               AporteBolsa.tipo_operacao == "compra")
        .group_by(Ativo.id, Ativo.ticker)
        .order_by(func.sum(AporteBolsa.valor_total_brl).desc())
        .limit(1)
    ).first()

    ativo_destaque = None
    if ativo_top:
        ativo_destaque = AtivoDestaque(
            id=ativo_top.id,
            ticker=ativo_top.ticker,
            valor_brl=float(ativo_top.total),
        )

    return DestaquesMes(
        categoria_maior_gasto=cat_destaque,
        ativo_maior_aporte=ativo_destaque,
    )


def _variacao(atual: float, anterior: float) -> VariacaoComparativa:
    if anterior == 0:
        pct = 100.0 if atual > 0 else 0.0
    else:
        pct = round((atual - anterior) / abs(anterior) * 100, 2)
    return VariacaoComparativa(
        valor_atual=atual, valor_anterior=anterior, variacao_pct=pct
    )


@router.get("", response_model=ResumoMensal)
def resumo_mensal(db: DbSession, ano_id: int, mes: int):
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        raise HTTPException(404, "Ano não encontrado")
    if mes < 1 or mes > 12:
        raise HTTPException(400, "Mês inválido")

    totais, contadores = _calcular_totais(db, ano_id, mes)
    destaques = _calcular_destaques(db, ano_id, mes, totais.despesas)

    # Comparativo com mês anterior
    comparativo = None
    ano_id_ant, mes_ant = _mes_anterior(ano_obj, mes, db)
    if ano_id_ant and mes_ant:
        totais_ant, _ = _calcular_totais(db, ano_id_ant, mes_ant)
        comparativo = ComparativoMesAnterior(
            receitas=_variacao(totais.receitas, totais_ant.receitas),
            despesas=_variacao(totais.despesas, totais_ant.despesas),
            saldo=_variacao(totais.saldo, totais_ant.saldo),
        )

    cotacao = obter_ou_buscar_cotacao(db, ano_id, mes)

    return ResumoMensal(
        periodo=PeriodoInfo(ano_id=ano_id, ano=ano_obj.ano, mes=mes),
        totais=totais,
        contadores=contadores,
        destaques=destaques,
        comparativo_mes_anterior=comparativo,
        cotacao_usd_brl_utilizada=cotacao,
    )
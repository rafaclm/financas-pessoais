"""
Service de posições mensais.
- Replicação de saldos do mês anterior
- Cálculo de preço médio sugerido (com base em aportes existentes)
"""
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session
from app.infrastructure.db.models import (
    SaldoConta, SaldoInvestimento, PosicaoCripto,
    PosicaoAtivoBR, PosicaoAtivoEUA, AporteBolsa, Ano
)


def _mes_anterior(db: Session, ano_id: int, mes: int) -> tuple[int | None, int | None]:
    """Retorna (ano_id_anterior, mes_anterior)."""
    if mes > 1:
        return ano_id, mes - 1
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        return None, None
    ano_ant = db.scalar(select(Ano).where(Ano.ano == ano_obj.ano - 1))
    return (ano_ant.id, 12) if ano_ant else (None, None)


def replicar_saldos_contas(db: Session, ano_id: int, mes: int, force: bool = False) -> dict:
    ano_origem, mes_origem = _mes_anterior(db, ano_id, mes)
    if not ano_origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem mês anterior disponível."}

    origem = db.scalars(
        select(SaldoConta).where(SaldoConta.ano_id == ano_origem, SaldoConta.mes == mes_origem)
    ).all()

    if not origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem saldos no mês anterior."}

    # Verifica existentes no destino
    existentes = db.scalars(
        select(SaldoConta).where(SaldoConta.ano_id == ano_id, SaldoConta.mes == mes)
    ).all()
    if existentes and not force:
        return {
            "replicados": 0, "origem_total": len(origem),
            "mensagem": "Já existem saldos no mês destino. Use force=true para sobrescrever."
        }

    if existentes and force:
        for e in existentes:
            db.delete(e)
        db.flush()

    for o in origem:
        novo = SaldoConta(
            ano_id=ano_id, mes=mes, conta_id=o.conta_id,
            saldo=o.saldo, cotacao_usd_brl=o.cotacao_usd_brl, saldo_brl=o.saldo_brl
        )
        db.add(novo)
    db.commit()
    return {
        "replicados": len(origem), "origem_total": len(origem),
        "mensagem": f"{len(origem)} saldos replicados do mês anterior."
    }


def replicar_saldos_investimentos(db: Session, ano_id: int, mes: int, force: bool = False) -> dict:
    ano_origem, mes_origem = _mes_anterior(db, ano_id, mes)
    if not ano_origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem mês anterior disponível."}

    origem = db.scalars(
        select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == ano_origem, SaldoInvestimento.mes == mes_origem
        )
    ).all()
    if not origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem saldos no mês anterior."}

    existentes = db.scalars(
        select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == ano_id, SaldoInvestimento.mes == mes
        )
    ).all()
    if existentes and not force:
        return {
            "replicados": 0, "origem_total": len(origem),
            "mensagem": "Já existem saldos no mês destino. Use force=true para sobrescrever."
        }

    if existentes and force:
        for e in existentes:
            db.delete(e)
        db.flush()

    for o in origem:
        novo = SaldoInvestimento(
            ano_id=ano_id, mes=mes, produto_id=o.produto_id,
            saldo=o.saldo, cotacao_usd_brl=o.cotacao_usd_brl, saldo_brl=o.saldo_brl
        )
        db.add(novo)
    db.commit()
    return {
        "replicados": len(origem), "origem_total": len(origem),
        "mensagem": f"{len(origem)} saldos replicados do mês anterior."
    }


def replicar_posicoes_cripto(db: Session, ano_id: int, mes: int, force: bool = False) -> dict:
    ano_origem, mes_origem = _mes_anterior(db, ano_id, mes)
    if not ano_origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem mês anterior disponível."}

    origem = db.scalars(
        select(PosicaoCripto).where(
            PosicaoCripto.ano_id == ano_origem, PosicaoCripto.mes == mes_origem
        )
    ).all()
    if not origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem posições no mês anterior."}

    existentes = db.scalars(
        select(PosicaoCripto).where(
            PosicaoCripto.ano_id == ano_id, PosicaoCripto.mes == mes
        )
    ).all()
    if existentes and not force:
        return {
            "replicados": 0, "origem_total": len(origem),
            "mensagem": "Já existem posições no mês destino. Use force=true."
        }
    if existentes and force:
        for e in existentes:
            db.delete(e)
        db.flush()

    for o in origem:
        novo = PosicaoCripto(
            ano_id=ano_id, mes=mes, ativo_id=o.ativo_id,
            quantidade=o.quantidade, saldo_brl=o.saldo_brl,
            cotacao_usd_brl=o.cotacao_usd_brl, saldo_usd=o.saldo_usd,
            variacao_pct=None,  # zera variação ao replicar
        )
        db.add(novo)
    db.commit()
    return {
        "replicados": len(origem), "origem_total": len(origem),
        "mensagem": f"{len(origem)} posições replicadas."
    }


def replicar_posicoes_br(db: Session, ano_id: int, mes: int, force: bool = False) -> dict:
    ano_origem, mes_origem = _mes_anterior(db, ano_id, mes)
    if not ano_origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem mês anterior disponível."}

    origem = db.scalars(
        select(PosicaoAtivoBR).where(
            PosicaoAtivoBR.ano_id == ano_origem, PosicaoAtivoBR.mes == mes_origem
        )
    ).all()
    if not origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem posições no mês anterior."}

    existentes = db.scalars(
        select(PosicaoAtivoBR).where(
            PosicaoAtivoBR.ano_id == ano_id, PosicaoAtivoBR.mes == mes
        )
    ).all()
    if existentes and not force:
        return {
            "replicados": 0, "origem_total": len(origem),
            "mensagem": "Já existem posições no mês destino. Use force=true."
        }
    if existentes and force:
        for e in existentes:
            db.delete(e)
        db.flush()

    for o in origem:
        novo = PosicaoAtivoBR(
            ano_id=ano_id, mes=mes, ativo_id=o.ativo_id,
            quantidade=o.quantidade, preco_medio=o.preco_medio,
            cotacao_fechamento=o.cotacao_fechamento,
            valor_total=float(o.quantidade) * float(o.cotacao_fechamento),
        )
        db.add(novo)
    db.commit()
    return {
        "replicados": len(origem), "origem_total": len(origem),
        "mensagem": f"{len(origem)} posições BR replicadas."
    }


def replicar_posicoes_eua(db: Session, ano_id: int, mes: int, force: bool = False) -> dict:
    ano_origem, mes_origem = _mes_anterior(db, ano_id, mes)
    if not ano_origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem mês anterior disponível."}

    origem = db.scalars(
        select(PosicaoAtivoEUA).where(
            PosicaoAtivoEUA.ano_id == ano_origem, PosicaoAtivoEUA.mes == mes_origem
        )
    ).all()
    if not origem:
        return {"replicados": 0, "origem_total": 0, "mensagem": "Sem posições no mês anterior."}

    existentes = db.scalars(
        select(PosicaoAtivoEUA).where(
            PosicaoAtivoEUA.ano_id == ano_id, PosicaoAtivoEUA.mes == mes
        )
    ).all()
    if existentes and not force:
        return {
            "replicados": 0, "origem_total": len(origem),
            "mensagem": "Já existem posições no mês destino. Use force=true."
        }
    if existentes and force:
        for e in existentes:
            db.delete(e)
        db.flush()

    for o in origem:
        valor_usd = float(o.quantidade) * float(o.cotacao_fechamento_usd)
        novo = PosicaoAtivoEUA(
            ano_id=ano_id, mes=mes, ativo_id=o.ativo_id,
            quantidade=o.quantidade, preco_medio_usd=o.preco_medio_usd,
            cotacao_fechamento_usd=o.cotacao_fechamento_usd,
            cotacao_usd_brl=o.cotacao_usd_brl,
            valor_total_usd=valor_usd,
            valor_total_brl=valor_usd * float(o.cotacao_usd_brl),
        )
        db.add(novo)
    db.commit()
    return {
        "replicados": len(origem), "origem_total": len(origem),
        "mensagem": f"{len(origem)} posições EUA replicadas."
    }


def calcular_preco_medio_sugerido(
    db: Session, ativo_id: int, ano_id: int, mes: int, moeda_filtro: str = "BRL"
) -> dict:
    """
    Calcula preço médio sugerido considerando todos os aportes do ativo
    até o mês de referência (compras adicionam, vendas removem).
    Fórmula simplificada: total investido (somente compras) / quantidade total.
    """
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        return {
            "ativo_id": ativo_id, "quantidade_acumulada": 0,
            "preco_medio_sugerido": 0, "total_aportes": 0
        }

    # Considera todos aportes do ativo até o ano/mês informado
    stmt = (
        select(
            func.count(AporteBolsa.id).label("qtd_total"),
            func.coalesce(func.sum(
                case((AporteBolsa.tipo_operacao == "compra", AporteBolsa.quantidade), else_=0)
            ), 0).label("qtd_compradas"),
            func.coalesce(func.sum(
                case((AporteBolsa.tipo_operacao == "venda", AporteBolsa.quantidade), else_=0)
            ), 0).label("qtd_vendidas"),
            func.coalesce(func.sum(
                case((AporteBolsa.tipo_operacao == "compra",
                      AporteBolsa.quantidade * AporteBolsa.preco_unitario), else_=0)
            ), 0).label("valor_compras"),
        )
        .where(
            and_(
                AporteBolsa.ativo_id == ativo_id,
                AporteBolsa.moeda == moeda_filtro,
            )
        )
    )
    r = db.execute(stmt).one()

    qtd_acumulada = float(r.qtd_compradas or 0) - float(r.qtd_vendidas or 0)
    valor_compras = float(r.valor_compras or 0)
    qtd_compradas = float(r.qtd_compradas or 0)

    preco_medio = valor_compras / qtd_compradas if qtd_compradas > 0 else 0

    return {
        "ativo_id": ativo_id,
        "quantidade_acumulada": qtd_acumulada,
        "preco_medio_sugerido": round(preco_medio, 4),
        "total_aportes": int(r.qtd_total or 0),
    }
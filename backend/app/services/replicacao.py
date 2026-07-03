"""
Service de replicação de lançamentos entre meses.
Replica receitas e despesas marcadas como recorrentes.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.infrastructure.db.models import (
    LancamentoReceita, LancamentoDespesa
)
from app.schemas.replicacao import ReplicarLancamentos, ResultadoReplicacao


def replicar_lancamentos(db: Session, payload: ReplicarLancamentos) -> ResultadoReplicacao:
    rec_origem_total = 0
    desp_origem_total = 0
    rec_replicadas = 0
    desp_replicadas = 0

    # ---------- RECEITAS ----------
    if payload.replicar_receitas:
        stmt = select(LancamentoReceita).where(
            LancamentoReceita.ano_id == payload.ano_origem_id,
            LancamentoReceita.mes == payload.mes_origem,
        )
        if payload.apenas_recorrentes:
            stmt = stmt.where(LancamentoReceita.recorrente == 1)
        receitas_origem = db.scalars(stmt).all()
        rec_origem_total = len(receitas_origem)

        destino_existente = db.scalar(
            select(LancamentoReceita).where(
                LancamentoReceita.ano_id == payload.ano_destino_id,
                LancamentoReceita.mes == payload.mes_destino,
            )
        )
        if destino_existente and not payload.force:
            return ResultadoReplicacao(
                receitas_replicadas=0,
                despesas_replicadas=0,
                receitas_origem_total=rec_origem_total,
                despesas_origem_total=0,
                mensagem=(
                    "Já existem receitas no mês destino. "
                    "Use force=true para sobrescrever (não recomendado)."
                ),
            )

        for r in receitas_origem:
            nova = LancamentoReceita(
                ano_id=payload.ano_destino_id,
                mes=payload.mes_destino,
                categoria_id=r.categoria_id,
                conta_id=r.conta_id,
                valor=r.valor,
                descricao=r.descricao,
                recorrente=r.recorrente,
                replicado_de_id=r.id,
            )
            db.add(nova)
            rec_replicadas += 1

    # ---------- DESPESAS ----------
    if payload.replicar_despesas:
        stmt = select(LancamentoDespesa).where(
            LancamentoDespesa.ano_id == payload.ano_origem_id,
            LancamentoDespesa.mes == payload.mes_origem,
            LancamentoDespesa.auto_pagamento_cartao == 0,
        )
        if payload.apenas_recorrentes:
            stmt = stmt.where(LancamentoDespesa.recorrente == 1)
        despesas_origem = db.scalars(stmt).all()
        desp_origem_total = len(despesas_origem)

        destino_existente = db.scalar(
            select(LancamentoDespesa).where(
                LancamentoDespesa.ano_id == payload.ano_destino_id,
                LancamentoDespesa.mes == payload.mes_destino,
            )
        )
        if destino_existente and not payload.force:
            db.rollback()
            return ResultadoReplicacao(
                receitas_replicadas=0,
                despesas_replicadas=0,
                receitas_origem_total=rec_origem_total,
                despesas_origem_total=desp_origem_total,
                mensagem=(
                    "Já existem despesas no mês destino. "
                    "Use force=true para sobrescrever."
                ),
            )

        for d in despesas_origem:
            nova = LancamentoDespesa(
                ano_id=payload.ano_destino_id,
                mes=payload.mes_destino,
                categoria_id=d.categoria_id,
                origem_tipo=d.origem_tipo,
                conta_id=d.conta_id,
                cartao_id=d.cartao_id,
                valor=d.valor,
                descricao=d.descricao,
                recorrente=d.recorrente,
                replicado_de_id=d.id,
            )
            db.add(nova)
            desp_replicadas += 1

    db.commit()

    return ResultadoReplicacao(
        receitas_replicadas=rec_replicadas,
        despesas_replicadas=desp_replicadas,
        receitas_origem_total=rec_origem_total,
        despesas_origem_total=desp_origem_total,
        mensagem=f"Replicação concluída: {rec_replicadas} receitas e {desp_replicadas} despesas.",
    )
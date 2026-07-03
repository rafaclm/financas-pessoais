from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import (
    LancamentoDespesa, Ano, CategoriaDespesa, Conta, Cartao
)
from app.schemas.despesas import DespesaCreate, DespesaUpdate, DespesaOut

router = APIRouter(prefix="/despesas", tags=["Lancamentos - Despesas"])


def _validar_refs(db, payload):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(CategoriaDespesa, payload.categoria_id):
        raise HTTPException(400, "Categoria inválida")
    if payload.conta_id and not db.get(Conta, payload.conta_id):
        raise HTTPException(400, "Conta inválida")
    if payload.cartao_id and not db.get(Cartao, payload.cartao_id):
        raise HTTPException(400, "Cartão inválido")


@router.get("", response_model=list[DespesaOut])
def listar(
    db: DbSession,
    ano_id: int | None = None,
    mes: int | None = None,
    categoria_id: int | None = None,
    origem_tipo: str | None = None,
    conta_id: int | None = None,
    cartao_id: int | None = None,
):
    stmt = select(LancamentoDespesa).order_by(
        LancamentoDespesa.ano_id.desc(),
        LancamentoDespesa.mes.desc(),
        LancamentoDespesa.id.desc(),
    )
    if ano_id: stmt = stmt.where(LancamentoDespesa.ano_id == ano_id)
    if mes: stmt = stmt.where(LancamentoDespesa.mes == mes)
    if categoria_id: stmt = stmt.where(LancamentoDespesa.categoria_id == categoria_id)
    if origem_tipo: stmt = stmt.where(LancamentoDespesa.origem_tipo == origem_tipo)
    if conta_id: stmt = stmt.where(LancamentoDespesa.conta_id == conta_id)
    if cartao_id: stmt = stmt.where(LancamentoDespesa.cartao_id == cartao_id)
    return db.scalars(stmt).all()


@router.get("/{item_id}", response_model=DespesaOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(LancamentoDespesa, item_id)
    if not obj:
        raise HTTPException(404, "Despesa não encontrada")
    return obj


@router.post("", response_model=DespesaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: DespesaCreate, db: DbSession):
    _validar_refs(db, payload)
    obj = LancamentoDespesa(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=DespesaOut)
def atualizar(item_id: int, payload: DespesaUpdate, db: DbSession):
    obj = db.get(LancamentoDespesa, item_id)
    if not obj:
        raise HTTPException(404, "Despesa não encontrada")
    # Bloqueia edição de despesas criadas automaticamente por pagamento de cartão
    if obj.auto_pagamento_cartao == 1:
        raise HTTPException(
            400,
            "Esta despesa foi gerada automaticamente. Edite via Pagamento de Cartão."
        )
    data = payload.model_dump(exclude_unset=True)
    if "categoria_id" in data and not db.get(CategoriaDespesa, data["categoria_id"]):
        raise HTTPException(400, "Categoria inválida")
    if data.get("conta_id") and not db.get(Conta, data["conta_id"]):
        raise HTTPException(400, "Conta inválida")
    if data.get("cartao_id") and not db.get(Cartao, data["cartao_id"]):
        raise HTTPException(400, "Cartão inválido")
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(LancamentoDespesa, item_id)
    if not obj:
        raise HTTPException(404, "Despesa não encontrada")
    if obj.auto_pagamento_cartao == 1:
        raise HTTPException(
            400,
            "Esta despesa foi gerada automaticamente. Exclua o pagamento de cartão correspondente."
        )
    db.delete(obj); db.commit()
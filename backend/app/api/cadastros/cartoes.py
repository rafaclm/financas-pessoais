from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import Cartao, Instituicao, Conta
from app.schemas.cartoes import CartaoCreate, CartaoUpdate, CartaoOut

router = APIRouter(prefix="/cartoes", tags=["Cadastros - Cartões"])


@router.get("", response_model=list[CartaoOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(Cartao).order_by(Cartao.nome)
    if apenas_ativos:
        stmt = stmt.where(Cartao.ativo == 1)
    return db.scalars(stmt).all()


@router.post("", response_model=CartaoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: CartaoCreate, db: DbSession):
    if not db.get(Instituicao, payload.instituicao_id):
        raise HTTPException(400, "Instituição inválida")
    if payload.conta_pagamento_id and not db.get(Conta, payload.conta_pagamento_id):
        raise HTTPException(400, "Conta de pagamento inválida")
    if db.scalar(select(Cartao).where(Cartao.nome == payload.nome)):
        raise HTTPException(409, "Já existe cartão com este nome")
    obj = Cartao(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=CartaoOut)
def atualizar(item_id: int, payload: CartaoUpdate, db: DbSession):
    obj = db.get(Cartao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(Cartao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    obj.ativo = 0; db.commit()
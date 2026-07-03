from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import CategoriaDespesa
from app.schemas.categorias import (
    CategoriaDespesaCreate, CategoriaDespesaUpdate, CategoriaDespesaOut
)

router = APIRouter(prefix="/categorias/despesas", tags=["Cadastros - Categorias Despesas"])


@router.get("", response_model=list[CategoriaDespesaOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(CategoriaDespesa).order_by(CategoriaDespesa.nome)
    if apenas_ativos:
        stmt = stmt.where(CategoriaDespesa.ativo == 1)
    return db.scalars(stmt).all()


@router.get("/{item_id}", response_model=CategoriaDespesaOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(CategoriaDespesa, item_id)
    if not obj:
        raise HTTPException(404, "Categoria não encontrada")
    return obj


@router.post("", response_model=CategoriaDespesaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: CategoriaDespesaCreate, db: DbSession):
    if db.scalar(select(CategoriaDespesa).where(CategoriaDespesa.nome == payload.nome)):
        raise HTTPException(409, "Já existe categoria com este nome")
    obj = CategoriaDespesa(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=CategoriaDespesaOut)
def atualizar(item_id: int, payload: CategoriaDespesaUpdate, db: DbSession):
    obj = db.get(CategoriaDespesa, item_id)
    if not obj:
        raise HTTPException(404, "Categoria não encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(CategoriaDespesa, item_id)
    if not obj:
        raise HTTPException(404, "Categoria não encontrada")
    obj.ativo = 0
    db.commit()
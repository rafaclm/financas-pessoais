from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import CategoriaReceita
from app.schemas.categorias import (
    CategoriaReceitaCreate, CategoriaReceitaUpdate, CategoriaReceitaOut
)

router = APIRouter(prefix="/categorias/receitas", tags=["Cadastros - Categorias Receitas"])


@router.get("", response_model=list[CategoriaReceitaOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(CategoriaReceita).order_by(CategoriaReceita.nome)
    if apenas_ativos:
        stmt = stmt.where(CategoriaReceita.ativo == 1)
    return db.scalars(stmt).all()


@router.post("", response_model=CategoriaReceitaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: CategoriaReceitaCreate, db: DbSession):
    if db.scalar(select(CategoriaReceita).where(CategoriaReceita.nome == payload.nome)):
        raise HTTPException(409, "Já existe categoria com este nome")
    obj = CategoriaReceita(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=CategoriaReceitaOut)
def atualizar(item_id: int, payload: CategoriaReceitaUpdate, db: DbSession):
    obj = db.get(CategoriaReceita, item_id)
    if not obj:
        raise HTTPException(404, "Categoria não encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(CategoriaReceita, item_id)
    if not obj:
        raise HTTPException(404, "Categoria não encontrada")
    obj.ativo = 0
    db.commit()
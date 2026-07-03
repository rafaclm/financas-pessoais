from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import Conta, Instituicao
from app.schemas.contas import ContaCreate, ContaUpdate, ContaOut

router = APIRouter(prefix="/contas", tags=["Cadastros - Contas"])


@router.get("", response_model=list[ContaOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(Conta).order_by(Conta.nome)
    if apenas_ativos:
        stmt = stmt.where(Conta.ativo == 1)
    return db.scalars(stmt).all()


@router.post("", response_model=ContaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ContaCreate, db: DbSession):
    if not db.get(Instituicao, payload.instituicao_id):
        raise HTTPException(400, "Instituição inválida")
    if db.scalar(select(Conta).where(Conta.nome == payload.nome)):
        raise HTTPException(409, "Já existe conta com este nome")
    obj = Conta(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=ContaOut)
def atualizar(item_id: int, payload: ContaUpdate, db: DbSession):
    obj = db.get(Conta, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrada")
    if payload.instituicao_id and not db.get(Instituicao, payload.instituicao_id):
        raise HTTPException(400, "Instituição inválida")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(Conta, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrada")
    obj.ativo = 0; db.commit()


# 🆕 REATIVAR
@router.post("/{item_id}/reativar", response_model=ContaOut)
def reativar(item_id: int, db: DbSession):
    obj = db.get(Conta, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrada")
    obj.ativo = 1
    db.commit(); db.refresh(obj)
    return obj
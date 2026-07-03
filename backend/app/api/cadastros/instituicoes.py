from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import Instituicao
from app.schemas.instituicoes import InstituicaoCreate, InstituicaoUpdate, InstituicaoOut

router = APIRouter(prefix="/instituicoes", tags=["Cadastros - Instituições"])


@router.get("", response_model=list[InstituicaoOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(Instituicao).order_by(Instituicao.nome)
    if apenas_ativos:
        stmt = stmt.where(Instituicao.ativo == 1)
    return db.scalars(stmt).all()


@router.post("", response_model=InstituicaoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: InstituicaoCreate, db: DbSession):
    if db.scalar(select(Instituicao).where(Instituicao.nome == payload.nome)):
        raise HTTPException(409, "Já existe instituição com este nome")
    obj = Instituicao(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=InstituicaoOut)
def atualizar(item_id: int, payload: InstituicaoUpdate, db: DbSession):
    obj = db.get(Instituicao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(Instituicao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrada")
    obj.ativo = 0; db.commit()


# 🆕 REATIVAR
@router.post("/{item_id}/reativar", response_model=InstituicaoOut)
def reativar(item_id: int, db: DbSession):
    obj = db.get(Instituicao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrada")
    obj.ativo = 1
    db.commit(); db.refresh(obj)
    return obj
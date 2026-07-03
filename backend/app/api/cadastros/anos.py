from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import Ano
from app.schemas.anos import AnoCreate, AnoUpdate, AnoOut

router = APIRouter(prefix="/anos", tags=["Cadastros - Anos"])


@router.get("", response_model=list[AnoOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(Ano).order_by(Ano.ano.desc())
    if apenas_ativos:
        stmt = stmt.where(Ano.ativo == 1)
    return db.scalars(stmt).all()


@router.get("/{ano_id}", response_model=AnoOut)
def obter(ano_id: int, db: DbSession):
    obj = db.get(Ano, ano_id)
    if not obj:
        raise HTTPException(404, "Ano não encontrado")
    return obj


@router.post("", response_model=AnoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: AnoCreate, db: DbSession):
    if db.scalar(select(Ano).where(Ano.ano == payload.ano)):
        raise HTTPException(409, "Ano já cadastrado")
    obj = Ano(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{ano_id}", response_model=AnoOut)
def atualizar(ano_id: int, payload: AnoUpdate, db: DbSession):
    obj = db.get(Ano, ano_id)
    if not obj:
        raise HTTPException(404, "Ano não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{ano_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(ano_id: int, db: DbSession):
    obj = db.get(Ano, ano_id)
    if not obj:
        raise HTTPException(404, "Ano não encontrado")
    obj.ativo = 0
    db.commit()


# 🆕 Endpoint para REATIVAR
@router.post("/{ano_id}/reativar", response_model=AnoOut)
def reativar(ano_id: int, db: DbSession):
    obj = db.get(Ano, ano_id)
    if not obj:
        raise HTTPException(404, "Ano não encontrado")
    obj.ativo = 1
    db.commit(); db.refresh(obj)
    return obj
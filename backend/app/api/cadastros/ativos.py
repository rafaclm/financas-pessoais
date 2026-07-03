from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import Ativo
from app.schemas.ativos import AtivoCreate, AtivoUpdate, AtivoOut

router = APIRouter(prefix="/ativos", tags=["Cadastros - Ativos"])


@router.get("", response_model=list[AtivoOut])
def listar(
    db: DbSession,
    apenas_ativos: bool = False,
    geografia: str | None = None,
    classe: str | None = None,
):
    stmt = select(Ativo).order_by(Ativo.ticker)
    if apenas_ativos:
        stmt = stmt.where(Ativo.ativo == 1)
    if geografia:
        stmt = stmt.where(Ativo.geografia == geografia)
    if classe:
        stmt = stmt.where(Ativo.classe == classe)
    return db.scalars(stmt).all()


@router.post("", response_model=AtivoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: AtivoCreate, db: DbSession):
    if db.scalar(select(Ativo).where(Ativo.ticker == payload.ticker.upper())):
        raise HTTPException(409, "Ticker já cadastrado")
    data = payload.model_dump()
    data["ticker"] = data["ticker"].upper()
    obj = Ativo(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=AtivoOut)
def atualizar(item_id: int, payload: AtivoUpdate, db: DbSession):
    obj = db.get(Ativo, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "ticker" in data:
        data["ticker"] = data["ticker"].upper()
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(Ativo, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    obj.ativo = 0; db.commit()


# 🆕 REATIVAR
@router.post("/{item_id}/reativar", response_model=AtivoOut)
def reativar(item_id: int, db: DbSession):
    obj = db.get(Ativo, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    obj.ativo = 1
    db.commit(); db.refresh(obj)
    return obj
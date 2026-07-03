from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import (
    BalanceamentoGeografia, BalanceamentoClasse, BalanceamentoAtivo, Ativo
)
from app.schemas.balanceamento import (
    BalanceamentoGeografiaCreate, BalanceamentoGeografiaUpdate, BalanceamentoGeografiaOut,
    BalanceamentoClasseCreate, BalanceamentoClasseUpdate, BalanceamentoClasseOut,
    BalanceamentoAtivoCreate, BalanceamentoAtivoUpdate, BalanceamentoAtivoOut,
)

router = APIRouter(prefix="/balanceamento/config", tags=["Balanceamento - Configuracao"])


# ============================================================
# NÍVEL 1 — GEOGRAFIA
# ============================================================

@router.get("/geografia", response_model=list[BalanceamentoGeografiaOut])
def listar_geografia(db: DbSession):
    return db.scalars(
        select(BalanceamentoGeografia).order_by(BalanceamentoGeografia.geografia)
    ).all()


@router.post("/geografia", response_model=BalanceamentoGeografiaOut, status_code=status.HTTP_201_CREATED)
def criar_geografia(payload: BalanceamentoGeografiaCreate, db: DbSession):
    existe = db.scalar(
        select(BalanceamentoGeografia).where(BalanceamentoGeografia.geografia == payload.geografia)
    )
    if existe:
        raise HTTPException(409, "Geografia já configurada (use PUT para atualizar)")
    obj = BalanceamentoGeografia(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/geografia/{item_id}", response_model=BalanceamentoGeografiaOut)
def atualizar_geografia(item_id: int, payload: BalanceamentoGeografiaUpdate, db: DbSession):
    obj = db.get(BalanceamentoGeografia, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/geografia/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_geografia(item_id: int, db: DbSession):
    obj = db.get(BalanceamentoGeografia, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()


# ============================================================
# NÍVEL 2 — CLASSE
# ============================================================

@router.get("/classe", response_model=list[BalanceamentoClasseOut])
def listar_classe(db: DbSession, geografia: str | None = None):
    stmt = select(BalanceamentoClasse).order_by(
        BalanceamentoClasse.geografia, BalanceamentoClasse.classe
    )
    if geografia:
        stmt = stmt.where(BalanceamentoClasse.geografia == geografia)
    return db.scalars(stmt).all()


@router.post("/classe", response_model=BalanceamentoClasseOut, status_code=status.HTTP_201_CREATED)
def criar_classe(payload: BalanceamentoClasseCreate, db: DbSession):
    existe = db.scalar(select(BalanceamentoClasse).where(
        BalanceamentoClasse.geografia == payload.geografia,
        BalanceamentoClasse.classe == payload.classe,
    ))
    if existe:
        raise HTTPException(409, "Classe já configurada para esta geografia")
    obj = BalanceamentoClasse(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/classe/{item_id}", response_model=BalanceamentoClasseOut)
def atualizar_classe(item_id: int, payload: BalanceamentoClasseUpdate, db: DbSession):
    obj = db.get(BalanceamentoClasse, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/classe/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_classe(item_id: int, db: DbSession):
    obj = db.get(BalanceamentoClasse, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()


# ============================================================
# NÍVEL 3 — ATIVO INDIVIDUAL
# ============================================================

@router.get("/ativo", response_model=list[BalanceamentoAtivoOut])
def listar_ativo(db: DbSession):
    return db.scalars(select(BalanceamentoAtivo)).all()


@router.post("/ativo", response_model=BalanceamentoAtivoOut, status_code=status.HTTP_201_CREATED)
def criar_ativo(payload: BalanceamentoAtivoCreate, db: DbSession):
    if not db.get(Ativo, payload.ativo_id):
        raise HTTPException(400, "Ativo inválido")
    existe = db.scalar(select(BalanceamentoAtivo).where(
        BalanceamentoAtivo.ativo_id == payload.ativo_id
    ))
    if existe:
        raise HTTPException(409, "Este ativo já possui meta configurada")
    obj = BalanceamentoAtivo(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/ativo/{item_id}", response_model=BalanceamentoAtivoOut)
def atualizar_ativo(item_id: int, payload: BalanceamentoAtivoUpdate, db: DbSession):
    obj = db.get(BalanceamentoAtivo, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/ativo/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_ativo(item_id: int, db: DbSession):
    obj = db.get(BalanceamentoAtivo, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()
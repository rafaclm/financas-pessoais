from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, and_
from app.api.deps import DbSession
from app.infrastructure.db.models import (
    SaldoInvestimento, ProdutoInvestimento, Ano
)
from app.schemas.saldos_investimentos import (
    SaldoInvestimentoCreate, SaldoInvestimentoUpdate,
    SaldoInvestimentoOut, SaldoInvestimentoLote
)
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/saldos-investimentos", tags=["Posicoes - Saldos de Investimentos"])


@router.get("", response_model=list[SaldoInvestimentoOut])
def listar(db: DbSession, ano_id: int, mes: int):
    stmt = select(SaldoInvestimento).where(
        SaldoInvestimento.ano_id == ano_id,
        SaldoInvestimento.mes == mes,
    )
    return db.scalars(stmt).all()


@router.get("/com-variacao")
def listar_com_variacao(db: DbSession, ano_id: int, mes: int):
    """
    Retorna saldos do periodo + variacao em relacao ao mes anterior.
    """
    # Determina o periodo anterior
    if mes == 1:
        mes_ant = 12
        ano_obj_atual = db.get(Ano, ano_id)
        if not ano_obj_atual:
            raise HTTPException(400, "Ano invalido")
        ano_ant = db.scalar(select(Ano).where(Ano.ano == ano_obj_atual.ano - 1))
        ano_id_ant = ano_ant.id if ano_ant else None
    else:
        mes_ant = mes - 1
        ano_id_ant = ano_id

    # Busca todos os produtos ativos
    produtos = db.scalars(
        select(ProdutoInvestimento).where(ProdutoInvestimento.ativo == 1)
    ).all()

    # Busca saldos do periodo atual
    saldos_atuais = db.scalars(
        select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == ano_id,
            SaldoInvestimento.mes == mes,
        )
    ).all()
    map_atual = {s.produto_id: s for s in saldos_atuais}

    # Busca saldos do periodo anterior
    map_anterior = {}
    if ano_id_ant is not None:
        saldos_anteriores = db.scalars(
            select(SaldoInvestimento).where(
                SaldoInvestimento.ano_id == ano_id_ant,
                SaldoInvestimento.mes == mes_ant,
            )
        ).all()
        map_anterior = {s.produto_id: s for s in saldos_anteriores}

    # Monta resultado
    resultado = []
    for produto in produtos:
        saldo_atual = map_atual.get(produto.id)
        saldo_ant = map_anterior.get(produto.id)

        saldo_brl_atual = float(saldo_atual.saldo_brl) if saldo_atual else 0
        saldo_brl_ant = float(saldo_ant.saldo_brl) if saldo_ant else 0

        # Calcula variacao
        variacao_valor = None
        variacao_pct = None
        if saldo_ant is not None and saldo_brl_ant > 0:
            variacao_valor = round(saldo_brl_atual - saldo_brl_ant, 2)
            variacao_pct = round((saldo_brl_atual - saldo_brl_ant) / saldo_brl_ant * 100, 2)

        resultado.append({
            "produto_id": produto.id,
            "produto_nome": produto.nome,
            "produto_categoria": produto.categoria,
            "produto_moeda": produto.moeda,
            "saldo_id": saldo_atual.id if saldo_atual else None,
            "saldo": float(saldo_atual.saldo) if saldo_atual else 0,
            "cotacao_usd_brl": float(saldo_atual.cotacao_usd_brl) if saldo_atual and saldo_atual.cotacao_usd_brl else None,
            "saldo_brl": saldo_brl_atual,
            "saldo_brl_mes_anterior": saldo_brl_ant,
            "variacao_valor": variacao_valor,
            "variacao_pct": variacao_pct,
            "existe": saldo_atual is not None,
        })

    return resultado


@router.post("", response_model=SaldoInvestimentoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: SaldoInvestimentoCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano invalido")
    if not db.get(ProdutoInvestimento, payload.produto_id):
        raise HTTPException(400, "Produto invalido")

    existente = db.scalar(select(SaldoInvestimento).where(
        SaldoInvestimento.ano_id == payload.ano_id,
        SaldoInvestimento.mes == payload.mes,
        SaldoInvestimento.produto_id == payload.produto_id,
    ))
    if existente:
        raise HTTPException(409, "Ja existe saldo para este produto neste periodo")

    produto = db.get(ProdutoInvestimento, payload.produto_id)
    saldo_brl = payload.saldo
    cotacao = payload.cotacao_usd_brl
    if produto.moeda == "USD":
        if not cotacao:
            cotacao = obter_ou_buscar_cotacao(db, payload.ano_id, payload.mes)
        if not cotacao:
            raise HTTPException(400, "Nao foi possivel obter cotacao USD/BRL")
        saldo_brl = payload.saldo * float(cotacao)

    obj = SaldoInvestimento(
        ano_id=payload.ano_id,
        mes=payload.mes,
        produto_id=payload.produto_id,
        saldo=payload.saldo,
        cotacao_usd_brl=cotacao,
        saldo_brl=saldo_brl,
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=SaldoInvestimentoOut)
def atualizar(item_id: int, payload: SaldoInvestimentoUpdate, db: DbSession):
    obj = db.get(SaldoInvestimento, item_id)
    if not obj:
        raise HTTPException(404, "Nao encontrado")

    produto = db.get(ProdutoInvestimento, obj.produto_id)

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)

    saldo = obj.saldo
    cotacao = obj.cotacao_usd_brl
    if produto.moeda == "USD":
        if not cotacao:
            cotacao = obter_ou_buscar_cotacao(db, obj.ano_id, obj.mes)
        obj.cotacao_usd_brl = cotacao
        if cotacao:
            obj.saldo_brl = float(saldo) * float(cotacao)
    else:
        obj.saldo_brl = saldo

    db.commit(); db.refresh(obj)
    return obj


@router.post("/lote", response_model=list[SaldoInvestimentoOut])
def lote(db: DbSession, payload: SaldoInvestimentoLote):
    """Insere ou atualiza varios saldos de uma vez."""
    resultado = []
    for item in payload.itens:
        produto = db.get(ProdutoInvestimento, item.produto_id)
        if not produto:
            continue

        saldo_brl = item.saldo
        cotacao = item.cotacao_usd_brl
        if produto.moeda == "USD":
            if not cotacao:
                cotacao = obter_ou_buscar_cotacao(db, item.ano_id, item.mes)
            if cotacao:
                saldo_brl = item.saldo * float(cotacao)

        existente = db.scalar(select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == item.ano_id,
            SaldoInvestimento.mes == item.mes,
            SaldoInvestimento.produto_id == item.produto_id,
        ))

        if existente:
            existente.saldo = item.saldo
            existente.cotacao_usd_brl = cotacao
            existente.saldo_brl = saldo_brl
            resultado.append(existente)
        else:
            novo = SaldoInvestimento(
                ano_id=item.ano_id, mes=item.mes, produto_id=item.produto_id,
                saldo=item.saldo, cotacao_usd_brl=cotacao, saldo_brl=saldo_brl,
            )
            db.add(novo)
            resultado.append(novo)

    db.commit()
    for r in resultado:
        db.refresh(r)
    return resultado


@router.post("/replicar-mes-anterior")
def replicar(db: DbSession, ano_id: int, mes: int):
    """Copia os saldos do mes anterior para o mes atual."""
    if mes == 1:
        mes_ant = 12
        ano_obj = db.get(Ano, ano_id)
        ano_ant = db.scalar(select(Ano).where(Ano.ano == ano_obj.ano - 1))
        if not ano_ant:
            return {"mensagem": "Nao ha ano anterior cadastrado", "replicados": 0}
        ano_id_ant = ano_ant.id
    else:
        mes_ant = mes - 1
        ano_id_ant = ano_id

    saldos_ant = db.scalars(
        select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == ano_id_ant,
            SaldoInvestimento.mes == mes_ant,
        )
    ).all()

    novos = 0
    for s in saldos_ant:
        ja_existe = db.scalar(select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == ano_id,
            SaldoInvestimento.mes == mes,
            SaldoInvestimento.produto_id == s.produto_id,
        ))
        if ja_existe:
            continue
        db.add(SaldoInvestimento(
            ano_id=ano_id, mes=mes, produto_id=s.produto_id,
            saldo=s.saldo, cotacao_usd_brl=s.cotacao_usd_brl, saldo_brl=s.saldo_brl,
        ))
        novos += 1
    db.commit()
    return {"mensagem": f"Replicados {novos} saldos", "replicados": novos}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(SaldoInvestimento, item_id)
    if not obj:
        raise HTTPException(404, "Nao encontrado")
    db.delete(obj); db.commit()
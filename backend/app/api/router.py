from fastapi import APIRouter

# 🆕 Autenticacao
from app.api.auth import router as auth_router

# Cadastros (Fase A)
from app.api.cadastros import (
    anos, categorias_despesas, categorias_receitas, instituicoes,
    contas, cartoes, produtos, ativos,
)

# Lançamentos (Fase B)
from app.api.lancamentos import (
    receitas, despesas, combustivel, pagamentos_cartao,
    aportes, proventos, cotacoes, replicar, resumo,
)

# Posições e Consolidação (Fase C)
from app.api.posicoes import (
    saldos_contas, saldos_investimentos, cripto, ativos_br, ativos_eua,
    consolidacao,
)

# Balanceamento (Fase D)
from app.api.balanceamento import config as balanc_config, analise as balanc_analise

# Posição Atual (Fase D+)
from app.api.posicao_atual import router as posicao_atual_router

# Backup (Fase E.1)
from app.api.backup import router as backup_router

# Importação (Fase E.2)
from app.api.importacao import router as importacao_router

# Dashboard (Fase F)
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")

# 🆕 Autenticacao (nao exige login)
api_router.include_router(auth_router.router)

# Cadastros
api_router.include_router(anos.router)
api_router.include_router(categorias_despesas.router)
api_router.include_router(categorias_receitas.router)
api_router.include_router(instituicoes.router)
api_router.include_router(contas.router)
api_router.include_router(cartoes.router)
api_router.include_router(produtos.router)
api_router.include_router(ativos.router)

# Lançamentos
api_router.include_router(receitas.router)
api_router.include_router(despesas.router)
api_router.include_router(combustivel.router)
api_router.include_router(pagamentos_cartao.router)
api_router.include_router(aportes.router)
api_router.include_router(proventos.router)
api_router.include_router(cotacoes.router)
api_router.include_router(replicar.router)
api_router.include_router(resumo.router)

# Posições
api_router.include_router(saldos_contas.router)
api_router.include_router(saldos_investimentos.router)
api_router.include_router(cripto.router)
api_router.include_router(ativos_br.router)
api_router.include_router(ativos_eua.router)
api_router.include_router(consolidacao.router)

# Balanceamento
api_router.include_router(balanc_config.router)
api_router.include_router(balanc_analise.router)

# Posição Atual
api_router.include_router(posicao_atual_router.router)

# Backup
api_router.include_router(backup_router.router)

# Importação
api_router.include_router(importacao_router.router)

# Dashboard
api_router.include_router(dashboard_router.router)
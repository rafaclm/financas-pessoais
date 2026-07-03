from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.api.deps import DbSession
from app.schemas.importacao import (
    AnaliseArquivo, RelatorioImportacao, ExploradorRelatorio,
    PayloadImportarMovimentos, RelatorioMovimentos
)
from app.services.importacao.leitor_excel import (
    carregar_workbook, analisar_planilha
)
from app.services.importacao.importacao_ativos import importar_ativos
from app.services.importacao.explorador import explorar_aba_anual
from app.services.importacao.importacao_movimentos import importar_movimentos_multi_anos
from app.services.importacao.importacao_aportes import (
    analisar_aba_aportes, importar_aportes
)
from app.services.importacao.importacao_proventos import (
    analisar_aba_proventos, importar_proventos
)
from app.services.importacao.importacao_contas import (
    garantir_categorias, garantir_contas_basicas,
    garantir_cartoes_basicos, garantir_produtos_investimento,
)
from app.services.backup import criar_backup

router = APIRouter(prefix="/importacao", tags=["Importacao de Planilha"])

_arquivo_cache: dict = {}


@router.post("/analisar", response_model=AnaliseArquivo)
async def analisar(arquivo: UploadFile = File(...)):
    if not arquivo.filename or not arquivo.filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Arquivo deve ser .xlsx")
    dados = await arquivo.read()
    if len(dados) == 0:
        raise HTTPException(400, "Arquivo vazio")
    if len(dados) > 100 * 1024 * 1024:
        raise HTTPException(400, "Arquivo muito grande (max 100MB)")
    _arquivo_cache[arquivo.filename] = {
        "dados": dados, "uploaded_at": datetime.now(),
        "nome": arquivo.filename,
    }
    try:
        return analisar_planilha(dados)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/preview-ativos", response_model=RelatorioImportacao)
def preview_ativos(db: DbSession, nome_arquivo: str = Form(...)):
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    wb = carregar_workbook(cache["dados"])
    resultado = importar_ativos(db, wb, dry_run=True)
    return RelatorioImportacao(
        timestamp=datetime.now(), backup_seguranca=None,
        blocos={"ativos": resultado.__dict__},
        sucesso_geral=resultado.erros == 0,
        mensagem_final=f"PREVIEW: {resultado.mensagem}",
    )


@router.post("/executar-ativos", response_model=RelatorioImportacao)
def executar_ativos(db: DbSession, nome_arquivo: str = Form(...)):
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    backup_info = criar_backup(descricao=f"Auto antes Ativos de '{nome_arquivo}'")
    wb = carregar_workbook(cache["dados"])
    resultado = importar_ativos(db, wb, dry_run=False)
    return RelatorioImportacao(
        timestamp=datetime.now(), backup_seguranca=backup_info["nome"],
        blocos={"ativos": resultado.__dict__},
        sucesso_geral=resultado.erros == 0,
        mensagem_final=f"EXECUCAO: {resultado.mensagem}",
    )


@router.post("/explorar/{nome_aba}", response_model=ExploradorRelatorio)
def explorar(nome_aba: str, nome_arquivo: str = Form(...)):
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    wb = carregar_workbook(cache["dados"])
    try:
        return ExploradorRelatorio(aba=nome_aba, dados=explorar_aba_anual(wb, nome_aba))
    except Exception as e:
        raise HTTPException(500, f"Erro: {e}")


@router.post("/preview-movimentos", response_model=RelatorioMovimentos)
def preview_movimentos(payload: PayloadImportarMovimentos, db: DbSession):
    cache = _arquivo_cache.get(payload.nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    garantir_categorias(db)
    garantir_contas_basicas(db)
    garantir_cartoes_basicos(db)
    garantir_produtos_investimento(db)
    wb = carregar_workbook(cache["dados"])
    relatorio = importar_movimentos_multi_anos(
        db, wb, payload.anos, payload.blocos, dry_run=True
    )
    total_inseridos = 0
    for ano_data in relatorio.values():
        if isinstance(ano_data, dict) and "erro" not in ano_data:
            for bloco_res in ano_data.values():
                if hasattr(bloco_res, "inseridos"):
                    total_inseridos += bloco_res.inseridos
                elif isinstance(bloco_res, dict):
                    total_inseridos += bloco_res.get("inseridos", 0)
    relatorio_serializado = {}
    for ano, dados in relatorio.items():
        if "erro" in dados:
            relatorio_serializado[ano] = dados
        else:
            relatorio_serializado[ano] = {
                k: (v.__dict__ if hasattr(v, "__dict__") else v)
                for k, v in dados.items()
            }
    return RelatorioMovimentos(
        timestamp=datetime.now(), backup_seguranca=None, dry_run=True,
        relatorio_por_ano=relatorio_serializado,
        mensagem_final=f"PREVIEW: {total_inseridos} registros",
    )


@router.post("/executar-movimentos", response_model=RelatorioMovimentos)
def executar_movimentos(payload: PayloadImportarMovimentos, db: DbSession):
    cache = _arquivo_cache.get(payload.nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    backup_info = criar_backup(
        descricao=f"Auto antes Movimentos anos {payload.anos}"
    )
    garantir_categorias(db)
    garantir_contas_basicas(db)
    garantir_cartoes_basicos(db)
    garantir_produtos_investimento(db)
    wb = carregar_workbook(cache["dados"])
    relatorio = importar_movimentos_multi_anos(
        db, wb, payload.anos, payload.blocos, dry_run=False
    )
    total_inseridos = 0
    for ano_data in relatorio.values():
        if isinstance(ano_data, dict) and "erro" not in ano_data:
            for bloco_res in ano_data.values():
                if hasattr(bloco_res, "inseridos"):
                    total_inseridos += bloco_res.inseridos
                elif isinstance(bloco_res, dict):
                    total_inseridos += bloco_res.get("inseridos", 0)
    relatorio_serializado = {}
    for ano, dados in relatorio.items():
        if "erro" in dados:
            relatorio_serializado[ano] = dados
        else:
            relatorio_serializado[ano] = {
                k: (v.__dict__ if hasattr(v, "__dict__") else v)
                for k, v in dados.items()
            }
    return RelatorioMovimentos(
        timestamp=datetime.now(), backup_seguranca=backup_info["nome"],
        dry_run=False, relatorio_por_ano=relatorio_serializado,
        mensagem_final=f"EXECUCAO: {total_inseridos} registros inseridos",
    )


# ============================================================
# APORTES
# ============================================================

@router.post("/analisar-aportes")
def analisar_aportes_endpoint(db: DbSession, nome_arquivo: str = Form(...)):
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    wb = carregar_workbook(cache["dados"])
    return analisar_aba_aportes(db, wb)


@router.post("/preview-aportes")
def preview_aportes_endpoint(db: DbSession, nome_arquivo: str = Form(...)):
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    wb = carregar_workbook(cache["dados"])
    resultado = importar_aportes(db, wb, criar_tickers_novos=False, dry_run=True)
    return {
        "timestamp": datetime.now().isoformat(),
        "backup_seguranca": None,
        "dry_run": True,
        "resultado": resultado,
        "mensagem_final": f"PREVIEW: {resultado.get('mensagem', 'sem dados')}",
    }


@router.post("/executar-aportes")
def executar_aportes_endpoint(
    db: DbSession,
    nome_arquivo: str = Form(...),
    criar_tickers_novos: bool = Form(default=True),
):
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    backup_info = criar_backup(descricao=f"Auto antes Aportes de '{nome_arquivo}'")
    wb = carregar_workbook(cache["dados"])
    resultado = importar_aportes(
        db, wb, criar_tickers_novos=criar_tickers_novos, dry_run=False
    )
    return {
        "timestamp": datetime.now().isoformat(),
        "backup_seguranca": backup_info["nome"],
        "dry_run": False,
        "resultado": resultado,
        "mensagem_final": f"EXECUCAO: {resultado.get('mensagem', 'sem dados')}",
    }


# ============================================================
# 🆕 PROVENTOS
# ============================================================

@router.post("/analisar-proventos")
def analisar_proventos_endpoint(db: DbSession, nome_arquivo: str = Form(...)):
    """Analisa a aba 'Proventos'."""
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    wb = carregar_workbook(cache["dados"])
    return analisar_aba_proventos(db, wb)


@router.post("/preview-proventos")
def preview_proventos_endpoint(db: DbSession, nome_arquivo: str = Form(...)):
    """Preview (dry-run) da importacao de proventos."""
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    wb = carregar_workbook(cache["dados"])
    resultado = importar_proventos(
        db, wb, criar_tickers_novos=False, dry_run=True
    )
    return {
        "timestamp": datetime.now().isoformat(),
        "backup_seguranca": None,
        "dry_run": True,
        "resultado": resultado,
        "mensagem_final": f"PREVIEW: {resultado.get('mensagem', 'sem dados')}",
    }


@router.post("/executar-proventos")
def executar_proventos_endpoint(
    db: DbSession,
    nome_arquivo: str = Form(...),
    criar_tickers_novos: bool = Form(default=True),
):
    """Executa importacao de proventos com backup."""
    cache = _arquivo_cache.get(nome_arquivo)
    if not cache:
        raise HTTPException(404, "Arquivo nao em cache")
    backup_info = criar_backup(descricao=f"Auto antes Proventos de '{nome_arquivo}'")
    wb = carregar_workbook(cache["dados"])
    resultado = importar_proventos(
        db, wb, criar_tickers_novos=criar_tickers_novos, dry_run=False
    )
    return {
        "timestamp": datetime.now().isoformat(),
        "backup_seguranca": backup_info["nome"],
        "dry_run": False,
        "resultado": resultado,
        "mensagem_final": f"EXECUCAO: {resultado.get('mensagem', 'sem dados')}",
    }
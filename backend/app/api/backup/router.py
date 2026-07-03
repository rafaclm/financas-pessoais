from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.schemas.backup import (
    BackupInfo, CriarBackupPayload, ResultadoBackup, ResultadoRestauracao
)
from app.services.backup import (
    listar_backups, criar_backup, deletar_backup,
    restaurar_backup, caminho_backup, importar_backup_externo
)

router = APIRouter(prefix="/backup", tags=["Backup e Restore"])


@router.get("", response_model=list[BackupInfo])
def listar():
    """Lista todos os backups disponíveis."""
    return listar_backups()


@router.post("", response_model=ResultadoBackup, status_code=status.HTTP_201_CREATED)
def criar(payload: CriarBackupPayload):
    """Cria um novo backup do banco de dados."""
    try:
        return criar_backup(payload.descricao)
    except Exception as e:
        raise HTTPException(500, f"Erro ao criar backup: {e}")


@router.get("/{nome}/download")
def download(nome: str):
    """Baixa o arquivo de um backup."""
    try:
        path = caminho_backup(nome)
    except FileNotFoundError:
        raise HTTPException(404, "Backup não encontrado")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return FileResponse(
        path=str(path),
        filename=nome,
        media_type="application/octet-stream",
    )


@router.delete("/{nome}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(nome: str):
    """Remove um backup."""
    try:
        deletar_backup(nome)
    except FileNotFoundError:
        raise HTTPException(404, "Backup não encontrado")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{nome}/restaurar", response_model=ResultadoRestauracao)
def restaurar(nome: str):
    """
    Restaura o banco a partir de um backup.
    ⚠️ Cria um backup de segurança automaticamente antes de restaurar.
    """
    try:
        return restaurar_backup(nome)
    except FileNotFoundError:
        raise HTTPException(404, "Backup não encontrado")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Erro ao restaurar: {e}")


@router.post("/upload", response_model=ResultadoBackup)
async def upload_backup(
    arquivo: UploadFile = File(...),
    descricao: str | None = Form(default=None),
):
    """
    Faz upload de um arquivo .db externo e o salva como um backup.
    (Não restaura — apenas adiciona à lista de backups disponíveis.)
    """
    if not arquivo.filename or not arquivo.filename.endswith(".db"):
        raise HTTPException(400, "Arquivo deve ter extensão .db")

    dados = await arquivo.read()
    if len(dados) == 0:
        raise HTTPException(400, "Arquivo vazio")
    if len(dados) > 200 * 1024 * 1024:  # 200 MB limite
        raise HTTPException(400, "Arquivo muito grande (máx. 200MB)")

    try:
        return importar_backup_externo(arquivo.filename, dados, descricao)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Erro ao importar: {e}")
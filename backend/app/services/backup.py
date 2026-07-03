"""
Service de Backup e Restore do banco de dados.
- Cria backups consistentes usando sqlite3.backup() (atomico)
- Mantem metadados (descricao) em arquivo .json paralelo
- Antes de qualquer restore, cria backup de seguranca automaticamente
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from loguru import logger
from app.core.config import settings


BACKUP_DIR = Path("data/backups")


def garantir_pasta_backup() -> Path:
    """Garante que a pasta de backups existe."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def _tamanho_legivel(bytes_size: int) -> str:
    """Converte bytes em formato legivel (KB, MB)."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    if bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    return f"{bytes_size / (1024 * 1024):.2f} MB"


def listar_backups() -> list[dict]:
    """Lista todos os backups disponiveis com metadados."""
    garantir_pasta_backup()
    backups = []
    for arquivo in sorted(BACKUP_DIR.glob("*.db"), reverse=True):
        meta_file = arquivo.with_suffix(".json")
        descricao = None
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                descricao = meta.get("descricao")
            except Exception:
                pass
        stat = arquivo.stat()
        backups.append({
            "nome": arquivo.name,
            "tamanho_bytes": stat.st_size,
            "tamanho_legivel": _tamanho_legivel(stat.st_size),
            "criado_em": datetime.fromtimestamp(stat.st_mtime),
            "descricao": descricao,
        })
    return backups


def criar_backup(descricao: str | None = None) -> dict:
    """
    Cria um backup do banco usando sqlite3.backup() (atomico e consistente).
    Retorna informacoes do backup criado.
    """
    garantir_pasta_backup()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome = f"financas_{timestamp}.db"
    destino = BACKUP_DIR / nome

    db_path = str(settings.db_path)
    logger.info(f"Criando backup: {nome}")

    src_conn = sqlite3.connect(db_path)
    try:
        dst_conn = sqlite3.connect(str(destino))
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    if descricao:
        meta = {
            "descricao": descricao,
            "criado_em": datetime.now().isoformat(),
            "origem": "manual",
        }
        destino.with_suffix(".json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8"
        )

    tamanho = destino.stat().st_size
    return {
        "nome": nome,
        "tamanho_bytes": tamanho,
        "tamanho_legivel": _tamanho_legivel(tamanho),
        "descricao": descricao,
        "mensagem": f"Backup {nome} criado com sucesso.",
    }


def deletar_backup(nome: str) -> None:
    """Remove um arquivo de backup e seus metadados."""
    garantir_pasta_backup()
    if "/" in nome or "\\" in nome or ".." in nome or not nome.endswith(".db"):
        raise ValueError("Nome de backup invalido")

    arquivo = BACKUP_DIR / nome
    if not arquivo.exists():
        raise FileNotFoundError("Backup nao encontrado")

    arquivo.unlink()
    meta = arquivo.with_suffix(".json")
    if meta.exists():
        meta.unlink()
    logger.info(f"Backup deletado: {nome}")


def caminho_backup(nome: str) -> Path:
    """Retorna o Path completo de um backup (para download)."""
    garantir_pasta_backup()
    if "/" in nome or "\\" in nome or ".." in nome or not nome.endswith(".db"):
        raise ValueError("Nome de backup invalido")
    arquivo = BACKUP_DIR / nome
    if not arquivo.exists():
        raise FileNotFoundError("Backup nao encontrado")
    return arquivo


def restaurar_backup(nome: str) -> dict:
    """
    Restaura um backup.
    Antes de restaurar, cria um backup de seguranca do estado atual.
    Apos a restauracao, o backend precisa ser REINICIADO para reabrir conexoes.
    """
    garantir_pasta_backup()
    origem = caminho_backup(nome)

    backup_seguranca = criar_backup(
        descricao=f"Auto-backup antes de restaurar {nome}"
    )

    from app.core.database import engine
    engine.dispose()

    shutil.copy2(origem, str(settings.db_path))

    logger.warning(f"Banco restaurado a partir de {nome}")

    return {
        "mensagem": f"Banco restaurado a partir de '{nome}' com sucesso.",
        "backup_seguranca_criado": backup_seguranca["nome"],
        "aviso": (
            "Recomendacao importante: reinicie o backend "
            "(Ctrl+C no terminal e rode 'uvicorn app.main:app --port 8080' novamente) "
            "para garantir que todas as conexoes sejam reabertas corretamente."
        ),
    }


def importar_backup_externo(nome_destino: str, dados_binarios: bytes, descricao: str | None = None) -> dict:
    """
    Salva um arquivo .db enviado pelo usuario como um novo backup.
    """
    garantir_pasta_backup()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_seguro = f"importado_{timestamp}.db"
    destino = BACKUP_DIR / nome_seguro
    destino.write_bytes(dados_binarios)

    try:
        conn = sqlite3.connect(str(destino))
        conn.execute("PRAGMA integrity_check")
        conn.close()
    except Exception as e:
        destino.unlink()
        raise ValueError(f"Arquivo nao e um banco SQLite valido: {e}")

    if descricao:
        meta = {
            "descricao": descricao,
            "criado_em": datetime.now().isoformat(),
            "origem": "upload",
        }
        destino.with_suffix(".json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8"
        )

    tamanho = destino.stat().st_size
    return {
        "nome": nome_seguro,
        "tamanho_bytes": tamanho,
        "tamanho_legivel": _tamanho_legivel(tamanho),
        "descricao": descricao,
        "mensagem": f"Backup externo importado como '{nome_seguro}'.",
    }
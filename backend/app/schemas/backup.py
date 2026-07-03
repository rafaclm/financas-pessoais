from datetime import datetime
from pydantic import Field
from app.schemas.common import ORMBase


class BackupInfo(ORMBase):
    nome: str
    tamanho_bytes: int
    tamanho_legivel: str
    criado_em: datetime
    descricao: str | None = None


class CriarBackupPayload(ORMBase):
    descricao: str | None = Field(default=None, max_length=200)


class ResultadoBackup(ORMBase):
    nome: str
    tamanho_bytes: int
    tamanho_legivel: str
    descricao: str | None = None
    mensagem: str


class ResultadoRestauracao(ORMBase):
    mensagem: str
    backup_seguranca_criado: str
    aviso: str
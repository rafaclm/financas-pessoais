from datetime import datetime
from typing import Any
from pydantic import Field
from app.schemas.common import ORMBase


class AbaInfo(ORMBase):
    nome: str
    max_row: int
    max_column: int
    tipo_detectado: str


class AnaliseArquivo(ORMBase):
    total_abas: int
    abas: list[AbaInfo]


class ResultadoBlocoImportacao(ORMBase):
    inseridos: int
    atualizados: int
    pulados: int
    erros: int
    detalhes_inseridos: list[str] = []
    detalhes_erros: list[str] = []
    mensagem: str


class RelatorioImportacao(ORMBase):
    timestamp: datetime
    backup_seguranca: str | None = None
    blocos: dict
    sucesso_geral: bool
    mensagem_final: str


class ExploradorRelatorio(ORMBase):
    aba: str
    dados: dict[str, Any]


class PayloadImportarMovimentos(ORMBase):
    nome_arquivo: str
    anos: list[int]
    blocos: list[str]


class RelatorioMovimentos(ORMBase):
    timestamp: datetime
    backup_seguranca: str | None = None
    dry_run: bool
    relatorio_por_ano: dict[str, Any]
    mensagem_final: str
"""
Estruturas base e helpers compartilhados entre importadores.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ResultadoImportacao:
    """Resultado padronizado de cada importador."""
    inseridos: int = 0
    atualizados: int = 0
    pulados: int = 0
    erros: int = 0
    detalhes_inseridos: list = field(default_factory=list)
    detalhes_erros: list = field(default_factory=list)
    mensagem: str = ""


def normalizar_ticker(ticker: str | None) -> str | None:
    """Padroniza tickers (upper, sem espacos)."""
    if not ticker:
        return None
    return str(ticker).strip().upper()


def parse_data(valor) -> datetime | None:
    """Tenta converter um valor (str/datetime/None) em datetime."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    try:
        # Formato "07/mai/26"
        meses = {
            "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
            "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
        }
        s = str(valor).strip().lower()
        partes = s.replace("-", "/").replace(".", "/").split("/")
        if len(partes) == 3:
            dia = int(partes[0])
            mes_str = partes[1].strip()
            if mes_str.isdigit():
                mes = int(mes_str)
            else:
                # "mai" → 5
                mes = meses.get(mes_str[:3], None)
                if not mes:
                    return None
            ano_str = partes[2].strip()
            ano = int(ano_str)
            if ano < 100:
                ano += 2000  # "26" → 2026
            return datetime(ano, mes, dia)
    except Exception:
        return None
    return None


def parse_periodo(valor) -> tuple[int, int] | None:
    """Converte '2026/4' em (2026, 4)."""
    if valor is None:
        return None
    try:
        s = str(valor).strip().replace("-", "/")
        partes = s.split("/")
        if len(partes) == 2:
            ano = int(partes[0])
            mes = int(partes[1])
            if 2000 <= ano <= 2100 and 1 <= mes <= 12:
                return (ano, mes)
    except Exception:
        return None
    return None


def parse_numero(valor) -> float | None:
    """Converte valor em float. Trata casos comuns de planilha."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        s = str(valor).strip().replace(".", "").replace(",", ".")
        # Remove R$, US$, $, %
        for char in ["R$", "US$", "$", "%", " "]:
            s = s.replace(char, "")
        if s in ("", "-", "—"):
            return None
        return float(s)
    except Exception:
        return None
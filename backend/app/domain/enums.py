from enum import StrEnum


class TipoCategoriaDespesa(StrEnum):
    FIXA = "fixa"
    VARIAVEL = "variavel"


class RecorrenciaReceita(StrEnum):
    RECORRENTE = "recorrente"
    EVENTUAL = "eventual"


class TipoInstituicao(StrEnum):
    BANCO = "banco"
    CORRETORA = "corretora"
    EXCHANGE = "exchange"
    OUTRO = "outro"


class TipoConta(StrEnum):
    CORRENTE = "corrente"
    INVESTIMENTO = "investimento"
    INTERNACIONAL = "internacional"
    OUTRO = "outro"


class Moeda(StrEnum):
    BRL = "BRL"
    USD = "USD"


class CategoriaProduto(StrEnum):
    RENDA_FIXA = "renda_fixa"
    PREVIDENCIA = "previdencia"
    FGTS = "fgts"
    FUNDO = "fundo"
    OUTRO = "outro"


class TipoAtivo(StrEnum):
    ACAO_BR = "acao_br"
    BDR = "bdr"
    FII = "fii"
    FIAGRO = "fiagro"
    ETF_BR = "etf_br"
    ACAO_EUA = "acao_eua"
    ETF_EUA = "etf_eua"
    REIT = "reit"
    CRIPTO = "cripto"


class MercadoAtivo(StrEnum):
    B3 = "B3"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    CRIPTO = "CRIPTO"


class Geografia(StrEnum):
    BR = "BR"
    EUA = "EUA"
    GLOBAL = "GLOBAL"


class ClasseAtivo(StrEnum):
    ACAO = "acao"
    ETF = "etf"
    FII = "fii"
    FIAGRO = "fiagro"
    REIT = "reit"
    CRIPTO = "cripto"
import { http } from "./http"

export interface PontoEvolucao {
  ano: number
  mes: number
  label: string
  patrimonio_total: number
}

export interface FatiaCarteira {
  categoria: string
  valor: number
  cor: string
}

export interface MesReceitaDespesa {
  label: string
  receitas: number
  despesas: number
  saldo: number
}

export interface MesProvento {
  label: string
  total: number
}

export interface DashboardKPIs {
  patrimonio_total: number
  variacao_mes_pct: number | null
  proventos_mes: number
  distribuicao_brl_pct: number
  distribuicao_usd_pct: number
}

export interface ComparativoAnual {
  ano: number
  receitas: number
  despesas: number
  saldo: number
  proventos: number
}

export interface PontoSaldoInvestimentos {
  label: string
  renda_fixa: number
  previdencia: number
  fgts: number
  cripto: number
  rv_br: number
  rv_eua: number
}

export interface PontoDistribuicaoMensal {
  label: string
  rv_br: number
  rv_eua: number
  cripto: number
}

export interface DashboardDados {
  timestamp: string
  kpis: DashboardKPIs
  evolucao_patrimonial: PontoEvolucao[]
  distribuicao_carteira: FatiaCarteira[]
  receitas_despesas: MesReceitaDespesa[]
  renda_passiva: MesProvento[]
  comparativo_anual: ComparativoAnual[]
  saldo_investimentos: PontoSaldoInvestimentos[]
  distribuicao_mensal: PontoDistribuicaoMensal[]
}

export const dashboardService = {
  obter: () => http.get<DashboardDados>("/dashboard/dados").then(r => r.data),
}
import { http } from "./http"

export interface ResumoMensal {
  periodo: { ano_id: number; ano: number; mes: number }
  totais: {
    receitas: number
    despesas: number
    saldo: number
    combustivel: number
    cartoes_total: number
    aportes_brl: number
    aportes_usd: number
    aportes_usd_em_brl: number
    proventos_brl: number
    proventos_usd: number
    proventos_usd_em_brl: number
  }
  contadores: {
    qtd_receitas: number
    qtd_despesas: number
    qtd_combustivel: number
    qtd_aportes: number
    qtd_proventos: number
  }
  destaques: {
    categoria_maior_gasto: {
      id: number; nome: string; valor: number; percentual_despesas: number
    } | null
    ativo_maior_aporte: { id: number; ticker: string; valor_brl: number } | null
  }
  comparativo_mes_anterior: {
    receitas: { valor_atual: number; valor_anterior: number; variacao_pct: number }
    despesas: { valor_atual: number; valor_anterior: number; variacao_pct: number }
    saldo: { valor_atual: number; valor_anterior: number; variacao_pct: number }
  } | null
  cotacao_usd_brl_utilizada: number | null
}

export const resumoService = {
  obter: (ano_id: number, mes: number) =>
    http.get<ResumoMensal>("/resumo-mensal",
      { params: { ano_id, mes } }).then(r => r.data),
}
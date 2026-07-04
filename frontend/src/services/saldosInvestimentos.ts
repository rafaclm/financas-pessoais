import { http } from "./http"

export interface SaldoInvestimento {
  id: number
  ano_id: number
  mes: number
  produto_id: number
  saldo: number
  cotacao_usd_brl: number | null
  saldo_brl: number
  criado_em: string
  atualizado_em: string
}

export interface SaldoInvestimentoComVariacao {
  produto_id: number
  produto_nome: string
  produto_categoria: string
  produto_moeda: string
  saldo_id: number | null
  saldo: number
  cotacao_usd_brl: number | null
  saldo_brl: number
  saldo_brl_mes_anterior: number
  variacao_valor: number | null
  variacao_pct: number | null
  existe: boolean
}

export interface SaldoInvestimentoLote {
  itens: Array<{
    ano_id: number
    mes: number
    produto_id: number
    saldo: number
    cotacao_usd_brl: number | null
  }>
}

export const saldosInvestimentosService = {
  listar: (ano_id: number, mes: number) =>
    http.get<SaldoInvestimento[]>("/saldos-investimentos",
      { params: { ano_id, mes } }).then(r => r.data),

  listarComVariacao: (ano_id: number, mes: number) =>
    http.get<SaldoInvestimentoComVariacao[]>("/saldos-investimentos/com-variacao",
      { params: { ano_id, mes } }).then(r => r.data),

  lote: (payload: SaldoInvestimentoLote) =>
    http.post<SaldoInvestimento[]>("/saldos-investimentos/lote", payload).then(r => r.data),

  excluir: (id: number) => http.delete(`/saldos-investimentos/${id}`),

  replicarMesAnterior: (ano_id: number, mes: number) =>
    http.post<{ mensagem: string; replicados: number }>(
      "/saldos-investimentos/replicar-mes-anterior",
      null,
      { params: { ano_id, mes } }
    ).then(r => r.data),
}
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

export const saldosInvService = {
  listar: (ano_id?: number, mes?: number) =>
    http.get<SaldoInvestimento[]>("/posicoes/saldos-investimentos",
      { params: { ano_id, mes } }).then(r => r.data),
  criar: (p: Partial<SaldoInvestimento>) =>
    http.post<SaldoInvestimento>("/posicoes/saldos-investimentos", p).then(r => r.data),
  lote: (lista: Partial<SaldoInvestimento>[]) =>
    http.post<SaldoInvestimento[]>("/posicoes/saldos-investimentos/lote", lista).then(r => r.data),
  atualizar: (id: number, p: Partial<SaldoInvestimento>) =>
    http.put<SaldoInvestimento>(`/posicoes/saldos-investimentos/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/posicoes/saldos-investimentos/${id}`),
  replicarMesAnterior: (ano_id: number, mes: number, force = false) =>
    http.post<{ replicados: number; origem_total: number; mensagem: string }>(
      "/posicoes/saldos-investimentos/replicar-mes-anterior",
      { ano_id, mes, force }
    ).then(r => r.data),
}
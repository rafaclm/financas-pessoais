import { http } from "./http"

export interface SaldoConta {
  id: number
  ano_id: number
  mes: number
  conta_id: number
  saldo: number
  cotacao_usd_brl: number | null
  saldo_brl: number
  criado_em: string
  atualizado_em: string
}

export const saldosContasService = {
  listar: (ano_id?: number, mes?: number) =>
    http.get<SaldoConta[]>("/posicoes/saldos-contas",
      { params: { ano_id, mes } }).then(r => r.data),
  criar: (p: Partial<SaldoConta>) =>
    http.post<SaldoConta>("/posicoes/saldos-contas", p).then(r => r.data),
  lote: (lista: Partial<SaldoConta>[]) =>
    http.post<SaldoConta[]>("/posicoes/saldos-contas/lote", lista).then(r => r.data),
  atualizar: (id: number, p: Partial<SaldoConta>) =>
    http.put<SaldoConta>(`/posicoes/saldos-contas/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/posicoes/saldos-contas/${id}`),
  replicarMesAnterior: (ano_id: number, mes: number, force = false) =>
    http.post<{ replicados: number; origem_total: number; mensagem: string }>(
      "/posicoes/saldos-contas/replicar-mes-anterior",
      { ano_id, mes, force }
    ).then(r => r.data),
}
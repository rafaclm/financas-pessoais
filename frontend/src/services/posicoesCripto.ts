import { http } from "./http"

export interface PosicaoCripto {
  id: number
  ano_id: number
  mes: number
  ativo_id: number
  quantidade: number
  saldo_brl: number
  cotacao_usd_brl: number
  saldo_usd: number
  variacao_pct: number | null
  criado_em: string
  atualizado_em: string
}

export const posicoesCriptoService = {
  listar: (ano_id?: number, mes?: number) =>
    http.get<PosicaoCripto[]>("/posicoes/cripto",
      { params: { ano_id, mes } }).then(r => r.data),
  criar: (p: Partial<PosicaoCripto>) =>
    http.post<PosicaoCripto>("/posicoes/cripto", p).then(r => r.data),
  lote: (lista: Partial<PosicaoCripto>[]) =>
    http.post<PosicaoCripto[]>("/posicoes/cripto/lote", lista).then(r => r.data),
  atualizar: (id: number, p: Partial<PosicaoCripto>) =>
    http.put<PosicaoCripto>(`/posicoes/cripto/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/posicoes/cripto/${id}`),
  replicarMesAnterior: (ano_id: number, mes: number, force = false) =>
    http.post<{ replicados: number; origem_total: number; mensagem: string }>(
      "/posicoes/cripto/replicar-mes-anterior",
      { ano_id, mes, force }
    ).then(r => r.data),
}
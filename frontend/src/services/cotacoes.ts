import { http } from "./http"

export interface CotacaoCambio {
  id: number
  ano_id: number
  mes: number
  par: string
  cotacao: number
  fonte: string
  criado_em: string
  atualizado_em: string
}

export const cotacoesService = {
  listar: (params: { ano_id?: number; mes?: number; par?: string } = {}) =>
    http.get<CotacaoCambio[]>("/cotacoes-cambio", { params }).then(r => r.data),
  atualizarViaBCB: (ano_id: number, mes: number, par = "USDBRL") =>
    http.post<{ par: string; ano_id: number; mes: number; cotacao: number }>(
      "/cotacoes-cambio/atualizar-bcb",
      { ano_id, mes, par }
    ).then(r => r.data),
  criar: (p: Partial<CotacaoCambio>) =>
    http.post<CotacaoCambio>("/cotacoes-cambio", p).then(r => r.data),
}
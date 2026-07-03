import { http } from "./http"
import type { PrecoMedioSugerido } from "./posicoesBR"

export interface PosicaoEUA {
  id: number
  ano_id: number
  mes: number
  ativo_id: number
  quantidade: number
  preco_medio_usd: number
  cotacao_fechamento_usd: number
  cotacao_usd_brl: number
  valor_total_usd: number
  valor_total_brl: number
  criado_em: string
  atualizado_em: string
}

export const posicoesEUAService = {
  listar: (ano_id?: number, mes?: number) =>
    http.get<PosicaoEUA[]>("/posicoes/ativos-eua",
      { params: { ano_id, mes } }).then(r => r.data),
  criar: (p: Partial<PosicaoEUA>) =>
    http.post<PosicaoEUA>("/posicoes/ativos-eua", p).then(r => r.data),
  lote: (lista: Partial<PosicaoEUA>[]) =>
    http.post<PosicaoEUA[]>("/posicoes/ativos-eua/lote", lista).then(r => r.data),
  atualizar: (id: number, p: Partial<PosicaoEUA>) =>
    http.put<PosicaoEUA>(`/posicoes/ativos-eua/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/posicoes/ativos-eua/${id}`),
  replicarMesAnterior: (ano_id: number, mes: number, force = false) =>
    http.post<{ replicados: number; origem_total: number; mensagem: string }>(
      "/posicoes/ativos-eua/replicar-mes-anterior",
      { ano_id, mes, force }
    ).then(r => r.data),
  precoMedioSugerido: (ativo_id: number, ano_id: number, mes: number) =>
    http.get<PrecoMedioSugerido>("/posicoes/ativos-eua/preco-medio-sugerido",
      { params: { ativo_id, ano_id, mes } }).then(r => r.data),
}
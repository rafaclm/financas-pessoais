import { http } from "./http"

export interface PosicaoBR {
  id: number
  ano_id: number
  mes: number
  ativo_id: number
  quantidade: number
  preco_medio: number
  cotacao_fechamento: number
  valor_total: number
  criado_em: string
  atualizado_em: string
}

export interface PrecoMedioSugerido {
  ativo_id: number
  quantidade_acumulada: number
  preco_medio_sugerido: number
  total_aportes: number
}

export const posicoesBRService = {
  listar: (ano_id?: number, mes?: number) =>
    http.get<PosicaoBR[]>("/posicoes/ativos-br",
      { params: { ano_id, mes } }).then(r => r.data),
  criar: (p: Partial<PosicaoBR>) =>
    http.post<PosicaoBR>("/posicoes/ativos-br", p).then(r => r.data),
  lote: (lista: Partial<PosicaoBR>[]) =>
    http.post<PosicaoBR[]>("/posicoes/ativos-br/lote", lista).then(r => r.data),
  atualizar: (id: number, p: Partial<PosicaoBR>) =>
    http.put<PosicaoBR>(`/posicoes/ativos-br/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/posicoes/ativos-br/${id}`),
  replicarMesAnterior: (ano_id: number, mes: number, force = false) =>
    http.post<{ replicados: number; origem_total: number; mensagem: string }>(
      "/posicoes/ativos-br/replicar-mes-anterior",
      { ano_id, mes, force }
    ).then(r => r.data),
  precoMedioSugerido: (ativo_id: number, ano_id: number, mes: number) =>
    http.get<PrecoMedioSugerido>("/posicoes/ativos-br/preco-medio-sugerido",
      { params: { ativo_id, ano_id, mes } }).then(r => r.data),
}
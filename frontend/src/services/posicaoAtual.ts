import { http } from "./http"

export interface PosicaoAtual {
  id: number
  ativo_id: number
  ticker: string
  nome: string
  geografia: string
  classe: string
  moeda: string
  quantidade: number
  quantidade_comprada_total: number
  quantidade_vendida_total: number
  custo_total: number
  custo_total_brl: number
  preco_medio: number
  preco_medio_calculado: number
  preco_medio_manual: number | null
  preco_medio_eh_manual: number
  cotacao_atual: number | null
  cotacao_atual_data: string | null
  cotacao_fonte: string | null
  cotacao_usd_brl: number | null
  valor_atual_brl: number
  rentabilidade_pct: number | null
  rentabilidade_total_pct: number | null  // 🆕
  proventos_totais_brl: number
  yield_on_cost_pct: number | null
  preco_teto: number | null
  margem_aporte_pct: number | null
  acima_do_teto: boolean
}

export interface ResultadoAtualizacaoCotacoes {
  atualizados: number
  falhas: number
  total: number
  mensagem: string
  detalhes: Array<{ ticker: string; cotacao: number | null; fonte: string | null; status: string; erro?: string }>
}

export interface ResultadoRecalculo {
  ativos_processados: number
  aportes_processados: number
  mensagem: string
}

export interface FiltroPosicaoAtual {
  apenas_com_posicao?: boolean
  geografia?: string
  classe?: string
}

export const posicaoAtualService = {
  listar: (f: FiltroPosicaoAtual = {}) =>
    http.get<PosicaoAtual[]>("/posicao-atual", { params: f }).then(r => r.data),
  obter: (ativo_id: number) =>
    http.get<PosicaoAtual>(`/posicao-atual/${ativo_id}`).then(r => r.data),
  definirPrecoMedioManual: (ativo_id: number, preco_medio_manual: number) =>
    http.put<PosicaoAtual>(`/posicao-atual/${ativo_id}/preco-medio`,
      { preco_medio_manual }).then(r => r.data),
  voltarPrecoAutomatico: (ativo_id: number) =>
    http.post<PosicaoAtual>(`/posicao-atual/${ativo_id}/voltar-preco-automatico`).then(r => r.data),
  definirPrecoTeto: (ativo_id: number, preco_teto: number) =>
    http.put<PosicaoAtual>(`/posicao-atual/${ativo_id}/preco-teto`,
      { preco_teto }).then(r => r.data),
  removerPrecoTeto: (ativo_id: number) =>
    http.delete<PosicaoAtual>(`/posicao-atual/${ativo_id}/preco-teto`).then(r => r.data),
  atualizarCotacaoApi: (ativo_id: number) =>
    http.post<PosicaoAtual>(`/posicao-atual/${ativo_id}/atualizar-cotacao-api`).then(r => r.data),
  atualizarTodasCotacoes: () =>
    http.post<ResultadoAtualizacaoCotacoes>("/posicao-atual/atualizar-cotacoes").then(r => r.data),
  recalcular: () =>
    http.post<ResultadoRecalculo>("/posicao-atual/recalcular").then(r => r.data),
  recalcularUm: (ativo_id: number) =>
    http.post<PosicaoAtual>(`/posicao-atual/${ativo_id}/recalcular`).then(r => r.data),
}
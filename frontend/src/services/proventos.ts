import { http } from "./http"

export interface Provento {
  id: number
  ano_id: number
  mes: number
  data: string
  ativo_id: number
  tipo: "dividendo" | "jcp" | "rendimento" | "juros_cripto" | "outro"
  valor_bruto: number
  valor_liquido: number
  moeda: "BRL" | "USD"
  cotacao_usd_brl: number | null
  valor_liquido_brl: number
  conta_id: number | null
  descricao: string | null
  quantidade_cotas: number | null  // 🆕
  criado_em: string
  atualizado_em: string
}

export interface ResumoMensalProventos {
  mes: number
  total_brl: number
  qtd: number
}

export interface ResumoAnualProventos {
  total_acumulado_brl: number
  media_mensal_brl: number
  maior_mes: number | null
  maior_valor: number
  qtd_total: number
}

export interface ResumoProventosPorAtivo {
  ativo_id: number
  ticker: string
  nome: string
  qtd: number
  total_brl: number
}

export interface FiltroProventos {
  ano_id?: number
  mes?: number
  ativo_id?: number
  tipo?: string
}

export const proventosService = {
  listar: (f: FiltroProventos = {}) =>
    http.get<Provento[]>("/proventos", { params: f }).then(r => r.data),
  obter: (id: number) =>
    http.get<Provento>(`/proventos/${id}`).then(r => r.data),
  criar: (p: Partial<Provento>) =>
    http.post<Provento>("/proventos", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Provento>) =>
    http.put<Provento>(`/proventos/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/proventos/${id}`),
  resumoMensal: (ano_id: number) =>
    http.get<ResumoMensalProventos[]>("/proventos/resumo-mensal",
      { params: { ano_id } }).then(r => r.data),
  resumoAnual: (ano_id: number) =>
    http.get<ResumoAnualProventos>("/proventos/resumo-anual",
      { params: { ano_id } }).then(r => r.data),
  porAtivo: (ano_id: number) =>
    http.get<ResumoProventosPorAtivo[]>("/proventos/por-ativo",
      { params: { ano_id } }).then(r => r.data),
}
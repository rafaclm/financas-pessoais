import { http } from "./http"

export interface Despesa {
  id: number
  ano_id: number
  mes: number
  categoria_id: number
  origem_tipo: "conta" | "cartao"
  conta_id: number | null
  cartao_id: number | null
  valor: number
  descricao: string | null
  recorrente: number
  auto_pagamento_cartao: number
  pagamento_cartao_id: number | null
  replicado_de_id: number | null
  criado_em: string
  atualizado_em: string
}

export interface FiltroDespesas {
  ano_id?: number
  mes?: number
  categoria_id?: number
  origem_tipo?: string
  conta_id?: number
  cartao_id?: number
}

export const despesasService = {
  listar: (f: FiltroDespesas = {}) =>
    http.get<Despesa[]>("/despesas", { params: f }).then(r => r.data),
  obter: (id: number) =>
    http.get<Despesa>(`/despesas/${id}`).then(r => r.data),
  criar: (p: Partial<Despesa>) =>
    http.post<Despesa>("/despesas", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Despesa>) =>
    http.put<Despesa>(`/despesas/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/despesas/${id}`),
}
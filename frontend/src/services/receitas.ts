import { http } from "./http"

export interface Receita {
  id: number
  ano_id: number
  mes: number
  categoria_id: number
  conta_id: number
  valor: number
  descricao: string | null
  recorrente: number
  replicado_de_id: number | null
  criado_em: string
  atualizado_em: string
}

export interface FiltroReceitas {
  ano_id?: number
  mes?: number
  categoria_id?: number
  conta_id?: number
}

export const receitasService = {
  listar: (f: FiltroReceitas = {}) =>
    http.get<Receita[]>("/receitas", { params: f }).then(r => r.data),
  obter: (id: number) =>
    http.get<Receita>(`/receitas/${id}`).then(r => r.data),
  criar: (p: Partial<Receita>) =>
    http.post<Receita>("/receitas", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Receita>) =>
    http.put<Receita>(`/receitas/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/receitas/${id}`),
}
import { http } from "./http"

// ===== Categorias de Despesas =====
export interface CategoriaDespesa {
  id: number
  nome: string
  tipo: "fixa" | "variavel"
  essencial: number
  cor: string | null
  icone: string | null
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const catDespService = {
  listar: (apenasAtivos = false) =>
    http.get<CategoriaDespesa[]>("/categorias/despesas",
      { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (p: Partial<CategoriaDespesa>) =>
    http.post<CategoriaDespesa>("/categorias/despesas", p).then(r => r.data),
  atualizar: (id: number, p: Partial<CategoriaDespesa>) =>
    http.put<CategoriaDespesa>(`/categorias/despesas/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/categorias/despesas/${id}`),
}

// ===== Categorias de Receitas =====
export interface CategoriaReceita {
  id: number
  nome: string
  recorrencia: "recorrente" | "eventual"
  cor: string | null
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const catRecService = {
  listar: (apenasAtivos = false) =>
    http.get<CategoriaReceita[]>("/categorias/receitas",
      { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (p: Partial<CategoriaReceita>) =>
    http.post<CategoriaReceita>("/categorias/receitas", p).then(r => r.data),
  atualizar: (id: number, p: Partial<CategoriaReceita>) =>
    http.put<CategoriaReceita>(`/categorias/receitas/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/categorias/receitas/${id}`),
}
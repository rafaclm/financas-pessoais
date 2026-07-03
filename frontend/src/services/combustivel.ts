import { http } from "./http"

export interface Combustivel {
  id: number
  ano_id: number
  mes: number
  data: string  // YYYY-MM-DD
  litros: number
  valor_total: number
  posto: string | null
  veiculo: string | null
  conta_id: number | null
  cartao_id: number | null
  preco_litro: number
  criado_em: string
  atualizado_em: string
}

export interface ResumoCombustivelMes {
  mes: number
  total_litros: number
  total_valor: number
  preco_medio_litro: number
  qtd_abastecimentos: number
}

export const combustivelService = {
  listar: (params: { ano_id?: number; mes?: number } = {}) =>
    http.get<Combustivel[]>("/combustivel", { params }).then(r => r.data),
  obter: (id: number) =>
    http.get<Combustivel>(`/combustivel/${id}`).then(r => r.data),
  criar: (p: Partial<Combustivel>) =>
    http.post<Combustivel>("/combustivel", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Combustivel>) =>
    http.put<Combustivel>(`/combustivel/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/combustivel/${id}`),
  resumoAnual: (ano_id: number) =>
    http.get<ResumoCombustivelMes[]>("/combustivel/resumo",
      { params: { ano_id } }).then(r => r.data),
}
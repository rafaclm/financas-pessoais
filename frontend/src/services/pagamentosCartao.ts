import { http } from "./http"

export interface PagamentoCartao {
  id: number
  ano_id: number
  mes: number
  cartao_id: number
  conta_id: number
  valor: number
  descricao: string | null
  criado_em: string
  atualizado_em: string
}

export const pagamentosCartaoService = {
  listar: (params: { ano_id?: number; mes?: number; cartao_id?: number } = {}) =>
    http.get<PagamentoCartao[]>("/pagamentos-cartao", { params }).then(r => r.data),
  obter: (id: number) =>
    http.get<PagamentoCartao>(`/pagamentos-cartao/${id}`).then(r => r.data),
  criar: (p: Partial<PagamentoCartao>) =>
    http.post<PagamentoCartao>("/pagamentos-cartao", p).then(r => r.data),
  atualizar: (id: number, p: Partial<PagamentoCartao>) =>
    http.put<PagamentoCartao>(`/pagamentos-cartao/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/pagamentos-cartao/${id}`),
}
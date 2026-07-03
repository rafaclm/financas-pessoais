import { http } from "./http"

export interface ProdutoInvestimento {
  id: number
  nome: string
  categoria: "renda_fixa" | "previdencia" | "fgts" | "fundo" | "outro"
  instituicao_id: number
  moeda: "BRL" | "USD"
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const produtosService = {
  listar: (apenasAtivos = false) =>
    http.get<ProdutoInvestimento[]>("/produtos-investimento",
      { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (p: Partial<ProdutoInvestimento>) =>
    http.post<ProdutoInvestimento>("/produtos-investimento", p).then(r => r.data),
  atualizar: (id: number, p: Partial<ProdutoInvestimento>) =>
    http.put<ProdutoInvestimento>(`/produtos-investimento/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/produtos-investimento/${id}`),
}
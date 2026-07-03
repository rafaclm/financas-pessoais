import { http } from "./http"

export interface Conta {
  id: number
  nome: string
  instituicao_id: number
  tipo: "corrente" | "investimento" | "internacional" | "outro"
  moeda: "BRL" | "USD"
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const contasService = {
  listar: (apenasAtivos = false) =>
    http.get<Conta[]>("/contas",
      { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (p: Partial<Conta>) =>
    http.post<Conta>("/contas", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Conta>) =>
    http.put<Conta>(`/contas/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/contas/${id}`),
}
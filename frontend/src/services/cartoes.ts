import { http } from "./http"

export interface Cartao {
  id: number
  nome: string
  instituicao_id: number
  conta_pagamento_id: number | null
  dia_fechamento: number
  dia_vencimento: number
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const cartoesService = {
  listar: (apenasAtivos = false) =>
    http.get<Cartao[]>("/cartoes",
      { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (p: Partial<Cartao>) =>
    http.post<Cartao>("/cartoes", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Cartao>) =>
    http.put<Cartao>(`/cartoes/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/cartoes/${id}`),
}
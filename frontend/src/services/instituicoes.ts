import { http } from "./http"

export interface Instituicao {
  id: number
  nome: string
  tipo: "banco" | "corretora" | "exchange" | "outro"
  pais: string
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const instituicoesService = {
  listar: (apenasAtivos = false) =>
    http.get<Instituicao[]>("/instituicoes",
      { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (p: Partial<Instituicao>) =>
    http.post<Instituicao>("/instituicoes", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Instituicao>) =>
    http.put<Instituicao>(`/instituicoes/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/instituicoes/${id}`),
}
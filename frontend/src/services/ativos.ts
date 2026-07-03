import { http } from './http'

export interface Ativo {
  id: number
  ticker: string
  nome: string
  tipo: string
  mercado: string
  geografia: string
  classe: string
  moeda: string
  setor: string | null
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const ativosService = {
  listar: (params: any = {}) =>
    http.get<Ativo[]>('/ativos', { params }).then(r => r.data),
  criar: (p: Partial<Ativo>) =>
    http.post<Ativo>('/ativos', p).then(r => r.data),
  atualizar: (id: number, p: Partial<Ativo>) =>
    http.put<Ativo>(`/ativos/${id}`, p).then(r => r.data),
  inativar: (id: number) => http.delete(`/ativos/${id}`),
}
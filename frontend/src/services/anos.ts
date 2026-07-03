import { http } from './http'

export interface Ano {
  id: number
  ano: number
  saldo_inicial: number
  observacao: string | null
  ativo: number
  criado_em: string
  atualizado_em: string
}

export const anosService = {
  listar: (apenasAtivos = false) =>
    http.get<Ano[]>('/anos', { params: { apenas_ativos: apenasAtivos } }).then(r => r.data),
  criar: (payload: Partial<Ano>) =>
    http.post<Ano>('/anos', payload).then(r => r.data),
  atualizar: (id: number, payload: Partial<Ano>) =>
    http.put<Ano>(`/anos/${id}`, payload).then(r => r.data),
  inativar: (id: number) => http.delete(`/anos/${id}`),
}
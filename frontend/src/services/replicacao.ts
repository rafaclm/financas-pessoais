import { http } from "./http"

export interface ReplicarPayload {
  ano_origem_id: number
  mes_origem: number
  ano_destino_id: number
  mes_destino: number
  replicar_receitas: boolean
  replicar_despesas: boolean
  apenas_recorrentes: boolean
  force: boolean
}

export interface ResultadoReplicacao {
  receitas_replicadas: number
  despesas_replicadas: number
  receitas_origem_total: number
  despesas_origem_total: number
  mensagem: string
}

export const replicacaoService = {
  replicar: (p: ReplicarPayload) =>
    http.post<ResultadoReplicacao>("/lancamentos/replicar", p).then(r => r.data),
}
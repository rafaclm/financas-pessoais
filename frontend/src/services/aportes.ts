import { http } from "./http"

export interface Aporte {
  id: number
  ano_id: number
  mes: number
  data: string
  ativo_id: number
  tipo_operacao: "compra" | "venda"
  quantidade: number
  preco_unitario: number
  taxas: number
  moeda: "BRL" | "USD"
  cotacao_usd_brl: number | null
  valor_total: number
  valor_total_brl: number
  conta_id: number | null  // 🆕 agora opcional
  descricao: string | null
  criado_em: string
  atualizado_em: string
}

export interface ResumoMensalAportes {
  mes: number
  total_brl: number
  qtd_operacoes: number
  qtd_compras: number
  qtd_vendas: number
  total_compras_brl: number
  total_vendas_brl: number
}

export interface ResumoPorAtivo {
  ativo_id: number
  ticker: string
  nome: string
  qtd_operacoes: number
  total_brl: number
  quantidade_acumulada: number | null
}

export interface FiltroAportes {
  ano_id?: number
  mes?: number
  ativo_id?: number
  tipo_operacao?: string
}

export const aportesService = {
  listar: (f: FiltroAportes = {}) =>
    http.get<Aporte[]>("/aportes", { params: f }).then(r => r.data),
  obter: (id: number) =>
    http.get<Aporte>(`/aportes/${id}`).then(r => r.data),
  criar: (p: Partial<Aporte>) =>
    http.post<Aporte>("/aportes", p).then(r => r.data),
  atualizar: (id: number, p: Partial<Aporte>) =>
    http.put<Aporte>(`/aportes/${id}`, p).then(r => r.data),
  excluir: (id: number) => http.delete(`/aportes/${id}`),
  resumoMensal: (ano_id: number) =>
    http.get<ResumoMensalAportes[]>("/aportes/resumo-mensal",
      { params: { ano_id } }).then(r => r.data),
  porAtivo: (ano_id: number, tipo_operacao?: string) =>
    http.get<ResumoPorAtivo[]>("/aportes/por-ativo",
      { params: { ano_id, tipo_operacao } }).then(r => r.data),
}
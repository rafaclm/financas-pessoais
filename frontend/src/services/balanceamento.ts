import { http } from "./http"

// ===== Configurações =====
export interface BalGeografia {
  id: number
  geografia: string
  percentual_alvo: number
  ativo: number
  criado_em: string
  atualizado_em: string
}

export interface BalClasse {
  id: number
  geografia: string
  classe: string
  percentual_alvo: number
  ativo: number
  criado_em: string
  atualizado_em: string
}

export interface BalAtivo {
  id: number
  ativo_id: number
  percentual_alvo_carteira: number
  ativo: number
  criado_em: string
  atualizado_em: string
}

// ===== Análise =====
export interface ItemBalGeografia {
  geografia: string
  valor_alocado_brl: number
  percentual_atual: number
  percentual_alvo: number | null
  gap_pct: number | null
  aporte_sugerido_brl: number | null
  status: "abaixo" | "acima" | "equilibrado" | "sem_meta"
}

export interface ItemBalClasse {
  geografia: string
  classe: string
  valor_alocado_brl: number
  percentual_atual: number
  percentual_alvo: number | null
  gap_pct: number | null
  aporte_sugerido_brl: number | null
  status: "abaixo" | "acima" | "equilibrado" | "sem_meta"
}

export interface ItemBalAtivo {
  ativo_id: number
  ticker: string
  nome: string
  classe: string
  geografia: string
  valor_alocado_brl: number
  percentual_atual: number
  percentual_alvo: number | null
  gap_pct: number | null
  aporte_sugerido_brl: number | null
  status: "abaixo" | "acima" | "equilibrado" | "sem_meta"
  ultima_cotacao_em: string | null
}

export interface AtivoSemCotacao {
  ticker: string
  motivo: string
}

export interface AnaliseBalanceamento {
  calculado_em: string
  total_rv_brl: number
  cotacao_usd_brl: number | null
  qtd_ativos_com_posicao: number
  qtd_ativos_sem_cotacao: number
  ativos_sem_cotacao: AtivoSemCotacao[]
  por_geografia: ItemBalGeografia[]
  por_classe: ItemBalClasse[]
  por_ativo: ItemBalAtivo[]
  soma_alvos_geografia: number
  soma_alvos_classe_por_geo: Record<string, number>
}

export const balanceamentoService = {
  // Geografia
  listarGeografia: () =>
    http.get<BalGeografia[]>("/balanceamento/config/geografia").then(r => r.data),
  criarGeografia: (p: Partial<BalGeografia>) =>
    http.post<BalGeografia>("/balanceamento/config/geografia", p).then(r => r.data),
  atualizarGeografia: (id: number, p: Partial<BalGeografia>) =>
    http.put<BalGeografia>(`/balanceamento/config/geografia/${id}`, p).then(r => r.data),
  excluirGeografia: (id: number) =>
    http.delete(`/balanceamento/config/geografia/${id}`),

  // Classe
  listarClasse: (geografia?: string) =>
    http.get<BalClasse[]>("/balanceamento/config/classe",
      { params: { geografia } }).then(r => r.data),
  criarClasse: (p: Partial<BalClasse>) =>
    http.post<BalClasse>("/balanceamento/config/classe", p).then(r => r.data),
  atualizarClasse: (id: number, p: Partial<BalClasse>) =>
    http.put<BalClasse>(`/balanceamento/config/classe/${id}`, p).then(r => r.data),
  excluirClasse: (id: number) =>
    http.delete(`/balanceamento/config/classe/${id}`),

  // Ativo
  listarAtivo: () =>
    http.get<BalAtivo[]>("/balanceamento/config/ativo").then(r => r.data),
  criarAtivo: (p: Partial<BalAtivo>) =>
    http.post<BalAtivo>("/balanceamento/config/ativo", p).then(r => r.data),
  atualizarAtivo: (id: number, p: Partial<BalAtivo>) =>
    http.put<BalAtivo>(`/balanceamento/config/ativo/${id}`, p).then(r => r.data),
  excluirAtivo: (id: number) =>
    http.delete(`/balanceamento/config/ativo/${id}`),

  // Análise (sem ano/mês!)
  analisar: () =>
    http.get<AnaliseBalanceamento>("/balanceamento/analise").then(r => r.data),
}
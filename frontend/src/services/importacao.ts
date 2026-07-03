import { http } from "./http"

export interface AbaInfo {
  nome: string
  max_row: number
  max_column: number
  tipo_detectado: string
}

export interface AnaliseArquivo {
  total_abas: number
  abas: AbaInfo[]
}

export interface ResultadoBlocoImportacao {
  inseridos: number
  atualizados: number
  pulados: number
  erros: number
  detalhes_inseridos: string[]
  detalhes_erros: string[]
  mensagem: string
}

export interface RelatorioImportacao {
  timestamp: string
  backup_seguranca: string | null
  blocos: Record<string, ResultadoBlocoImportacao>
  sucesso_geral: boolean
  mensagem_final: string
}

export interface ExploradorRelatorio {
  aba: string
  dados: Record<string, any>
}

export interface PayloadImportarMovimentos {
  nome_arquivo: string
  anos: number[]
  blocos: string[]
}

export interface RelatorioMovimentos {
  timestamp: string
  backup_seguranca: string | null
  dry_run: boolean
  relatorio_por_ano: Record<string, any>
  mensagem_final: string
}

export interface TickerInfo {
  ticker: string
  pais_planilha?: string
  classe: string
  tipo?: string
  mercado?: string
  geografia: string
  nome_sistema?: string
}

export interface AnaliseAportes {
  total_linhas_validas: number
  compras: number
  vendas: number
  valor_total_brl_estimado: number
  tickers_existentes: TickerInfo[]
  tickers_novos: TickerInfo[]
}

export interface AnaliseProventos {
  total_linhas_validas: number
  total_brl_estimado: number
  distribuicao_tipos: Record<string, number>
  tickers_existentes: TickerInfo[]
  tickers_novos: TickerInfo[]
}

export interface RelatorioGenerico {
  timestamp: string
  backup_seguranca: string | null
  dry_run: boolean
  resultado: {
    inseridos: number
    atualizados: number
    pulados: number
    erros: number
    detalhes_inseridos: string[]
    detalhes_erros: string[]
    mensagem: string
  }
  mensagem_final: string
}

export const importacaoService = {
  analisar: (arquivo: File) => {
    const fd = new FormData()
    fd.append("arquivo", arquivo)
    return http.post<AnaliseArquivo>("/importacao/analisar", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  previewAtivos: (nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<RelatorioImportacao>("/importacao/preview-ativos", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  executarAtivos: (nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<RelatorioImportacao>("/importacao/executar-ativos", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  explorarAba: (nome_aba: string, nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<ExploradorRelatorio>(
      `/importacao/explorar/${encodeURIComponent(nome_aba)}`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  previewMovimentos: (payload: PayloadImportarMovimentos) =>
    http.post<RelatorioMovimentos>("/importacao/preview-movimentos", payload).then(r => r.data),

  executarMovimentos: (payload: PayloadImportarMovimentos) =>
    http.post<RelatorioMovimentos>("/importacao/executar-movimentos", payload).then(r => r.data),

  // APORTES
  analisarAportes: (nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<AnaliseAportes>("/importacao/analisar-aportes", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  previewAportes: (nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<RelatorioGenerico>("/importacao/preview-aportes", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  executarAportes: (nome_arquivo: string, criar_tickers_novos = true) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    fd.append("criar_tickers_novos", criar_tickers_novos ? "true" : "false")
    return http.post<RelatorioGenerico>("/importacao/executar-aportes", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  // 🆕 PROVENTOS
  analisarProventos: (nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<AnaliseProventos>("/importacao/analisar-proventos", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  previewProventos: (nome_arquivo: string) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    return http.post<RelatorioGenerico>("/importacao/preview-proventos", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },

  executarProventos: (nome_arquivo: string, criar_tickers_novos = true) => {
    const fd = new FormData()
    fd.append("nome_arquivo", nome_arquivo)
    fd.append("criar_tickers_novos", criar_tickers_novos ? "true" : "false")
    return http.post<RelatorioGenerico>("/importacao/executar-proventos", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },
}
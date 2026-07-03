import { http } from "./http"

export interface ComponentePatrimonio {
  categoria: string
  label: string
  valor_brl: number
  percentual_total: number
  cor: string | null
}

export interface VariacaoPatrimonial {
  valor_atual: number
  valor_referencia: number
  diferenca: number
  variacao_pct: number
}

export interface ConsolidacaoPatrimonial {
  periodo: { ano_id: number; ano: number; mes: number }
  patrimonio_total: number
  componentes: ComponentePatrimonio[]
  total_liquidez: number
  total_renda_fixa: number
  total_renda_variavel: number
  total_cripto: number
  variacao_mes_anterior: VariacaoPatrimonial | null
  variacao_ano_anterior: VariacaoPatrimonial | null
  pct_liquidez: number
  pct_renda_fixa: number
  pct_renda_variavel: number
  pct_cripto: number
  pct_brl: number
  pct_usd: number
  cotacao_usd_brl: number | null
}

export interface ItemPorGeografia {
  geografia: string
  valor_brl: number
  percentual_carteira: number
  qtd_ativos: number
}

export interface ItemPorClasse {
  classe: string
  valor_brl: number
  percentual_carteira: number
  qtd_ativos: number
}

export interface ItemPorAtivo {
  ativo_id: number
  ticker: string
  nome: string
  classe: string
  geografia: string
  valor_brl: number
  percentual_carteira: number
}

export interface ConsolidacaoRV {
  periodo: { ano_id: number; ano: number; mes: number }
  total_brl: number
  total_br_brl: number
  total_eua_brl: number
  total_cripto_brl: number
  por_geografia: ItemPorGeografia[]
  por_classe: ItemPorClasse[]
  por_ativo: ItemPorAtivo[]
}

export const consolidacaoService = {
  patrimonial: (ano_id: number, mes: number) =>
    http.get<ConsolidacaoPatrimonial>("/consolidacao/patrimonial",
      { params: { ano_id, mes } }).then(r => r.data),
  rendaVariavel: (ano_id: number, mes: number) =>
    http.get<ConsolidacaoRV>("/consolidacao/renda-variavel",
      { params: { ano_id, mes } }).then(r => r.data),
}
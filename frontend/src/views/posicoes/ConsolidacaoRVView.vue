<script setup lang="ts">
import { ref, watch } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import { consolidacaoService } from "@/services/consolidacao"
import type { ConsolidacaoRV } from "@/services/consolidacao"
import { useToast } from "primevue/usetoast"
import ProgressSpinner from "primevue/progressspinner"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Tag from "primevue/tag"
import Panel from "primevue/panel"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()
const dados = ref(null as ConsolidacaoRV | null)
const carregando = ref(false)

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

const flagGeografia = (g: string) =>
  ({ BR: "🇧🇷", EUA: "🇺🇸", GLOBAL: "🌐" } as any)[g] || g

const labelClasse = (c: string) =>
  ({ acao: "Ação", etf: "ETF", fii: "FII", fiagro: "Fiagro",
     reit: "REIT", cripto: "Cripto" } as any)[c] || c

const corClasse = (c: string) =>
  ({ acao: "#10B981", etf: "#22C55E", fii: "#84CC16", fiagro: "#EAB308",
     reit: "#EC4899", cripto: "#F59E0B" } as any)[c] || "#888"

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    dados.value = await consolidacaoService.rendaVariavel(
      periodo.anoIdSelecionado, periodo.mesSelecionado
    )
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })
</script>

<template>
  <PageHeader title="📊 Consolidação da Renda Variável"
              :subtitle="`BR + EUA + Cripto - ${periodo.labelPeriodo}`" />

  <div v-if="carregando" class="loading"><ProgressSpinner /></div>

  <template v-else-if="dados">
    <section class="hero">
      <div class="hero-label">TOTAL EM RENDA VARIÁVEL</div>
      <div class="hero-valor tabular">{{ fmtBRL(dados.total_brl) }}</div>
    </section>

    <section class="grid-categorias">
      <div class="card-cat">
        <div class="cat-flag">🇧🇷</div>
        <div class="cat-label">Brasil</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_br_brl) }}</div>
        <div class="cat-pct">
          {{ dados.total_brl > 0 ? (dados.total_br_brl / dados.total_brl * 100).toFixed(1) : 0 }}% da carteira
        </div>
      </div>
      <div class="card-cat">
        <div class="cat-flag">🇺🇸</div>
        <div class="cat-label">EUA</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_eua_brl) }}</div>
        <div class="cat-pct">
          {{ dados.total_brl > 0 ? (dados.total_eua_brl / dados.total_brl * 100).toFixed(1) : 0 }}% da carteira
        </div>
      </div>
      <div class="card-cat">
        <div class="cat-flag">₿</div>
        <div class="cat-label">Criptoativos</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_cripto_brl) }}</div>
        <div class="cat-pct">
          {{ dados.total_brl > 0 ? (dados.total_cripto_brl / dados.total_brl * 100).toFixed(1) : 0 }}% da carteira
        </div>
      </div>
    </section>

    <Panel header="🌎 Distribuição por geografia" toggleable :collapsed="false" class="painel">
      <DataTable v-if="dados.por_geografia.length" :value="dados.por_geografia" stripedRows>
        <Column header="Geografia">
          <template #body="{ data }">
            <span class="geo-tag">{{ flagGeografia(data.geografia) }} {{ data.geografia }}</span>
          </template>
        </Column>
        <Column header="Qtd. ativos" style="text-align: center">
          <template #body="{ data }">{{ data.qtd_ativos }}</template>
        </Column>
        <Column header="Valor (BRL)" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular">{{ fmtBRL(data.valor_brl) }}</span>
          </template>
        </Column>
        <Column header="% Carteira" style="text-align: right">
          <template #body="{ data }">
            <Tag :value="data.percentual_carteira.toFixed(2) + '%'" severity="info" />
          </template>
        </Column>
      </DataTable>
      <div v-else class="vazio">Sem dados.</div>
    </Panel>

    <Panel header="🧩 Distribuição por classe de ativo" toggleable :collapsed="false" class="painel">
      <DataTable v-if="dados.por_classe.length" :value="dados.por_classe" stripedRows>
        <Column header="Classe">
          <template #body="{ data }">
            <Tag :value="labelClasse(data.classe)"
                 :style="{ background: corClasse(data.classe), color: 'white' }" />
          </template>
        </Column>
        <Column header="Qtd. ativos" style="text-align: center">
          <template #body="{ data }">{{ data.qtd_ativos }}</template>
        </Column>
        <Column header="Valor (BRL)" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular">{{ fmtBRL(data.valor_brl) }}</span>
          </template>
        </Column>
        <Column header="% Carteira" style="text-align: right">
          <template #body="{ data }">
            <Tag :value="data.percentual_carteira.toFixed(2) + '%'" severity="secondary" />
          </template>
        </Column>
      </DataTable>
      <div v-else class="vazio">Sem dados.</div>
    </Panel>

    <Panel header="🎯 Top ativos da carteira" toggleable :collapsed="false" class="painel">
      <DataTable v-if="dados.por_ativo.length" :value="dados.por_ativo.slice(0, 30)" stripedRows>
        <Column header="Ativo">
          <template #body="{ data }">
            <span class="ativo-cell">
              {{ flagGeografia(data.geografia) }}
              <strong>{{ data.ticker }}</strong>
              <span class="nome">{{ data.nome }}</span>
            </span>
          </template>
        </Column>
        <Column header="Classe">
          <template #body="{ data }">
            <Tag :value="labelClasse(data.classe)"
                 :style="{ background: corClasse(data.classe), color: 'white' }" />
          </template>
        </Column>
        <Column header="Valor (BRL)" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular">{{ fmtBRL(data.valor_brl) }}</span>
          </template>
        </Column>
        <Column header="% Carteira" style="text-align: right">
          <template #body="{ data }">
            <div class="pct-bar">
              <span class="tabular">{{ data.percentual_carteira.toFixed(2) }}%</span>
              <div class="bar"><div :style="{ width: data.percentual_carteira + '%' }"></div></div>
            </div>
          </template>
        </Column>
      </DataTable>
      <div v-else class="vazio">Sem dados.</div>
    </Panel>
  </template>
</template>

<style scoped>
.loading { display: flex; justify-content: center; padding: var(--space-12); }
.hero {
  background: linear-gradient(135deg, var(--brand-secondary), #059669);
  color: white; border-radius: var(--radius-xl);
  padding: var(--space-6); margin-bottom: var(--space-6); text-align: center;
}
.hero-label { font-size: var(--text-xs); letter-spacing: 0.1em; opacity: 0.85; }
.hero-valor { font-size: var(--text-3xl); font-weight: 700; margin-top: var(--space-2); }
.grid-categorias {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4); margin-bottom: var(--space-6);
}
.card-cat {
  background: var(--bg-surface); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); padding: var(--space-5); text-align: center;
}
.cat-flag { font-size: 36px; }
.cat-label { font-size: var(--text-xs); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: var(--space-2); }
.cat-valor { font-size: var(--text-xl); font-weight: 700; margin: var(--space-2) 0; }
.cat-pct { font-size: var(--text-sm); color: var(--text-secondary); }
.painel { margin-top: var(--space-4); }
.geo-tag { display: inline-flex; align-items: center; gap: 6px; font-weight: 500; }
.ativo-cell { display: inline-flex; align-items: center; gap: 8px; }
.ativo-cell .nome { color: var(--text-muted); font-size: var(--text-sm); }
.pct-bar { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.pct-bar .bar { width: 80px; height: 4px; background: var(--bg-elevated); border-radius: var(--radius-full); overflow: hidden; }
.pct-bar .bar > div { height: 100%; background: var(--brand-primary); transition: width 600ms; }
.vazio { padding: var(--space-6); text-align: center; color: var(--text-muted); }
</style>
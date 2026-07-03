<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { balanceamentoService } from "@/services/balanceamento"
import type { AnaliseBalanceamento } from "@/services/balanceamento"
import { useToast } from "primevue/usetoast"
import ProgressSpinner from "primevue/progressspinner"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Tag from "primevue/tag"
import Panel from "primevue/panel"
import Button from "primevue/button"
import Message from "primevue/message"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()
const dados = ref(null as AnaliseBalanceamento | null)
const carregando = ref(false)

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)
const fmtPct = (v: number | null) =>
  v === null || v === undefined ? "—" : `${v.toFixed(2)}%`

const fmtDataHora = (d: string) => {
  const dt = new Date(d)
  return dt.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
}

const labelGeo = (g: string) =>
  ({ BR: "🇧🇷 Brasil", EUA: "🇺🇸 EUA", GLOBAL: "🌐 Global" } as any)[g] || g

const labelClasse = (c: string) =>
  ({ acao: "Ação", etf: "ETF", fii: "FII", fiagro: "Fiagro",
     reit: "REIT", cripto: "Cripto" } as any)[c] || c

function severityStatus(s: string) {
  if (s === "abaixo") return "warning"
  if (s === "acima") return "danger"
  if (s === "equilibrado") return "success"
  return "secondary"
}

function labelStatus(s: string) {
  if (s === "abaixo") return "▼ Abaixo do alvo"
  if (s === "acima") return "▲ Acima do alvo"
  if (s === "equilibrado") return "✓ Equilibrado"
  return "Sem meta"
}

async function carregar() {
  carregando.value = true
  try {
    dados.value = await balanceamentoService.analisar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

const totalAporteSugerido = computed(() => {
  if (!dados.value) return 0
  return dados.value.por_geografia
    .filter(g => g.aporte_sugerido_brl !== null)
    .reduce((acc, g) => acc + (g.aporte_sugerido_brl || 0), 0)
})
</script>

<template>
  <PageHeader title="🚀 Análise de Balanceamento"
              subtitle="Foto mais recente da sua carteira de renda variável">
    <template #actions>
      <Button label="🔄 Atualizar" outlined @click="carregar" :loading="carregando" />
    </template>
  </PageHeader>

  <div v-if="carregando && !dados" class="loading"><ProgressSpinner /></div>

  <template v-else-if="dados">
    <!-- Info de cálculo -->
    <div class="info-calculo">
      📅 Calculado em <strong>{{ fmtDataHora(dados.calculado_em) }}</strong>
      &nbsp;•&nbsp; {{ dados.qtd_ativos_com_posicao }} ativos em carteira
      <span v-if="dados.cotacao_usd_brl">
        &nbsp;•&nbsp; USD/BRL: <strong>R$ {{ dados.cotacao_usd_brl.toFixed(4) }}</strong>
      </span>
    </div>

    <!-- Aviso de ativos sem cotação -->
    <Message v-if="dados.qtd_ativos_sem_cotacao > 0"
             severity="warn" :closable="false" class="aviso">
      ⚠️ <strong>{{ dados.qtd_ativos_sem_cotacao }} ativo(s) sem cotação:</strong>
      {{ dados.ativos_sem_cotacao.map(a => a.ticker).join(", ") }}.
      Eles não são considerados no cálculo.
      Vá em <strong>"Posição Atual"</strong> e clique em
      <strong>"🔄 Atualizar todas as cotações"</strong>.
    </Message>

    <!-- 💎 HERO -->
    <section class="hero">
      <div class="hero-bloco">
        <div class="hero-label">💼 CARTEIRA DE RENDA VARIÁVEL</div>
        <div class="hero-valor tabular">{{ fmtBRL(dados.total_rv_brl) }}</div>
      </div>
      <div v-if="totalAporteSugerido > 0" class="hero-bloco aporte">
        <div class="hero-label">🎯 APORTE SUGERIDO TOTAL</div>
        <div class="hero-valor tabular">{{ fmtBRL(totalAporteSugerido) }}</div>
        <div class="hero-sub">para atingir os alvos por geografia</div>
      </div>
    </section>

    <!-- 🌎 NÍVEL 1 — GEOGRAFIA -->
    <Panel header="🌎 Nível 1 — Por Geografia" toggleable :collapsed="false" class="painel">
      <DataTable v-if="dados.por_geografia.length" :value="dados.por_geografia" stripedRows>
        <Column header="Geografia">
          <template #body="{ data }">
            <strong>{{ labelGeo(data.geografia) }}</strong>
          </template>
        </Column>
        <Column header="💰 Valor Alocado (R$)" style="text-align: right">
          <template #body="{ data }">
            <strong class="tabular">{{ fmtBRL(data.valor_alocado_brl) }}</strong>
          </template>
        </Column>
        <Column header="% Atual" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular">{{ fmtPct(data.percentual_atual) }}</span>
          </template>
        </Column>
        <Column header="% Alvo" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular value-muted">{{ fmtPct(data.percentual_alvo) }}</span>
          </template>
        </Column>
        <Column header="Gap" style="text-align: right">
          <template #body="{ data }">
            <span v-if="data.gap_pct !== null" class="tabular"
                  :class="data.gap_pct > 0 ? 'value-positive' : 'value-negative'">
              {{ data.gap_pct > 0 ? "+" : "" }}{{ fmtPct(data.gap_pct) }}
            </span>
            <span v-else>—</span>
          </template>
        </Column>
        <Column header="💸 Aporte Sugerido" style="text-align: right">
          <template #body="{ data }">
            <strong v-if="data.aporte_sugerido_brl" class="tabular aporte-destaque">
              {{ fmtBRL(data.aporte_sugerido_brl) }}
            </strong>
            <span v-else class="value-muted">—</span>
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <Tag :severity="severityStatus(data.status) as any"
                 :value="labelStatus(data.status)" />
          </template>
        </Column>
      </DataTable>
      <div v-else class="vazio">
        Configure as metas em <strong>"Config. Metas"</strong> ou lance posições para começar.
      </div>
    </Panel>

    <!-- 🧩 NÍVEL 2 — CLASSE -->
    <Panel header="🧩 Nível 2 — Por Classe de Ativo" toggleable :collapsed="false" class="painel">
      <DataTable v-if="dados.por_classe.length" :value="dados.por_classe" stripedRows>
        <Column header="Geografia">
          <template #body="{ data }">{{ labelGeo(data.geografia) }}</template>
        </Column>
        <Column header="Classe">
          <template #body="{ data }">
            <Tag :value="labelClasse(data.classe)" severity="info" />
          </template>
        </Column>
        <Column header="💰 Valor Alocado (R$)" style="text-align: right">
          <template #body="{ data }">
            <strong class="tabular">{{ fmtBRL(data.valor_alocado_brl) }}</strong>
          </template>
        </Column>
        <Column header="% Atual" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular">{{ fmtPct(data.percentual_atual) }}</span>
          </template>
        </Column>
        <Column header="% Alvo" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular value-muted">{{ fmtPct(data.percentual_alvo) }}</span>
          </template>
        </Column>
        <Column header="Gap" style="text-align: right">
          <template #body="{ data }">
            <span v-if="data.gap_pct !== null" class="tabular"
                  :class="data.gap_pct > 0 ? 'value-positive' : 'value-negative'">
              {{ data.gap_pct > 0 ? "+" : "" }}{{ fmtPct(data.gap_pct) }}
            </span>
            <span v-else>—</span>
          </template>
        </Column>
        <Column header="💸 Aporte Sugerido" style="text-align: right">
          <template #body="{ data }">
            <strong v-if="data.aporte_sugerido_brl" class="tabular aporte-destaque">
              {{ fmtBRL(data.aporte_sugerido_brl) }}
            </strong>
            <span v-else class="value-muted">—</span>
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <Tag :severity="severityStatus(data.status) as any"
                 :value="labelStatus(data.status)" />
          </template>
        </Column>
      </DataTable>
      <div v-else class="vazio">Sem dados.</div>
    </Panel>

    <!-- 🎯 NÍVEL 3 — ATIVOS -->
    <Panel header="🎯 Nível 3 — Ativos Individuais" toggleable :collapsed="false" class="painel">
      <DataTable v-if="dados.por_ativo.length" :value="dados.por_ativo" stripedRows>
        <Column header="Ativo">
          <template #body="{ data }">
            <strong>{{ data.ticker }}</strong>
            <span class="nome">{{ data.nome }}</span>
          </template>
        </Column>
        <Column header="Geo/Classe">
          <template #body="{ data }">
            <span class="badge-mini">{{ labelGeo(data.geografia).split(" ")[0] }}</span>
            <Tag :value="labelClasse(data.classe)" severity="info" class="badge-mini" />
          </template>
        </Column>
        <Column header="💰 Valor Alocado (R$)" style="text-align: right">
          <template #body="{ data }">
            <strong class="tabular">{{ fmtBRL(data.valor_alocado_brl) }}</strong>
          </template>
        </Column>
        <Column header="% Atual" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular">{{ fmtPct(data.percentual_atual) }}</span>
          </template>
        </Column>
        <Column header="% Alvo" style="text-align: right">
          <template #body="{ data }">
            <span class="tabular value-muted">{{ fmtPct(data.percentual_alvo) }}</span>
          </template>
        </Column>
        <Column header="Gap" style="text-align: right">
          <template #body="{ data }">
            <span v-if="data.gap_pct !== null" class="tabular"
                  :class="data.gap_pct > 0 ? 'value-positive' : 'value-negative'">
              {{ data.gap_pct > 0 ? "+" : "" }}{{ fmtPct(data.gap_pct) }}
            </span>
            <span v-else>—</span>
          </template>
        </Column>
        <Column header="💸 Aporte Sugerido" style="text-align: right">
          <template #body="{ data }">
            <strong v-if="data.aporte_sugerido_brl" class="tabular aporte-destaque">
              {{ fmtBRL(data.aporte_sugerido_brl) }}
            </strong>
            <span v-else class="value-muted">—</span>
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <Tag :severity="severityStatus(data.status) as any"
                 :value="labelStatus(data.status)" />
          </template>
        </Column>
      </DataTable>
      <div v-else class="vazio">
        Configure ativos individuais em <strong>"Config. Metas" → Nível 3</strong>.
      </div>
    </Panel>
  </template>
</template>

<style scoped>
.loading { display: flex; justify-content: center; padding: var(--space-12); }
.info-calculo {
  background: var(--bg-elevated); padding: var(--space-3);
  border-radius: var(--radius-md); font-size: var(--text-sm);
  color: var(--text-secondary); margin-bottom: var(--space-4);
}
.aviso { margin-bottom: var(--space-4); }
.hero {
  display: grid; grid-template-columns: 1fr auto; gap: var(--space-4);
  background: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-hover));
  color: white; border-radius: var(--radius-xl);
  padding: var(--space-6); margin-bottom: var(--space-6);
}
.hero-bloco.aporte {
  background: rgba(245, 158, 11, 0.2); border-radius: var(--radius-lg);
  padding: var(--space-4); text-align: right;
}
.hero-label { font-size: var(--text-xs); letter-spacing: 0.1em; opacity: 0.85; }
.hero-valor { font-size: var(--text-3xl); font-weight: 700; margin-top: var(--space-2); }
.hero-sub { font-size: var(--text-xs); opacity: 0.7; margin-top: 4px; }
.painel { margin-top: var(--space-4); }
.aporte-destaque { color: var(--brand-accent); font-weight: 700; }
.nome { color: var(--text-muted); font-size: var(--text-sm); margin-left: var(--space-2); }
.badge-mini { margin-right: var(--space-1); }
.vazio { padding: var(--space-6); text-align: center; color: var(--text-muted); }
</style>
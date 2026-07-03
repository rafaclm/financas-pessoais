<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { posicaoAtualService } from "@/services/posicaoAtual"
import type { PosicaoAtual } from "@/services/posicaoAtual"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import ProgressSpinner from "primevue/progressspinner"
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Wallet, TrendingUp as TrendingUpIcon, Sparkles, Award } from "lucide-vue-next"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()
const lista = ref([] as PosicaoAtual[])
const carregando = ref(false)
const atualizandoTodas = ref(false)

const filtroGeo = ref(null as string | null)
const filtroClasse = ref(null as string | null)

const dialogPrecoMedio = ref(false)
const ativoEditandoPM = ref(null as PosicaoAtual | null)
const precoMedioInput = ref(0)

const dialogPrecoTeto = ref(false)
const ativoEditandoTeto = ref(null as PosicaoAtual | null)
const precoTetoInput = ref(0)

const opcoesGeo = [
  { label: "🇧🇷 BR", value: "BR" },
  { label: "🇺🇸 EUA", value: "EUA" },
  { label: "🌐 Global", value: "GLOBAL" },
]
const opcoesClasse = [
  { label: "Ação", value: "acao" },
  { label: "ETF", value: "etf" },
  { label: "FII", value: "fii" },
  { label: "Fiagro", value: "fiagro" },
  { label: "REIT", value: "reit" },
  { label: "Cripto", value: "cripto" },
]

const listaFiltrada = computed(() => {
  return lista.value.filter(p => {
    if (filtroGeo.value && p.geografia !== filtroGeo.value) return false
    if (filtroClasse.value && p.classe !== filtroClasse.value) return false
    return true
  })
})

const totais = computed(() => {
  const total_brl = listaFiltrada.value.reduce((acc, p) => acc + Number(p.valor_atual_brl), 0)
  const custo_brl = listaFiltrada.value.reduce((acc, p) => acc + Number(p.custo_total_brl), 0)
  const proventos_brl = listaFiltrada.value.reduce((acc, p) => acc + Number(p.proventos_totais_brl), 0)
  const rentab_capital_pct = custo_brl > 0 ? ((total_brl - custo_brl) / custo_brl * 100) : null
  const rentab_total_pct = custo_brl > 0
    ? (((total_brl + proventos_brl) - custo_brl) / custo_brl * 100)
    : null
  return {
    qtd_ativos: listaFiltrada.value.length,
    valor_total_brl: total_brl,
    custo_total_brl: custo_brl,
    proventos_totais_brl: proventos_brl,
    rentabilidade_capital_pct: rentab_capital_pct,
    rentabilidade_total_pct: rentab_total_pct,
    ganho_total_brl: (total_brl + proventos_brl) - custo_brl,
  }
})

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

const fmtMoeda = (v: number, moeda: string) =>
  new Intl.NumberFormat(moeda === "BRL" ? "pt-BR" : "en-US",
    { style: "currency", currency: moeda }).format(v || 0)

const fmtQtd = (v: number) =>
  Number(v).toLocaleString("pt-BR", { maximumFractionDigits: 8 })

const fmtPct = (v: number | null) =>
  v === null || v === undefined ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`

const flagGeo = (g: string) =>
  ({ BR: "🇧🇷", EUA: "🇺🇸", GLOBAL: "🌐" } as any)[g] || g

const labelClasse = (c: string) =>
  ({ acao: "Ação", etf: "ETF", fii: "FII", fiagro: "Fiagro",
     reit: "REIT", cripto: "Cripto" } as any)[c] || c

const corClasse = (c: string) =>
  ({ acao: "#A78BFA", etf: "#22D3EE", fii: "#8B5CF6", fiagro: "#EAB308",
     reit: "#F472B6", cripto: "#F97316" } as any)[c] || "#94A3B8"

async function carregar() {
  carregando.value = true
  try {
    lista.value = await posicaoAtualService.listar({ apenas_com_posicao: true })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

async function atualizarTodas() {
  if (!confirm("Atualizar cotações de TODOS os ativos via APIs externas?")) return
  atualizandoTodas.value = true
  try {
    const r = await posicaoAtualService.atualizarTodasCotacoes()
    toast.add({
      severity: r.falhas > 0 ? "warn" : "success",
      summary: `${r.atualizados}/${r.total} atualizados`,
      detail: r.mensagem, life: 5000
    })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally {
    atualizandoTodas.value = false
  }
}

async function atualizarUm(item: PosicaoAtual) {
  try {
    await posicaoAtualService.atualizarCotacaoApi(item.ativo_id)
    toast.add({ severity: "success", summary: `${item.ticker} atualizado`, life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

function abrirPrecoMedio(item: PosicaoAtual) {
  ativoEditandoPM.value = item
  precoMedioInput.value = Number(item.preco_medio || 0)
  dialogPrecoMedio.value = true
}
async function salvarPrecoMedio() {
  if (!ativoEditandoPM.value) return
  try {
    await posicaoAtualService.definirPrecoMedioManual(
      ativoEditandoPM.value.ativo_id, precoMedioInput.value
    )
    toast.add({ severity: "success", summary: "Preço médio salvo", life: 2500 })
    dialogPrecoMedio.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
async function voltarPMAutomatico() {
  if (!ativoEditandoPM.value) return
  if (!confirm("Voltar ao preço médio automático?")) return
  try {
    await posicaoAtualService.voltarPrecoAutomatico(ativoEditandoPM.value.ativo_id)
    dialogPrecoMedio.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

function abrirPrecoTeto(item: PosicaoAtual) {
  ativoEditandoTeto.value = item
  precoTetoInput.value = Number(item.preco_teto || 0)
  dialogPrecoTeto.value = true
}
async function salvarPrecoTeto() {
  if (!ativoEditandoTeto.value) return
  try {
    await posicaoAtualService.definirPrecoTeto(
      ativoEditandoTeto.value.ativo_id, precoTetoInput.value
    )
    dialogPrecoTeto.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
async function removerTeto() {
  if (!ativoEditandoTeto.value) return
  if (!confirm("Remover o preço teto deste ativo?")) return
  try {
    await posicaoAtualService.removerPrecoTeto(ativoEditandoTeto.value.ativo_id)
    dialogPrecoTeto.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function recalcularTudo() {
  if (!confirm("Recalcular posições de TODOS os ativos a partir dos aportes?")) return
  try {
    const r = await posicaoAtualService.recalcular()
    toast.add({ severity: "success", summary: "Recálculo concluído", detail: r.mensagem, life: 4000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}
</script>

<template>
  <PageHeader title="📊 Posição Atual dos Ativos"
              subtitle="Visão sempre atualizada da sua carteira de renda variável">
    <template #actions>
      <Button label="Recalcular" icon="pi pi-refresh" outlined @click="recalcularTudo" />
      <Button :label="atualizandoTodas ? 'Atualizando...' : 'Atualizar cotações'"
              icon="pi pi-cloud-download"
              :loading="atualizandoTodas" @click="atualizarTodas" />
    </template>
  </PageHeader>

  <!-- 🆕 KPIs COM NOVO LAYOUT -->
  <section class="hero-stats">
    <div class="stat">
      <div class="stat-header">
        <div class="stat-icone" style="background: linear-gradient(135deg, #06B6D4, #22D3EE)">
          <Wallet :size="18" />
        </div>
        <span class="stat-label">TOTAL DA CARTEIRA</span>
      </div>
      <div class="stat-valor tabular">{{ fmtBRL(totais.valor_total_brl) }}</div>
    </div>

    <div class="stat">
      <div class="stat-header">
        <div class="stat-icone" style="background: linear-gradient(135deg, #A78BFA, #C4B5FD)">
          <Sparkles :size="18" />
        </div>
        <span class="stat-label">ATIVOS</span>
      </div>
      <div class="stat-valor">{{ totais.qtd_ativos }}</div>
    </div>

    <div class="stat success">
      <div class="stat-header">
        <div class="stat-icone" style="background: linear-gradient(135deg, #10B981, #34D399)">
          <TrendingUpIcon :size="18" />
        </div>
        <span class="stat-label">PROVENTOS TOTAIS</span>
      </div>
      <div class="stat-valor tabular">{{ fmtBRL(totais.proventos_totais_brl) }}</div>
    </div>

    <div class="stat" :class="{
      success: (totais.rentabilidade_capital_pct ?? 0) >= 0,
      danger: (totais.rentabilidade_capital_pct ?? 0) < 0
    }">
      <div class="stat-header">
        <div class="stat-icone" :style="{
          background: (totais.rentabilidade_capital_pct ?? 0) >= 0
            ? 'linear-gradient(135deg, #10B981, #34D399)'
            : 'linear-gradient(135deg, #F43F5E, #FB7185)'
        }">
          <TrendingUp v-if="(totais.rentabilidade_capital_pct ?? 0) >= 0" :size="18" />
          <TrendingDown v-else :size="18" />
        </div>
        <span class="stat-label">RENTAB. CAPITAL</span>
      </div>
      <div class="stat-valor tabular">{{ fmtPct(totais.rentabilidade_capital_pct) }}</div>
    </div>

    <div class="stat destaque" :class="{
      success: (totais.rentabilidade_total_pct ?? 0) >= 0,
      danger: (totais.rentabilidade_total_pct ?? 0) < 0
    }">
      <div class="stat-header">
        <div class="stat-icone dourado">
          <Award :size="18" />
        </div>
        <span class="stat-label">RENTAB. TOTAL 🏆</span>
      </div>
      <div class="stat-valor tabular">{{ fmtPct(totais.rentabilidade_total_pct) }}</div>
      <div class="stat-sub tabular" v-if="totais.ganho_total_brl !== null">
        {{ totais.ganho_total_brl > 0 ? "+" : "" }}{{ fmtBRL(totais.ganho_total_brl) }}
      </div>
    </div>
  </section>

  <div class="filtros">
    <div class="filtro-grupo">
      <label>Geografia</label>
      <Dropdown v-model="filtroGeo" :options="opcoesGeo"
                optionLabel="label" optionValue="value"
                placeholder="Todas" showClear
                :pt="{ root: { style: 'min-width: 160px' } }" />
    </div>
    <div class="filtro-grupo">
      <label>Classe</label>
      <Dropdown v-model="filtroClasse" :options="opcoesClasse"
                optionLabel="label" optionValue="value"
                placeholder="Todas" showClear
                :pt="{ root: { style: 'min-width: 160px' } }" />
    </div>
  </div>

  <div v-if="carregando" class="loading"><ProgressSpinner /></div>

  <DataTable v-else :value="listaFiltrada" stripedRows
             :paginator="true" :rows="50" scrollable scrollHeight="flex"
             sortMode="single" removableSort>
    <Column header="Ativo" frozen style="min-width: 110px" sortable sortField="ticker">
      <template #body="{ data }">
        <span class="ativo-cell">
          {{ flagGeo(data.geografia) }}
          <strong>{{ data.ticker }}</strong>
        </span>
      </template>
    </Column>
    <Column header="Classe" style="min-width: 80px" sortable sortField="classe">
      <template #body="{ data }">
        <Tag :value="labelClasse(data.classe)"
             :style="{ background: corClasse(data.classe), color: 'white' }" />
      </template>
    </Column>
    <Column header="Qtd" style="min-width: 100px; text-align: right" sortable sortField="quantidade">
      <template #body="{ data }">
        <span class="tabular">{{ fmtQtd(data.quantidade) }}</span>
      </template>
    </Column>
    <Column header="Preço Médio" style="min-width: 150px; text-align: right" sortable sortField="preco_medio">
      <template #body="{ data }">
        <div class="pm-cell">
          <span class="tabular value-muted">{{ fmtMoeda(data.preco_medio, data.moeda) }}</span>
          <Tag v-if="data.preco_medio_eh_manual" value="M"
               severity="warning" class="mini-tag" v-tooltip="'Manual'" />
          <Button icon="pi pi-pencil" text rounded size="small"
                  v-tooltip="'Editar PM'" @click="abrirPrecoMedio(data)" class="mini-btn" />
        </div>
      </template>
    </Column>
    <Column header="Cotação" style="min-width: 130px; text-align: right" sortable sortField="cotacao_atual">
      <template #body="{ data }">
        <span v-if="data.cotacao_atual" class="tabular">
          {{ fmtMoeda(data.cotacao_atual, data.moeda) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Rentab. Capital" style="min-width: 130px; text-align: right" sortable sortField="rentabilidade_pct">
      <template #body="{ data }">
        <span v-if="data.rentabilidade_pct !== null"
              class="variacao"
              :class="data.rentabilidade_pct >= 0 ? 'value-positive' : 'value-negative'">
          <TrendingUp v-if="data.rentabilidade_pct > 0" :size="14" />
          <TrendingDown v-else-if="data.rentabilidade_pct < 0" :size="14" />
          <Minus v-else :size="14" />
          {{ fmtPct(data.rentabilidade_pct) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Rentab. Total 🏆" style="min-width: 130px; text-align: right" sortable sortField="rentabilidade_total_pct">
      <template #body="{ data }">
        <span v-if="data.rentabilidade_total_pct !== null"
              class="variacao destaque-rentab"
              :class="data.rentabilidade_total_pct >= 0 ? 'value-positive' : 'value-negative'">
          <TrendingUp v-if="data.rentabilidade_total_pct > 0" :size="14" />
          <TrendingDown v-else-if="data.rentabilidade_total_pct < 0" :size="14" />
          <Minus v-else :size="14" />
          <strong>{{ fmtPct(data.rentabilidade_total_pct) }}</strong>
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Valor Atual (BRL)" style="min-width: 140px; text-align: right" sortable sortField="valor_atual_brl">
      <template #body="{ data }">
        <strong class="tabular">{{ fmtBRL(data.valor_atual_brl) }}</strong>
      </template>
    </Column>
    <Column header="Proventos" style="min-width: 130px; text-align: right" sortable sortField="proventos_totais_brl">
      <template #body="{ data }">
        <span class="tabular value-positive" v-if="data.proventos_totais_brl > 0">
          {{ fmtBRL(data.proventos_totais_brl) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="YoC" style="min-width: 90px; text-align: right" sortable sortField="yield_on_cost_pct">
      <template #body="{ data }">
        <span v-if="data.yield_on_cost_pct !== null" class="tabular value-positive">
          {{ data.yield_on_cost_pct.toFixed(2) }}%
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Preço Teto" style="min-width: 140px; text-align: right" sortable sortField="preco_teto">
      <template #body="{ data }">
        <div class="pm-cell">
          <span v-if="data.preco_teto" class="tabular value-muted">
            {{ fmtMoeda(data.preco_teto, data.moeda) }}
          </span>
          <span v-else class="value-muted">—</span>
          <Button icon="pi pi-pencil" text rounded size="small"
                  v-tooltip="'Editar teto'" @click="abrirPrecoTeto(data)" class="mini-btn" />
        </div>
      </template>
    </Column>
    <Column header="Margem" style="min-width: 130px; text-align: right" sortable sortField="margem_aporte_pct">
      <template #body="{ data }">
        <span v-if="data.margem_aporte_pct !== null" class="variacao"
              :class="data.acima_do_teto ? 'value-negative' : 'value-positive'">
          <AlertTriangle v-if="data.acima_do_teto" :size="14" />
          <TrendingUp v-else :size="14" />
          {{ fmtPct(data.margem_aporte_pct) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="" style="min-width: 60px">
      <template #body="{ data }">
        <Button icon="pi pi-refresh" text v-tooltip="'Atualizar cotação'"
                @click="atualizarUm(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total: <strong class="tabular">{{ fmtBRL(totais.valor_total_brl) }}</strong>
        ({{ totais.qtd_ativos }} ativos)
      </div>
    </template>
  </DataTable>

  <!-- Dialogs (mesmos de antes) -->
  <Dialog v-model:visible="dialogPrecoMedio"
          :header="`Preço Médio: ${ativoEditandoPM?.ticker || ''}`"
          modal :style="{ width: '460px' }">
    <div class="form">
      <div class="info-box">
        <div><strong>Calculado pelos aportes:</strong>
          <span class="tabular">{{
            ativoEditandoPM ? fmtMoeda(ativoEditandoPM.preco_medio_calculado, ativoEditandoPM.moeda) : '—'
          }}</span>
        </div>
        <div v-if="ativoEditandoPM?.preco_medio_eh_manual" class="manual-info">
          <Tag value="🖋️ Manual" severity="warning" />
        </div>
      </div>
      <label>Novo preço médio ({{ ativoEditandoPM?.moeda }})</label>
      <InputNumber v-model="precoMedioInput"
                   :minFractionDigits="2" :maxFractionDigits="8" :min="0"
                   :locale="ativoEditandoPM?.moeda === 'BRL' ? 'pt-BR' : 'en-US'" />
    </div>
    <template #footer>
      <Button v-if="ativoEditandoPM?.preco_medio_eh_manual"
              label="Voltar automático" severity="secondary" outlined
              @click="voltarPMAutomatico" />
      <Button label="Cancelar" text @click="dialogPrecoMedio = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvarPrecoMedio" />
    </template>
  </Dialog>

  <Dialog v-model:visible="dialogPrecoTeto"
          :header="`Preço Teto: ${ativoEditandoTeto?.ticker || ''}`"
          modal :style="{ width: '460px' }">
    <div class="form">
      <div class="info-box">
        <div><strong>Cotação atual:</strong>
          <span class="tabular">{{
            ativoEditandoTeto?.cotacao_atual
              ? fmtMoeda(ativoEditandoTeto.cotacao_atual, ativoEditandoTeto.moeda)
              : '—'
          }}</span>
        </div>
      </div>
      <label>Preço teto ({{ ativoEditandoTeto?.moeda }})</label>
      <InputNumber v-model="precoTetoInput"
                   :minFractionDigits="2" :maxFractionDigits="8" :min="0"
                   :locale="ativoEditandoTeto?.moeda === 'BRL' ? 'pt-BR' : 'en-US'" />
    </div>
    <template #footer>
      <Button v-if="ativoEditandoTeto?.preco_teto"
              label="Remover teto" severity="danger" outlined @click="removerTeto" />
      <Button label="Cancelar" text @click="dialogPrecoTeto = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvarPrecoTeto" />
    </template>
  </Dialog>
</template>

<style scoped>
/* ========================================
   💎 KPIs COM RESPIRAÇÃO ADEQUADA
   ======================================== */
.hero-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
@media (max-width: 1400px) {
  .hero-stats { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 900px) {
  .hero-stats { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .hero-stats { grid-template-columns: 1fr; }
}

.stat {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 24px;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: all 250ms ease;
  min-height: 140px;
}
.stat:hover {
  transform: translateY(-2px);
  border-color: var(--border-default);
  box-shadow: var(--shadow-md);
}

.stat.success {
  border-left: 3px solid var(--success);
}
.stat.danger {
  border-left: 3px solid var(--danger);
}

/* Card destaque (Rentab. Total) */
.stat.destaque {
  background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 100%);
  border: none;
  color: white;
  box-shadow: var(--shadow-md), 0 0 40px rgba(167, 139, 250, 0.25);
}
.stat.destaque .stat-label,
.stat.destaque .stat-valor,
.stat.destaque .stat-sub {
  color: white;
}
.stat.destaque .stat-sub {
  opacity: 0.9;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.stat-icone {
  width: 36px; height: 36px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  color: white;
  flex-shrink: 0;
}
.stat-icone.dourado {
  background: linear-gradient(135deg, #F59E0B, #FBBF24);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}

.stat-valor {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-numeric);
  letter-spacing: -0.02em;
  line-height: 1;
}

.stat-sub {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: auto;
}

/* ========================================
   FILTROS
   ======================================== */
.filtros {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}
.filtro-grupo {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.filtro-grupo label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.loading { display: flex; justify-content: center; padding: var(--space-12); }

/* ========================================
   TABELA
   ======================================== */
.ativo-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.pm-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  justify-content: flex-end;
}
.mini-tag {
  font-size: 10px !important;
  padding: 2px 4px !important;
}
.mini-btn {
  padding: 4px !important;
  min-width: auto !important;
}
.variacao {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}
.destaque-rentab {
  font-size: var(--text-sm);
}
.footer-total {
  text-align: right;
  font-size: var(--text-base);
  padding: var(--space-3) 0;
}

/* ========================================
   DIALOGS
   ======================================== */
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.form label {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-top: var(--space-2);
}
.info-box {
  background: var(--bg-elevated);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.manual-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
</style>
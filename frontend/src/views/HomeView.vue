<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { dashboardService } from "@/services/dashboard"
import type { DashboardDados } from "@/services/dashboard"
import { useToast } from "primevue/usetoast"
import { usePeriodoStore } from "@/stores/periodo"
import Button from "primevue/button"
import ProgressSpinner from "primevue/progressspinner"
import GraficoBase from "@/components/GraficoBase.vue"
import KPIAnimado from "@/components/KPIAnimado.vue"
import { TrendingUp, TrendingDown, Sparkles, Wallet, DollarSign } from "lucide-vue-next"

const router = useRouter()
const toast = useToast()
const periodo = usePeriodoStore()
const dados = ref<DashboardDados | null>(null)
const carregando = ref(false)

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

const fmtPct = (v: number | null) =>
  v === null || v === undefined ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`

async function carregar() {
  carregando.value = true
  try {
    dados.value = await dashboardService.obter()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

// Drill-downs
function clickDistribuicao(item: { label: string }) {
  const filtros: Record<string, { geografia?: string; classe?: string }> = {
    "💰 Liquidez": {},
    "🏦 Renda Fixa": {},
    "🇧🇷 RV Brasil": { geografia: "BR" },
    "🇺🇸 RV EUA": { geografia: "EUA" },
    "₿ Cripto": { classe: "cripto" },
  }
  const f = filtros[item.label]
  if (f) {
    const query: any = {}
    if (f.geografia) query.geografia = f.geografia
    if (f.classe) query.classe = f.classe
    router.push({ path: "/posicoes/posicao-atual", query })
    toast.add({ severity: "info", summary: `Filtrado: ${item.label}`, life: 2500 })
  }
}

function clickReceitasDespesas(item: { datasetIndex: number; label: string }) {
  const [mes, ano] = item.label.split("/")
  const mesesMap: Record<string, number> = {
    Jan: 1, Fev: 2, Mar: 3, Abr: 4, Mai: 5, Jun: 6,
    Jul: 7, Ago: 8, Set: 9, Out: 10, Nov: 11, Dez: 12
  }
  const mesNum = mesesMap[mes]
  const anoNum = 2000 + parseInt(ano)
  const anoObj = periodo.anosDisponiveis.find(a => a.ano === anoNum)
  if (anoObj && mesNum) {
    periodo.definir(anoObj.id, mesNum)
    const destino = item.datasetIndex === 0 ? "/lancamentos/receitas" : "/lancamentos/despesas"
    router.push(destino)
  }
}

function clickRendaPassiva(item: { label: string }) {
  const [mes, ano] = item.label.split("/")
  const mesesMap: Record<string, number> = {
    Jan: 1, Fev: 2, Mar: 3, Abr: 4, Mai: 5, Jun: 6,
    Jul: 7, Ago: 8, Set: 9, Out: 10, Nov: 11, Dez: 12
  }
  const mesNum = mesesMap[mes]
  const anoNum = 2000 + parseInt(ano)
  const anoObj = periodo.anosDisponiveis.find(a => a.ano === anoNum)
  if (anoObj && mesNum) {
    periodo.definir(anoObj.id, mesNum)
    router.push("/lancamentos/proventos")
  }
}

function clickComparativoAnual(item: { label: string }) {
  const anoNum = parseInt(item.label)
  const anoObj = periodo.anosDisponiveis.find(a => a.ano === anoNum)
  if (anoObj) {
    periodo.definir(anoObj.id, periodo.mesSelecionado)
    toast.add({ severity: "success", summary: `Período: ${item.label}`, life: 2500 })
  }
}

function clickEvolucao(item: { label: string }) {
  const [mes, ano] = item.label.split("/")
  const mesesMap: Record<string, number> = {
    Jan: 1, Fev: 2, Mar: 3, Abr: 4, Mai: 5, Jun: 6,
    Jul: 7, Ago: 8, Set: 9, Out: 10, Nov: 11, Dez: 12
  }
  const mesNum = mesesMap[mes]
  const anoNum = 2000 + parseInt(ano)
  const anoObj = periodo.anosDisponiveis.find(a => a.ano === anoNum)
  if (anoObj && mesNum) {
    periodo.definir(anoObj.id, mesNum)
    router.push("/posicoes/consolidacao-patrimonial")
  }
}

// GRÁFICOS
const dataEvolucao = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  return {
    labels: dados.value.evolucao_patrimonial.map(p => p.label),
    datasets: [{
      label: "Patrimônio",
      data: dados.value.evolucao_patrimonial.map(p => p.patrimonio_total),
      borderColor: "#A78BFA",
      backgroundColor: "rgba(167, 139, 250, 0.15)",
      borderWidth: 3, tension: 0.3, fill: true,
      pointRadius: 3, pointHoverRadius: 8,
      pointBackgroundColor: "#A78BFA",
    }]
  }
})

const opcoesEvolucao = computed(() => ({
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const valor = ctx.parsed.y
          const arr = dados.value?.evolucao_patrimonial || []
          const ant = arr[ctx.dataIndex - 1]
          let extra = ""
          if (ant && ant.patrimonio_total > 0) {
            const variacao = (valor - ant.patrimonio_total) / ant.patrimonio_total * 100
            const delta = valor - ant.patrimonio_total
            extra = `\n${delta > 0 ? "▲" : "▼"} ${fmtPct(variacao)} (${fmtBRL(delta)})`
          }
          return [`Patrimônio: ${fmtBRL(valor)}`, extra].filter(Boolean)
        }
      }
    }
  },
  scales: {
    y: { ticks: { callback: (v: any) => "R$ " + (v / 1000).toFixed(0) + "k" } }
  }
}))

const dataDistribuicao = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  const cores: Record<string, string> = {
    "💰 Liquidez": "#06B6D4",
    "🏦 Renda Fixa": "#3B82F6",
    "🇧🇷 RV Brasil": "#A78BFA",
    "🇺🇸 RV EUA": "#EC4899",
    "₿ Cripto": "#F97316",
  }
  return {
    labels: dados.value.distribuicao_carteira.map(f => f.categoria),
    datasets: [{
      data: dados.value.distribuicao_carteira.map(f => f.valor),
      backgroundColor: dados.value.distribuicao_carteira.map(f => cores[f.categoria] || f.cor),
      borderColor: "transparent",
      borderWidth: 2, hoverOffset: 10,
    }]
  }
})

const opcoesDistribuicao = computed(() => ({
  plugins: {
    legend: { position: "right" as const, labels: { padding: 12 } },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const pct = (ctx.parsed / total * 100).toFixed(1)
          return `${ctx.label}: ${fmtBRL(ctx.parsed)} (${pct}%)`
        }
      }
    }
  },
  cutout: "68%"
}))

const dataReceitasDespesas = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  return {
    labels: dados.value.receitas_despesas.map(m => m.label),
    datasets: [
      {
        label: "Receitas",
        data: dados.value.receitas_despesas.map(m => m.receitas),
        backgroundColor: "rgba(16, 185, 129, 0.7)",
        borderColor: "#10B981", borderWidth: 2, borderRadius: 6,
      },
      {
        label: "Despesas",
        data: dados.value.receitas_despesas.map(m => m.despesas),
        backgroundColor: "rgba(244, 63, 94, 0.7)",
        borderColor: "#F43F5E", borderWidth: 2, borderRadius: 6,
      }
    ]
  }
})

const opcoesReceitasDespesas = computed(() => ({
  plugins: {
    tooltip: {
      callbacks: { label: (ctx: any) => `${ctx.dataset.label}: ${fmtBRL(ctx.parsed.y)}` }
    }
  },
  scales: {
    y: { ticks: { callback: (v: any) => "R$ " + (v / 1000).toFixed(0) + "k" } }
  }
}))

const dataRendaPassiva = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  return {
    labels: dados.value.renda_passiva.map(m => m.label),
    datasets: [{
      label: "Proventos",
      data: dados.value.renda_passiva.map(m => m.total),
      backgroundColor: "rgba(221, 183, 255, 0.7)",
      borderColor: "#DDB7FF", borderWidth: 2, borderRadius: 6,
    }]
  }
})

const opcoesRendaPassiva = computed(() => ({
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (ctx: any) => `Proventos: ${fmtBRL(ctx.parsed.y)}` } }
  },
  scales: { y: { ticks: { callback: (v: any) => "R$ " + v.toFixed(0) } } }
}))

const dataComparativoAnual = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  return {
    labels: dados.value.comparativo_anual.map(c => c.ano.toString()),
    datasets: [
      {
        label: "Receitas", data: dados.value.comparativo_anual.map(c => c.receitas),
        backgroundColor: "rgba(16, 185, 129, 0.7)", borderColor: "#10B981", borderWidth: 2, borderRadius: 6,
      },
      {
        label: "Despesas", data: dados.value.comparativo_anual.map(c => c.despesas),
        backgroundColor: "rgba(244, 63, 94, 0.7)", borderColor: "#F43F5E", borderWidth: 2, borderRadius: 6,
      },
      {
        label: "Proventos", data: dados.value.comparativo_anual.map(c => c.proventos),
        backgroundColor: "rgba(221, 183, 255, 0.7)", borderColor: "#DDB7FF", borderWidth: 2, borderRadius: 6,
      }
    ]
  }
})

const opcoesComparativoAnual = computed(() => ({
  plugins: {
    tooltip: { callbacks: { label: (ctx: any) => `${ctx.dataset.label}: ${fmtBRL(ctx.parsed.y)}` } }
  },
  scales: { y: { ticks: { callback: (v: any) => "R$ " + (v / 1000).toFixed(0) + "k" } } }
}))

const dataSaldoInvestimentos = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  return {
    labels: dados.value.saldo_investimentos.map(p => p.label),
    datasets: [
      {
        label: "Renda Fixa", data: dados.value.saldo_investimentos.map(p => p.renda_fixa),
        borderColor: "#3B82F6", backgroundColor: "rgba(59, 130, 246, 0.1)",
        borderWidth: 2, tension: 0.3, fill: false, pointRadius: 2,
      },
      {
        label: "Previdência", data: dados.value.saldo_investimentos.map(p => p.previdencia),
        borderColor: "#A78BFA", backgroundColor: "rgba(167, 139, 250, 0.1)",
        borderWidth: 2, tension: 0.3, fill: false, pointRadius: 2,
      },
      {
        label: "FGTS", data: dados.value.saldo_investimentos.map(p => p.fgts),
        borderColor: "#B0C6FF", backgroundColor: "rgba(176, 198, 255, 0.1)",
        borderWidth: 2, tension: 0.3, fill: false, pointRadius: 2,
      }
    ]
  }
})

const opcoesSaldoInvestimentos = computed(() => ({
  plugins: {
    tooltip: { callbacks: { label: (ctx: any) => `${ctx.dataset.label}: ${fmtBRL(ctx.parsed.y)}` } }
  },
  scales: { y: { ticks: { callback: (v: any) => "R$ " + (v / 1000).toFixed(0) + "k" } } }
}))

const dataDistribuicaoMensal = computed(() => {
  if (!dados.value) return { labels: [], datasets: [] }
  return {
    labels: dados.value.distribuicao_mensal.map(p => p.label),
    datasets: [
      {
        label: "🇧🇷 RV Brasil", data: dados.value.distribuicao_mensal.map(p => p.rv_br),
        backgroundColor: "rgba(167, 139, 250, 0.7)", borderColor: "#A78BFA", fill: true, tension: 0.3,
      },
      {
        label: "🇺🇸 RV EUA", data: dados.value.distribuicao_mensal.map(p => p.rv_eua),
        backgroundColor: "rgba(236, 72, 153, 0.7)", borderColor: "#EC4899", fill: true, tension: 0.3,
      },
      {
        label: "₿ Cripto", data: dados.value.distribuicao_mensal.map(p => p.cripto),
        backgroundColor: "rgba(249, 115, 22, 0.7)", borderColor: "#F97316", fill: true, tension: 0.3,
      }
    ]
  }
})

const opcoesDistribuicaoMensal = computed(() => ({
  plugins: {
    tooltip: { callbacks: { label: (ctx: any) => `${ctx.dataset.label}: ${fmtBRL(ctx.parsed.y)}` } }
  },
  scales: {
    y: { stacked: true, ticks: { callback: (v: any) => "R$ " + (v / 1000).toFixed(0) + "k" } },
    x: { stacked: true }
  }
}))
</script>

<template>
  <div>
    <!-- HERO -->
    <header class="hero">
      <div class="hero-titulo">
        <h1>👋 Bem-vindo, Rafael!</h1>
        <p class="muted">Visão geral da sua vida financeira</p>
      </div>
      <div class="hero-badges">
        <div class="badge-live">
          <span class="dot"></span>
          LIVE MARKET DATA
        </div>
        <Button label="Refresh" outlined icon="pi pi-refresh"
                :loading="carregando" @click="carregar" />
      </div>
    </header>

    <div v-if="carregando && !dados" class="loading"><ProgressSpinner /></div>

    <template v-else-if="dados">
      <!-- 💎 KPIs DO TOPO -->
      <section class="grid-kpis">
        <!-- KPI PRINCIPAL (destaque com gradiente) -->
        <div class="kpi-card destaque">
          <div class="kpi-decoracao">
            <div class="circle-deco c1"></div>
            <div class="circle-deco c2"></div>
          </div>
          <div class="kpi-conteudo">
            <div class="kpi-header">
              <div class="kpi-icon-glass"><Sparkles :size="18" /></div>
              <span class="kpi-label">PATRIMÔNIO TOTAL</span>
            </div>
            <div class="kpi-valor-grande tabular">
              <KPIAnimado :valor="dados.kpis.patrimonio_total" formato="brl" :decimais="2" />
            </div>
            <div v-if="dados.kpis.variacao_mes_pct !== null" class="kpi-sub"
                 :class="dados.kpis.variacao_mes_pct >= 0 ? 'positiva' : 'negativa'">
              <TrendingUp v-if="dados.kpis.variacao_mes_pct >= 0" :size="14" />
              <TrendingDown v-else :size="14" />
              <span class="tabular">{{ fmtPct(dados.kpis.variacao_mes_pct) }}</span>
              <span class="kpi-sub-texto">vs mês anterior</span>
            </div>
          </div>
        </div>

        <!-- KPI Proventos -->
        <div class="kpi-card">
          <div class="kpi-header">
            <div class="kpi-icon proventos"><Wallet :size="18" /></div>
            <span class="kpi-label">PROVENTOS NO MÊS</span>
          </div>
          <div class="kpi-valor tabular">
            <KPIAnimado :valor="dados.kpis.proventos_mes" formato="brl" :decimais="2" />
          </div>
          <div class="kpi-nota">Baseado em dividendos recebidos</div>
        </div>

        <!-- KPI Currency -->
        <div class="kpi-card">
          <div class="kpi-header">
            <div class="kpi-icon currency"><DollarSign :size="18" /></div>
            <span class="kpi-label">CURRENCY (BRL/USD)</span>
          </div>
          <div class="kpi-currency">
            <div class="currency-line">
              <span class="currency-label">BRL</span>
              <span class="tabular value-positive">+{{ dados.kpis.distribuicao_brl_pct.toFixed(1) }}%</span>
            </div>
            <div class="currency-line">
              <span class="currency-label">USD</span>
              <span class="tabular value-positive">+{{ dados.kpis.distribuicao_usd_pct.toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 📈 EVOLUÇÃO PATRIMONIAL -->
      <section class="card-grafico full">
        <div class="card-header-linha">
          <div>
            <h2>📈 Evolução Patrimonial</h2>
            <p class="hint">Últimos 24 meses • Clique em um ponto para detalhes</p>
          </div>
        </div>
        <div class="grafico-container alto">
          <GraficoBase type="line" :data="dataEvolucao" :options="opcoesEvolucao" :onItemClick="clickEvolucao" />
        </div>
      </section>

      <div class="grid-2">
        <section class="card-grafico">
          <h2>🥧 Distribuição da Carteira</h2>
          <p class="hint">Clique numa fatia para filtrar</p>
          <div class="grafico-container">
            <GraficoBase type="doughnut" :data="dataDistribuicao" :options="opcoesDistribuicao" :onItemClick="clickDistribuicao" />
          </div>
        </section>

        <section class="card-grafico">
          <h2>💎 Renda Passiva Mensal</h2>
          <p class="hint">Clique numa barra para ver os proventos</p>
          <div class="grafico-container">
            <GraficoBase type="bar" :data="dataRendaPassiva" :options="opcoesRendaPassiva" :onItemClick="clickRendaPassiva" />
          </div>
        </section>
      </div>

      <section class="card-grafico full">
        <h2>📊 Receitas vs Despesas</h2>
        <p class="hint">Últimos 12 meses</p>
        <div class="grafico-container alto">
          <GraficoBase type="bar" :data="dataReceitasDespesas" :options="opcoesReceitasDespesas" :onItemClick="clickReceitasDespesas" />
        </div>
      </section>

      <section class="card-grafico full">
        <h2>📈 Comparativo Anual</h2>
        <p class="hint">Clique num ano para mudar o período</p>
        <div class="grafico-container">
          <GraficoBase type="bar" :data="dataComparativoAnual" :options="opcoesComparativoAnual" :onItemClick="clickComparativoAnual" />
        </div>
      </section>

      <section class="card-grafico full">
        <h2>💰 Saldo de Investimentos</h2>
        <p class="hint">Renda Fixa, Previdência e FGTS</p>
        <div class="grafico-container alto">
          <GraficoBase type="line" :data="dataSaldoInvestimentos" :options="opcoesSaldoInvestimentos" />
        </div>
      </section>

      <section class="card-grafico full">
        <h2>🌎 Distribuição BR / EUA / Cripto</h2>
        <p class="hint">Evolução mensal da composição</p>
        <div class="grafico-container alto">
          <GraficoBase type="line" :data="dataDistribuicaoMensal" :options="opcoesDistribuicaoMensal" />
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
/* HERO */
.hero {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: var(--space-8);
  gap: var(--space-4); flex-wrap: wrap;
}
.hero-titulo h1 {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
}
.muted { color: var(--text-muted); margin-top: 4px; font-size: var(--text-sm); }

.hero-badges { display: flex; gap: var(--space-3); align-items: center; }

.badge-live {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
  color: var(--text-secondary); text-transform: uppercase;
}
.badge-live .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--brand-primary);
  box-shadow: 0 0 8px var(--brand-primary);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.loading { display: flex; justify-content: center; padding: var(--space-12); }

/* ========================================
   💎 KPIs — Novo layout com respiração
   ======================================== */
.grid-kpis {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: var(--space-5);
  margin-bottom: var(--space-8);
}
@media (max-width: 1100px) {
  .grid-kpis { grid-template-columns: 1fr; }
}

.kpi-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: 28px;
  transition: all 250ms ease;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.kpi-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-default);
  box-shadow: var(--shadow-md);
}

/* Card destaque (Patrimônio) */
.kpi-card.destaque {
  background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 50%, #A78BFA 100%);
  border: none;
  color: white;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 20px 60px rgba(76, 29, 149, 0.4),
    0 0 60px rgba(167, 139, 250, 0.25);
}
.kpi-decoracao {
  position: absolute; inset: 0;
  overflow: hidden; pointer-events: none;
}
.circle-deco {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
}
.circle-deco.c1 {
  width: 180px; height: 180px;
  top: -60px; right: -60px;
}
.circle-deco.c2 {
  width: 100px; height: 100px;
  bottom: -30px; right: 120px;
  background: rgba(221, 183, 255, 0.15);
}
.kpi-conteudo {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  height: 100%;
}

.kpi-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.kpi-icon-glass {
  width: 36px; height: 36px;
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  display: flex; align-items: center; justify-content: center;
  color: white;
}

.kpi-icon {
  width: 36px; height: 36px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  color: white;
}
.kpi-icon.proventos {
  background: linear-gradient(135deg, #10B981, #06B6D4);
}
.kpi-icon.currency {
  background: linear-gradient(135deg, #F97316, #F59E0B);
}

.kpi-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  font-weight: 600;
}
.kpi-card.destaque .kpi-label {
  color: rgba(255,255,255,0.85);
}

.kpi-valor-grande {
  font-family: var(--font-mono);
  font-size: 40px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.03em;
  line-height: 1;
  text-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.kpi-valor {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text-numeric);
  letter-spacing: -0.02em;
  line-height: 1;
}

.kpi-sub {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  padding: 8px 14px;
  border-radius: var(--radius-full);
  align-self: flex-start;
  margin-top: auto;
  backdrop-filter: blur(10px);
}
.kpi-sub.positiva {
  background: rgba(16, 185, 129, 0.25);
  color: white;
  border: 1px solid rgba(16, 185, 129, 0.4);
}
.kpi-sub.negativa {
  background: rgba(244, 63, 94, 0.25);
  color: white;
  border: 1px solid rgba(244, 63, 94, 0.4);
}
.kpi-sub-texto {
  opacity: 0.85;
  font-weight: 400;
}

.kpi-nota {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: auto;
}

.kpi-currency {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.currency-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-subtle);
}
.currency-line:last-child { border-bottom: none; }
.currency-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

/* ========================================
   📊 GRÁFICOS
   ======================================== */
.card-grafico {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 28px;
  margin-bottom: var(--space-4);
  transition: border-color 200ms ease;
}
.card-grafico:hover { border-color: var(--border-default); }
.card-grafico.full { width: 100%; }
.card-grafico h2 {
  font-size: var(--text-lg);
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.01em;
}
.hint {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-bottom: var(--space-4);
}

.card-header-linha {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.grafico-container { height: 300px; }
.grafico-container.alto { height: 380px; }

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}
@media (max-width: 1000px) {
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
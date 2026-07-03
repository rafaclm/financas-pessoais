<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import { consolidacaoService } from "@/services/consolidacao"
import type { ConsolidacaoPatrimonial } from "@/services/consolidacao"
import { useToast } from "primevue/usetoast"
import ProgressSpinner from "primevue/progressspinner"
import Tag from "primevue/tag"
import { TrendingUp, TrendingDown, Wallet, PiggyBank, BarChart3, Bitcoin, Sparkles } from "lucide-vue-next"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()
const dados = ref(null as ConsolidacaoPatrimonial | null)
const carregando = ref(false)

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

const fmtPct = (v: number) =>
  `${v > 0 ? "+" : ""}${v.toFixed(2)}%`

const MESES = [
  "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
  "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
]

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    dados.value = await consolidacaoService.patrimonial(
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
  <PageHeader title="🌟 Consolidação Patrimonial"
              :subtitle="`Visão completa do seu patrimônio · ${periodo.labelPeriodo}`" />

  <div v-if="carregando" class="loading"><ProgressSpinner /></div>

  <template v-else-if="dados">
    <!-- 💎 HERO PATRIMÔNIO (novo estilo premium) -->
    <section class="hero-patrimonio">
      <div class="hero-conteudo">
        <div class="hero-topo">
          <div class="hero-label">
            <Sparkles :size="16" />
            <span>PATRIMÔNIO TOTAL</span>
          </div>
        </div>
        <div class="hero-valor tabular">{{ fmtBRL(dados.patrimonio_total) }}</div>
        <div class="hero-variacoes">
          <div v-if="dados.variacao_mes_anterior" class="hero-var"
               :class="dados.variacao_mes_anterior.variacao_pct >= 0 ? 'positiva' : 'negativa'">
            <TrendingUp v-if="dados.variacao_mes_anterior.variacao_pct >= 0" :size="16" />
            <TrendingDown v-else :size="16" />
            <span class="var-pct tabular">{{ fmtPct(dados.variacao_mes_anterior.variacao_pct) }}</span>
            <span class="var-valor tabular">({{ fmtBRL(dados.variacao_mes_anterior.diferenca) }})</span>
            <span class="var-label">vs. mês anterior</span>
          </div>
          <div v-if="dados.variacao_ano_anterior" class="hero-var"
               :class="dados.variacao_ano_anterior.variacao_pct >= 0 ? 'positiva' : 'negativa'">
            <TrendingUp v-if="dados.variacao_ano_anterior.variacao_pct >= 0" :size="16" />
            <TrendingDown v-else :size="16" />
            <span class="var-pct tabular">{{ fmtPct(dados.variacao_ano_anterior.variacao_pct) }}</span>
            <span class="var-valor tabular">({{ fmtBRL(dados.variacao_ano_anterior.diferenca) }})</span>
            <span class="var-label">vs. {{ MESES[dados.periodo.mes - 1] }} ano anterior</span>
          </div>
        </div>
      </div>
      <div class="hero-decoracao">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
      </div>
    </section>

    <!-- 📊 4 CATEGORIAS -->
    <section class="grid-categorias">
      <div class="card-cat">
        <div class="cat-icone" style="background: linear-gradient(135deg, #06B6D4, #22D3EE)">
          <Wallet :size="20" />
        </div>
        <div class="cat-label">LIQUIDEZ</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_liquidez) }}</div>
        <div class="cat-pct">{{ dados.pct_liquidez.toFixed(1) }}% do patrimônio</div>
        <div class="cat-bar">
          <div :style="{ width: dados.pct_liquidez + '%', background: '#06B6D4' }"></div>
        </div>
      </div>
      <div class="card-cat">
        <div class="cat-icone" style="background: linear-gradient(135deg, #3B82F6, #60A5FA)">
          <PiggyBank :size="20" />
        </div>
        <div class="cat-label">RENDA FIXA</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_renda_fixa) }}</div>
        <div class="cat-pct">{{ dados.pct_renda_fixa.toFixed(1) }}% do patrimônio</div>
        <div class="cat-bar">
          <div :style="{ width: dados.pct_renda_fixa + '%', background: '#3B82F6' }"></div>
        </div>
      </div>
      <div class="card-cat">
        <div class="cat-icone" style="background: linear-gradient(135deg, #A78BFA, #C4B5FD)">
          <BarChart3 :size="20" />
        </div>
        <div class="cat-label">RENDA VARIÁVEL</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_renda_variavel) }}</div>
        <div class="cat-pct">{{ dados.pct_renda_variavel.toFixed(1) }}% do patrimônio</div>
        <div class="cat-bar">
          <div :style="{ width: dados.pct_renda_variavel + '%', background: '#A78BFA' }"></div>
        </div>
      </div>
      <div class="card-cat">
        <div class="cat-icone" style="background: linear-gradient(135deg, #F97316, #FB923C)">
          <Bitcoin :size="20" />
        </div>
        <div class="cat-label">CRIPTOATIVOS</div>
        <div class="cat-valor tabular">{{ fmtBRL(dados.total_cripto) }}</div>
        <div class="cat-pct">{{ dados.pct_cripto.toFixed(1) }}% do patrimônio</div>
        <div class="cat-bar">
          <div :style="{ width: dados.pct_cripto + '%', background: '#F97316' }"></div>
        </div>
      </div>
    </section>

    <!-- 💱 DISTRIBUIÇÃO POR MOEDA -->
    <section class="secao">
      <h2 class="secao-titulo">💱 Distribuição por moeda</h2>
      <div class="moedas-grid">
        <div class="moeda-card brl">
          <div class="moeda-badge">BR</div>
          <div class="moeda-info">
            <div class="moeda-label">EM BRL</div>
            <div class="moeda-pct tabular">{{ dados.pct_brl.toFixed(1) }}%</div>
            <div class="moeda-valor tabular">
              {{ fmtBRL(dados.patrimonio_total * dados.pct_brl / 100) }}
            </div>
          </div>
        </div>
        <div class="moeda-card usd">
          <div class="moeda-badge">US</div>
          <div class="moeda-info">
            <div class="moeda-label">EM USD (CONVERTIDO)</div>
            <div class="moeda-pct tabular">{{ dados.pct_usd.toFixed(1) }}%</div>
            <div class="moeda-valor tabular">
              {{ fmtBRL(dados.patrimonio_total * dados.pct_usd / 100) }}
            </div>
          </div>
        </div>
        <div v-if="dados.cotacao_usd_brl" class="cotacao-badge">
          <span class="lbl">Cotação aplicada</span>
          <strong class="tabular">R$ {{ dados.cotacao_usd_brl.toFixed(4) }}</strong>
          <span class="unit">/ USD</span>
        </div>
      </div>
    </section>

    <!-- 🎯 COMPONENTES -->
    <section class="secao">
      <h2 class="secao-titulo">🎯 Componentes do patrimônio</h2>
      <div v-if="dados.componentes.length === 0" class="vazio">
        Nenhum componente cadastrado neste período.<br>
        Comece lançando saldos de contas, investimentos, criptoativos e ações.
      </div>
      <div v-else class="comp-grid">
        <div v-for="c in dados.componentes" :key="c.categoria" class="comp-card"
             :style="{ '--comp-cor': c.cor || '#94A3B8' } as any">
          <div class="comp-header">
            <span class="comp-label">{{ c.label }}</span>
            <span class="comp-pct tabular">{{ c.percentual_total.toFixed(1) }}%</span>
          </div>
          <div class="comp-valor tabular">{{ fmtBRL(c.valor_brl) }}</div>
          <div class="comp-bar">
            <div :style="{ width: c.percentual_total + '%' }"></div>
          </div>
        </div>
      </div>
    </section>
  </template>
</template>

<style scoped>
.loading { display: flex; justify-content: center; padding: var(--space-12); }

/* ========================================
   🎨 HERO PATRIMÔNIO — Nova identidade premium
   ======================================== */
.hero-patrimonio {
  position: relative;
  background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 40%, #A78BFA 100%);
  border-radius: var(--radius-2xl);
  padding: 40px 48px;
  margin-bottom: var(--space-6);
  color: white;
  overflow: hidden;
  box-shadow:
    0 20px 60px rgba(76, 29, 149, 0.4),
    0 0 60px rgba(167, 139, 250, 0.25);
}

.hero-conteudo {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.hero-topo {
  display: flex;
  align-items: center;
}

.hero-label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px 14px;
  background: rgba(255,255,255,0.15);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  backdrop-filter: blur(10px);
}

.hero-valor {
  font-family: var(--font-mono);
  font-size: 56px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
  margin: var(--space-2) 0 var(--space-4);
  color: white;
  text-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.hero-variacoes {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.hero-var {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px 18px;
  border-radius: var(--radius-full);
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  font-size: var(--text-sm);
  font-weight: 500;
}
.hero-var.positiva {
  background: rgba(16, 185, 129, 0.25);
  border: 1px solid rgba(16, 185, 129, 0.4);
}
.hero-var.negativa {
  background: rgba(244, 63, 94, 0.25);
  border: 1px solid rgba(244, 63, 94, 0.4);
}

.var-pct { font-weight: 700; font-size: var(--text-base); }
.var-valor { opacity: 0.9; font-size: var(--text-xs); }
.var-label {
  opacity: 0.75;
  font-size: var(--text-xs);
  margin-left: var(--space-1);
}

/* Círculos decorativos */
.hero-decoracao {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
}
.circle-1 {
  width: 280px; height: 280px;
  top: -80px; right: -80px;
}
.circle-2 {
  width: 180px; height: 180px;
  bottom: -60px; right: 200px;
  background: rgba(221, 183, 255, 0.15);
}

/* ========================================
   🎯 CATEGORIAS
   ======================================== */
.grid-categorias {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}
@media (max-width: 1200px) {
  .grid-categorias { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .grid-categorias { grid-template-columns: 1fr; }
}

.card-cat {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: all 250ms ease;
}
.card-cat:hover {
  transform: translateY(-3px);
  border-color: var(--border-default);
  box-shadow: var(--shadow-md);
}

.cat-icone {
  width: 44px; height: 44px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  color: white;
  margin-bottom: var(--space-2);
}

.cat-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}

.cat-valor {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-numeric);
  letter-spacing: -0.02em;
  margin: 4px 0;
}

.cat-pct {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.cat-bar {
  height: 4px;
  background: var(--bg-elevated);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--space-3);
}
.cat-bar > div {
  height: 100%;
  transition: width 800ms cubic-bezier(0.16, 1, 0.3, 1);
  border-radius: var(--radius-full);
}

/* ========================================
   📊 SEÇÕES
   ======================================== */
.secao { margin-bottom: var(--space-8); }
.secao-titulo {
  font-size: var(--text-xl);
  color: var(--text-primary);
  margin-bottom: var(--space-4);
  font-weight: 600;
  letter-spacing: -0.01em;
}

/* ========================================
   💱 MOEDAS
   ======================================== */
.moedas-grid {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: var(--space-4);
  align-items: stretch;
}
@media (max-width: 900px) {
  .moedas-grid { grid-template-columns: 1fr; }
}

.moeda-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 20px 24px;
  transition: border-color 200ms ease;
}
.moeda-card:hover { border-color: var(--border-default); }

.moeda-badge {
  width: 56px; height: 56px;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: var(--text-lg);
  flex-shrink: 0;
}
.moeda-card.brl .moeda-badge {
  background: linear-gradient(135deg, #10B981, #34D399);
  color: white;
}
.moeda-card.usd .moeda-badge {
  background: linear-gradient(135deg, #3B82F6, #60A5FA);
  color: white;
}

.moeda-info { display: flex; flex-direction: column; gap: 2px; }
.moeda-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}
.moeda-pct {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-numeric);
  letter-spacing: -0.02em;
}
.moeda-valor {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.cotacao-badge {
  display: flex; flex-direction: column;
  justify-content: center;
  padding: 20px 24px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  gap: 4px;
}
.cotacao-badge .lbl {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}
.cotacao-badge strong {
  font-family: var(--font-mono);
  color: var(--text-numeric);
  font-size: var(--text-lg);
}
.cotacao-badge .unit {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

/* ========================================
   🎯 COMPONENTES
   ======================================== */
.vazio {
  padding: var(--space-12);
  text-align: center;
  color: var(--text-muted);
  background: var(--bg-surface);
  border-radius: var(--radius-xl);
  border: 1px dashed var(--border-default);
}

.comp-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}
@media (max-width: 1000px) {
  .comp-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .comp-grid { grid-template-columns: 1fr; }
}

.comp-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--comp-cor);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all 200ms ease;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.comp-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-default);
  border-left-color: var(--comp-cor);
}

.comp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.comp-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}
.comp-pct {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--comp-cor);
  padding: 3px 10px;
  background: rgba(255,255,255,0.05);
  border-radius: var(--radius-full);
}

.comp-valor {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.comp-bar {
  height: 4px;
  background: var(--bg-elevated);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.comp-bar > div {
  height: 100%;
  background: var(--comp-cor);
  transition: width 800ms cubic-bezier(0.16, 1, 0.3, 1);
}
</style>
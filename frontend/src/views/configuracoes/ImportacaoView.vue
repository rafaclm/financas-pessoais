<script setup lang="ts">
import { ref, computed } from "vue"
import { importacaoService } from "@/services/importacao"
import type {
  AnaliseArquivo, RelatorioImportacao, ExploradorRelatorio,
  RelatorioMovimentos, AnaliseAportes, AnaliseProventos, RelatorioGenerico
} from "@/services/importacao"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Tag from "primevue/tag"
import Message from "primevue/message"
import Dialog from "primevue/dialog"
import Dropdown from "primevue/dropdown"
import Checkbox from "primevue/checkbox"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()
const arquivoSelecionado = ref<File | null>(null)
const analise = ref<AnaliseArquivo | null>(null)
const preview = ref<RelatorioImportacao | null>(null)
const relatorioFinal = ref<RelatorioImportacao | null>(null)
const exploracao = ref<ExploradorRelatorio | null>(null)
const previewMov = ref<RelatorioMovimentos | null>(null)
const relatorioMov = ref<RelatorioMovimentos | null>(null)

// Aportes
const analiseAportes = ref<AnaliseAportes | null>(null)
const previewAportes = ref<RelatorioGenerico | null>(null)
const relatorioAportesFinal = ref<RelatorioGenerico | null>(null)
const criarTickersNovosAportes = ref(true)

// 🆕 Proventos
const analiseProventos = ref<AnaliseProventos | null>(null)
const previewProventos = ref<RelatorioGenerico | null>(null)
const relatorioProventosFinal = ref<RelatorioGenerico | null>(null)
const criarTickersNovosProventos = ref(true)

const analisando = ref(false)
const fazendoPreview = ref(false)
const executando = ref(false)
const explorando = ref(false)
const previewMovLoading = ref(false)
const execMovLoading = ref(false)
const analiseAportesLoading = ref(false)
const previewAportesLoading = ref(false)
const execAportesLoading = ref(false)
const analiseProvLoading = ref(false)
const previewProvLoading = ref(false)
const execProvLoading = ref(false)

const dialogExplorador = ref(false)
const abaParaExplorar = ref("2026")
const opcoesAba = [
  { label: "2026", value: "2026" }, { label: "2025", value: "2025" },
  { label: "2024", value: "2024" },
]

const anosSelecionados = ref<number[]>([2024])
const blocosSelecionados = ref<string[]>([
  "receitas_despesas", "saldos_contas", "combustivel",
  "extras", "pagamentos_cartao", "saldos_investimentos"
])

const opcoesAnos = [
  { label: "2024", value: 2024 }, { label: "2025", value: 2025 }, { label: "2026", value: 2026 },
]
const opcoesBlocos = [
  { label: "💰 Receitas e Despesas", value: "receitas_despesas" },
  { label: "🏦 Saldos de Contas", value: "saldos_contas" },
  { label: "⛽ Combustível", value: "combustivel" },
  { label: "🎯 Extras detalhados", value: "extras" },
  { label: "💳 Pagamentos de Cartão", value: "pagamentos_cartao" },
  { label: "📈 Saldos de Investimentos", value: "saldos_investimentos" },
]

function selecionarArquivo(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    arquivoSelecionado.value = input.files[0]
    analise.value = null
    preview.value = null
    relatorioFinal.value = null
    exploracao.value = null
    previewMov.value = null
    relatorioMov.value = null
    analiseAportes.value = null
    previewAportes.value = null
    relatorioAportesFinal.value = null
    analiseProventos.value = null
    previewProventos.value = null
    relatorioProventosFinal.value = null
  }
}

async function analisarArquivo() {
  if (!arquivoSelecionado.value) return
  analisando.value = true
  try {
    analise.value = await importacaoService.analisar(arquivoSelecionado.value)
    toast.add({ severity: "success", summary: "Analisado", detail: `${analise.value.total_abas} abas`, life: 3000 })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { analisando.value = false }
}

async function fazerPreviewAtivos() {
  if (!arquivoSelecionado.value) return
  fazendoPreview.value = true
  try {
    preview.value = await importacaoService.previewAtivos(arquivoSelecionado.value.name)
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { fazendoPreview.value = false }
}

async function executarAtivos() {
  if (!arquivoSelecionado.value) return
  if (!confirm("Executar importacao de Ativos?")) return
  executando.value = true
  try {
    relatorioFinal.value = await importacaoService.executarAtivos(arquivoSelecionado.value.name)
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { executando.value = false }
}

async function explorarAba() {
  if (!arquivoSelecionado.value) return
  explorando.value = true
  try {
    exploracao.value = await importacaoService.explorarAba(
      abaParaExplorar.value, arquivoSelecionado.value.name)
    dialogExplorador.value = true
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { explorando.value = false }
}

async function fazerPreviewMov() {
  if (!arquivoSelecionado.value) return
  if (anosSelecionados.value.length === 0 || blocosSelecionados.value.length === 0) {
    toast.add({ severity: "warn", summary: "Selecione anos e blocos" })
    return
  }
  previewMovLoading.value = true
  try {
    previewMov.value = await importacaoService.previewMovimentos({
      nome_arquivo: arquivoSelecionado.value.name,
      anos: anosSelecionados.value, blocos: blocosSelecionados.value,
    })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { previewMovLoading.value = false }
}

async function executarMov() {
  if (!arquivoSelecionado.value || !previewMov.value) return
  if (!confirm(`Executar importacao de ${anosSelecionados.value.join(", ")}?`)) return
  execMovLoading.value = true
  try {
    relatorioMov.value = await importacaoService.executarMovimentos({
      nome_arquivo: arquivoSelecionado.value.name,
      anos: anosSelecionados.value, blocos: blocosSelecionados.value,
    })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { execMovLoading.value = false }
}

// === APORTES ===
async function analisarAportesFunc() {
  if (!arquivoSelecionado.value) return
  analiseAportesLoading.value = true
  try {
    analiseAportes.value = await importacaoService.analisarAportes(arquivoSelecionado.value.name)
    toast.add({ severity: "info", summary: "Aportes analisados",
      detail: `${analiseAportes.value.total_linhas_validas} linhas`, life: 5000 })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { analiseAportesLoading.value = false }
}

async function previewAportesFunc() {
  if (!arquivoSelecionado.value) return
  previewAportesLoading.value = true
  try {
    previewAportes.value = await importacaoService.previewAportes(arquivoSelecionado.value.name)
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { previewAportesLoading.value = false }
}

async function executarAportesFunc() {
  if (!arquivoSelecionado.value) return
  if (!confirm("Executar importacao de Aportes?")) return
  execAportesLoading.value = true
  try {
    relatorioAportesFinal.value = await importacaoService.executarAportes(
      arquivoSelecionado.value.name, criarTickersNovosAportes.value
    )
    toast.add({ severity: "success", summary: "Concluido!",
      detail: relatorioAportesFinal.value.mensagem_final, life: 6000 })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { execAportesLoading.value = false }
}

// 🆕 === PROVENTOS ===
async function analisarProventosFunc() {
  if (!arquivoSelecionado.value) return
  analiseProvLoading.value = true
  try {
    analiseProventos.value = await importacaoService.analisarProventos(arquivoSelecionado.value.name)
    toast.add({
      severity: "info",
      summary: "Proventos analisados",
      detail: `${analiseProventos.value.total_linhas_validas} linhas, R$ ${analiseProventos.value.total_brl_estimado.toFixed(2)}`,
      life: 5000
    })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally { analiseProvLoading.value = false }
}

async function previewProventosFunc() {
  if (!arquivoSelecionado.value) return
  previewProvLoading.value = true
  try {
    previewProventos.value = await importacaoService.previewProventos(arquivoSelecionado.value.name)
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message })
  } finally { previewProvLoading.value = false }
}

async function executarProventosFunc() {
  if (!arquivoSelecionado.value) return
  if (!confirm("Executar importacao de Proventos?")) return
  execProvLoading.value = true
  try {
    relatorioProventosFinal.value = await importacaoService.executarProventos(
      arquivoSelecionado.value.name, criarTickersNovosProventos.value
    )
    toast.add({
      severity: "success", summary: "Proventos importados!",
      detail: relatorioProventosFinal.value.mensagem_final, life: 8000
    })
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 6000 })
  } finally { execProvLoading.value = false }
}

function corTipo(tipo: string) {
  const cores: Record<string, string> = {
    movimentos_anuais: "info", cripto: "warning",
    ativos_br: "success", ativos_eua: "success",
    consolidacao: "info", aportes: "warning",
    proventos: "warning", desconhecida: "secondary",
  }
  return cores[tipo] || "secondary"
}

const dadosExp = computed(() => exploracao.value?.dados || {})
const bloco1 = computed(() => dadosExp.value?.bloco_1_movimentos || {})
const bloco2 = computed(() => dadosExp.value?.bloco_2_contas || {})
const bloco3 = computed(() => dadosExp.value?.bloco_3_extras || {})
const bloco4 = computed(() => dadosExp.value?.bloco_4_combustivel || {})
const bloco5 = computed(() => dadosExp.value?.bloco_5_investimentos || {})

function calcTotal(relatorio: RelatorioMovimentos | null): number {
  if (!relatorio) return 0
  let total = 0
  for (const ano of Object.values(relatorio.relatorio_por_ano)) {
    if (typeof ano === "object" && ano && !("erro" in ano)) {
      for (const bloco of Object.values(ano as any)) {
        if (typeof bloco === "object" && bloco && "inseridos" in (bloco as any)) {
          total += (bloco as any).inseridos
        }
      }
    }
  }
  return total
}

// 🆕 Lista formatada de tipos de provento
const tiposProventoFormatado = computed(() => {
  if (!analiseProventos.value) return []
  const mapaIcones: Record<string, string> = {
    dividendo: "💵 Dividendo",
    jcp: "💼 JCP",
    rendimento: "📈 Rendimento",
    juros_cripto: "₿ Juros Cripto",
    outro: "📦 Outro",
  }
  return Object.entries(analiseProventos.value.distribuicao_tipos).map(
    ([tipo, qtd]) => ({ label: mapaIcones[tipo] || tipo, qtd })
  )
})
</script>

<template>
  <PageHeader title="📥 Importacao da Planilha" subtitle="Migre os dados historicos" />

  <section class="card">
    <h3>📁 1. Selecionar arquivo</h3>
    <input type="file" accept=".xlsx" @change="selecionarArquivo" class="file-input" />
    <div v-if="arquivoSelecionado" class="arquivo-info">
      ✅ <strong>{{ arquivoSelecionado.name }}</strong>
    </div>
    <div class="acoes">
      <Button label="🔍 Analisar abas" :disabled="!arquivoSelecionado || analisando"
              :loading="analisando" @click="analisarArquivo" />
    </div>
  </section>

  <section v-if="analise" class="card">
    <h3>🔍 Abas detectadas</h3>
    <DataTable :value="analise.abas" stripedRows :paginator="false">
      <Column field="nome" header="Aba" />
      <Column header="Tipo">
        <template #body="{ data }">
          <Tag :value="data.tipo_detectado" :severity="corTipo(data.tipo_detectado) as any" />
        </template>
      </Column>
    </DataTable>
  </section>

  <section v-if="analise" class="card">
    <h3>📊 Importacao de Ativos</h3>
    <div class="acoes">
      <Button label="🔍 Preview" :loading="fazendoPreview" @click="fazerPreviewAtivos" />
      <Button v-if="preview" label="✅ Executar" severity="success"
              :loading="executando" @click="executarAtivos" />
    </div>
    <Message v-if="preview" severity="info" :closable="false">{{ preview.mensagem_final }}</Message>
    <Message v-if="relatorioFinal" severity="success" :closable="false">✅ {{ relatorioFinal.mensagem_final }}</Message>
  </section>

  <section v-if="analise" class="card destaque-explorador">
    <h3>🔬 Modo Explorador</h3>
    <div class="form-explorador">
      <Dropdown v-model="abaParaExplorar" :options="opcoesAba" optionLabel="label" optionValue="value" />
      <Button label="🔬 Explorar" :loading="explorando" @click="explorarAba" />
    </div>
  </section>

  <section v-if="analise" class="card destaque-movimentos">
    <h3>🚀 Importar Movimentacoes Mensais</h3>
    <div class="form-mov">
      <div class="grupo-checkbox">
        <h5>📅 Anos</h5>
        <div class="lista-check">
          <div v-for="op in opcoesAnos" :key="op.value" class="check-item">
            <Checkbox v-model="anosSelecionados" :value="op.value" :inputId="`a${op.value}`" />
            <label :for="`a${op.value}`">{{ op.label }}</label>
          </div>
        </div>
      </div>
      <div class="grupo-checkbox">
        <h5>📦 Blocos</h5>
        <div class="lista-check">
          <div v-for="op in opcoesBlocos" :key="op.value" class="check-item">
            <Checkbox v-model="blocosSelecionados" :value="op.value" :inputId="`b${op.value}`" />
            <label :for="`b${op.value}`">{{ op.label }}</label>
          </div>
        </div>
      </div>
    </div>
    <div class="acoes">
      <Button label="🔍 Preview" :loading="previewMovLoading" @click="fazerPreviewMov"
              :disabled="anosSelecionados.length === 0 || blocosSelecionados.length === 0" />
      <Button v-if="previewMov" label="✅ Executar" severity="success"
              :loading="execMovLoading" @click="executarMov" />
    </div>
    <div v-if="previewMov" class="bloco-resultado">
      <Message severity="info" :closable="false">{{ previewMov.mensagem_final }}</Message>
    </div>
    <div v-if="relatorioMov" class="bloco-resultado">
      <Message severity="success" :closable="false">✅ {{ relatorioMov.mensagem_final }}</Message>
    </div>
  </section>

  <!-- APORTES -->
  <section v-if="analise" class="card destaque-aportes">
    <h3>💎 Importar Aportes</h3>
    <div class="acoes">
      <Button label="📊 Analisar aba Aportes"
              :loading="analiseAportesLoading" @click="analisarAportesFunc" />
    </div>
    <div v-if="analiseAportes" class="bloco-resultado">
      <div class="kpis">
        <div class="kpi-card success">
          <span class="kpi-label">Linhas validas</span>
          <span class="kpi-valor">{{ analiseAportes.total_linhas_validas }}</span>
        </div>
        <div class="kpi-card secondary">
          <span class="kpi-label">Compras</span>
          <span class="kpi-valor">{{ analiseAportes.compras }}</span>
        </div>
        <div class="kpi-card warning">
          <span class="kpi-label">Vendas</span>
          <span class="kpi-valor">{{ analiseAportes.vendas }}</span>
        </div>
      </div>

      <h4>✅ Tickers existentes ({{ analiseAportes.tickers_existentes.length }})</h4>
      <div class="tags-lista">
        <Tag v-for="t in analiseAportes.tickers_existentes" :key="t.ticker"
             :value="t.ticker" severity="success" />
      </div>

      <h4>🆕 Tickers novos ({{ analiseAportes.tickers_novos.length }})</h4>
      <DataTable v-if="analiseAportes.tickers_novos.length > 0"
                 :value="analiseAportes.tickers_novos" stripedRows>
        <Column field="ticker" header="Ticker" />
        <Column field="geografia" header="Geografia" />
        <Column field="classe" header="Classe" />
      </DataTable>

      <div class="opcoes-aportes">
        <Checkbox v-model="criarTickersNovosAportes" :binary="true" inputId="criar-novos-ap" />
        <label for="criar-novos-ap">☑️ Criar tickers novos automaticamente</label>
      </div>

      <div class="acoes">
        <Button label="🔍 Preview" :loading="previewAportesLoading" @click="previewAportesFunc" />
        <Button v-if="previewAportes" label="✅ Executar"
                severity="success" :loading="execAportesLoading" @click="executarAportesFunc" />
      </div>
    </div>
    <Message v-if="previewAportes" severity="info" :closable="false">{{ previewAportes.mensagem_final }}</Message>
    <div v-if="relatorioAportesFinal" class="bloco-resultado">
      <Message severity="success" :closable="false">✅ {{ relatorioAportesFinal.mensagem_final }}</Message>
    </div>
  </section>

  <!-- 🆕 PROVENTOS -->
  <section v-if="analise" class="card destaque-proventos">
    <h3>💰 Importar Proventos</h3>
    <p class="hint">
      Importa proventos (dividendos, JCPs, rendimentos) da aba 'Proventos'.
      Para USD: usa cotacao implicita da planilha (Total Convertido ÷ Total).
    </p>

    <div class="acoes">
      <Button label="📊 Analisar aba Proventos"
              :loading="analiseProvLoading" @click="analisarProventosFunc" />
    </div>

    <div v-if="analiseProventos" class="bloco-resultado">
      <h4>📊 Resumo</h4>
      <div class="kpis">
        <div class="kpi-card success">
          <span class="kpi-label">Linhas validas</span>
          <span class="kpi-valor">{{ analiseProventos.total_linhas_validas }}</span>
        </div>
        <div class="kpi-card warning">
          <span class="kpi-label">Total estimado (BRL)</span>
          <span class="kpi-valor">R$ {{ analiseProventos.total_brl_estimado.toLocaleString("pt-BR", { minimumFractionDigits: 2 }) }}</span>
        </div>
      </div>

      <h4>📋 Distribuicao por tipo</h4>
      <div class="tags-lista">
        <Tag v-for="t in tiposProventoFormatado" :key="t.label"
             :value="`${t.label}: ${t.qtd}`" severity="info" />
      </div>

      <h4>✅ Tickers existentes ({{ analiseProventos.tickers_existentes.length }})</h4>
      <div class="tags-lista">
        <Tag v-for="t in analiseProventos.tickers_existentes" :key="t.ticker"
             :value="t.ticker" severity="success" />
      </div>

      <h4>🆕 Tickers novos ({{ analiseProventos.tickers_novos.length }})</h4>
      <Message v-if="analiseProventos.tickers_novos.length > 0" severity="warn" :closable="false">
        ⚠️ Estes tickers nao existem ainda. Serao criados automaticamente se voce marcar a opcao abaixo.
      </Message>
      <DataTable v-if="analiseProventos.tickers_novos.length > 0"
                 :value="analiseProventos.tickers_novos" stripedRows>
        <Column field="ticker" header="Ticker" />
        <Column field="pais_planilha" header="Pais (planilha)" />
        <Column field="geografia" header="Geografia inferida" />
        <Column field="classe" header="Classe inferida" />
      </DataTable>

      <div class="opcoes-aportes">
        <Checkbox v-model="criarTickersNovosProventos" :binary="true" inputId="criar-novos-prov" />
        <label for="criar-novos-prov">
          ☑️ Criar automaticamente os tickers novos durante a importacao
        </label>
      </div>

      <div class="acoes">
        <Button label="🔍 Preview" :loading="previewProvLoading" @click="previewProventosFunc" />
        <Button v-if="previewProventos" label="✅ Executar Proventos"
                severity="success" :loading="execProvLoading"
                @click="executarProventosFunc" />
      </div>
    </div>

    <Message v-if="previewProventos" severity="info" :closable="false">{{ previewProventos.mensagem_final }}</Message>

    <div v-if="relatorioProventosFinal" class="bloco-resultado">
      <Message severity="success" :closable="false">
        ✅ {{ relatorioProventosFinal.mensagem_final }}
      </Message>
      <div v-if="relatorioProventosFinal.backup_seguranca" class="backup-info">
        🛡️ Backup: <strong>{{ relatorioProventosFinal.backup_seguranca }}</strong>
      </div>
      <details class="detalhes">
        <summary>Detalhes da importacao</summary>
        <pre class="json-box">{{ relatorioProventosFinal.resultado }}</pre>
      </details>
      <Message severity="info" :closable="false" class="proximo-passo">
        💡 Va em <strong>Lancamentos → Proventos</strong> para conferir!
        E em <strong>Posicao Atual</strong>, a coluna YoC e Proventos ja estarao preenchidas.
      </Message>
    </div>
  </section>

  <!-- DIALOG EXPLORADOR -->
  <Dialog v-model:visible="dialogExplorador"
          :header="`🔬 Exploracao da aba ${exploracao?.aba || ''}`"
          modal :style="{ width: '95vw', maxWidth: '1200px', height: '90vh' }"
          :contentStyle="{ overflow: 'auto' }">
    <div v-if="exploracao">
      <h4>📅 Mapeamento de meses</h4>
      <pre class="json-box">{{ dadosExp.mapeamento_meses }}</pre>
      <h4>📋 Bloco 1 — Movimentacoes</h4>
      <DataTable v-if="bloco1.categorias_encontradas?.length"
                 :value="bloco1.categorias_encontradas" stripedRows>
        <Column field="categoria" header="Categoria" />
        <Column header="Tipo">
          <template #body="{ data }">
            <Tag :value="data.tipo" :severity="data.tipo === 'receita' ? 'success' : data.tipo === 'despesa' ? 'danger' : 'warning'" />
          </template>
        </Column>
      </DataTable>
      <h4>💰 Bloco 2 — Contas</h4>
      <DataTable v-if="bloco2.contas_encontradas?.length"
                 :value="bloco2.contas_encontradas" stripedRows>
        <Column field="conta" header="Conta" />
      </DataTable>
      <h4>⛽ Bloco 4 — Combustivel</h4>
      <pre class="json-box">{{ bloco4.dias_e_valores }}</pre>
      <h4>📈 Bloco 5 — Investimentos</h4>
      <DataTable v-if="bloco5.categorias_encontradas?.length"
                 :value="bloco5.categorias_encontradas" stripedRows>
        <Column field="categoria" header="Categoria" />
      </DataTable>
    </div>
    <template #footer>
      <Button label="Fechar" @click="dialogExplorador = false" />
    </template>
  </Dialog>
</template>

<style scoped>
.card { background: var(--bg-surface); border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg); padding: var(--space-5); margin-bottom: var(--space-4); }
.card.destaque-explorador { border-left: 4px solid var(--brand-accent); }
.card.destaque-movimentos { border-left: 4px solid var(--success); }
.card.destaque-aportes { border-left: 4px solid var(--info); }
.card.destaque-proventos { border-left: 4px solid var(--brand-secondary); }
.card h3 { margin-bottom: var(--space-3); }
.card h4 { margin: var(--space-4) 0 var(--space-2); color: var(--text-secondary); }
.card h5 { margin-bottom: var(--space-2); font-size: var(--text-sm); }
.file-input { display: block; padding: var(--space-3); background: var(--bg-elevated);
              border: 1px solid var(--border-default); border-radius: var(--radius-md);
              color: var(--text-primary); width: 100%; margin-bottom: var(--space-3); }
.arquivo-info { padding: var(--space-3); background: var(--bg-elevated);
                border-radius: var(--radius-md); font-size: var(--text-sm); }
.acoes { display: flex; gap: var(--space-3); margin-top: var(--space-4); flex-wrap: wrap; }
.hint { font-size: var(--text-sm); color: var(--text-muted); margin-bottom: var(--space-3); }
.form-explorador { display: flex; gap: var(--space-3); align-items: center; margin-top: var(--space-3); }
.form-mov { display: grid; grid-template-columns: 1fr 2fr; gap: var(--space-5); margin: var(--space-4) 0; }
.grupo-checkbox { background: var(--bg-elevated); padding: var(--space-4); border-radius: var(--radius-md); }
.lista-check { display: flex; flex-direction: column; gap: var(--space-2); }
.check-item { display: flex; align-items: center; gap: var(--space-2); }
.check-item label { cursor: pointer; font-size: var(--text-sm); }
.bloco-resultado { margin: var(--space-4) 0; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--space-3); margin: var(--space-3) 0; }
.kpi-card { background: var(--bg-elevated); padding: var(--space-4); border-radius: var(--radius-md); text-align: center; }
.kpi-card.success { border-left: 3px solid var(--success); }
.kpi-card.warning { border-left: 3px solid var(--warning); }
.kpi-card.secondary { border-left: 3px solid var(--text-muted); }
.kpi-label { display: block; font-size: var(--text-xs); color: var(--text-muted); text-transform: uppercase; margin-bottom: var(--space-2); }
.kpi-valor { display: block; font-size: var(--text-xl); font-weight: 700; }
.tags-lista { display: flex; flex-wrap: wrap; gap: var(--space-2); margin: var(--space-2) 0; }
.opcoes-aportes { display: flex; align-items: center; gap: var(--space-2);
                  margin: var(--space-3) 0; padding: var(--space-3);
                  background: var(--bg-elevated); border-radius: var(--radius-md); }
.detalhes { margin-top: var(--space-3); padding: var(--space-3);
            background: var(--bg-elevated); border-radius: var(--radius-md); }
.detalhes summary { cursor: pointer; font-weight: 500; }
.json-box { background: var(--bg-base); padding: var(--space-3); border-radius: var(--radius-md);
            font-family: ui-monospace, monospace; font-size: var(--text-xs);
            white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow-y: auto; }
.backup-info { padding: var(--space-3); background: var(--bg-elevated);
               border-radius: var(--radius-md); font-size: var(--text-sm);
               border-left: 3px solid var(--brand-accent); margin: var(--space-3) 0; }
.proximo-passo { margin-top: var(--space-4); }
</style>
<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  posicoesEUAService, type PosicaoEUA
} from "@/services/posicoesEUA"
import { ativosService, type Ativo } from "@/services/ativos"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref<PosicaoEUA[]>([])
const ativos = ref<Ativo[]>([])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<PosicaoEUA>>({})
const sugestao = ref<{ qtd: number; preco_medio: number } | null>(null)

const ativosEUA = computed(() => ativos.value.filter(a => a.geografia === "EUA"))

const mapAtivo = computed(() => {
  const m = new Map<number, Ativo>()
  ativos.value.forEach(a => m.set(a.id, a))
  return m
})

const totais = computed(() => ({
  brl: lista.value.reduce((a, p) => a + Number(p.valor_total_brl), 0),
  usd: lista.value.reduce((a, p) => a + Number(p.valor_total_usd), 0),
}))

const classeColor = (c: string) => ({
  acao: "#F97316",
  etf: "#FB923C",
  reit: "#EC4899",
} as any)[c] || "#888"

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)
const fmtUSD = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v || 0)

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [pos, ats] = await Promise.all([
      posicoesEUAService.listar(periodo.anoIdSelecionado, periodo.mesSelecionado),
      ativos.value.length ? Promise.resolve(ativos.value) : ativosService.listar({ apenas_ativos: true }),
    ])
    lista.value = pos
    if (!ativos.value.length) ativos.value = ats
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })

async function buscarSugestao() {
  if (!form.value.ativo_id || !periodo.anoIdSelecionado) return
  try {
    const r = await posicoesEUAService.precoMedioSugerido(
      form.value.ativo_id, periodo.anoIdSelecionado, periodo.mesSelecionado
    )
    sugestao.value = { qtd: r.quantidade_acumulada, preco_medio: r.preco_medio_sugerido }
  } catch {
    sugestao.value = null
  }
}

function aplicarSugestao() {
  if (!sugestao.value) return
  form.value.quantidade = sugestao.value.qtd
  form.value.preco_medio_usd = sugestao.value.preco_medio
  toast.add({ severity: "info", summary: "Sugestão aplicada", life: 2500 })
}

watch(() => form.value.ativo_id, () => {
  if (form.value.ativo_id) buscarSugestao()
})

function abrirNovo() {
  editando.value = null
  sugestao.value = null
  form.value = {
    ano_id: periodo.anoIdSelecionado!,
    mes: periodo.mesSelecionado,
    ativo_id: ativosEUA.value[0]?.id,
    quantidade: 0,
    preco_medio_usd: 0,
    cotacao_fechamento_usd: 0,
    cotacao_usd_brl: undefined,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: PosicaoEUA) {
  editando.value = row.id
  sugestao.value = null
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value)
      await posicoesEUAService.atualizar(editando.value, form.value)
    else
      await posicoesEUAService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: PosicaoEUA) {
  if (!confirm(`Remover posição de ${mapAtivo.value.get(row.ativo_id)?.ticker}?`)) return
  try {
    await posicoesEUAService.excluir(row.id)
    toast.add({ severity: "info", summary: "Removido", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function replicar() {
  if (!confirm(`Replicar posições do mês anterior para ${periodo.labelPeriodo}?`)) return
  try {
    const r = await posicoesEUAService.replicarMesAnterior(
      periodo.anoIdSelecionado!, periodo.mesSelecionado
    )
    toast.add({ severity: "success", summary: "Replicado", detail: r.mensagem, life: 4000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}
</script>

<template>
  <PageHeader title="🇺🇸 Posições de Ativos dos EUA"
              :subtitle="`Ações, ETFs, REITs - ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="🔁 Replicar mês anterior" outlined @click="replicar" />
      <Button label="Nova posição" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows sortMode="single">
    <Column header="Ativo" sortable sortField="ticker">
      <template #body="{ data }">
        <span class="ativo-tag">
          <strong>{{ mapAtivo.get(data.ativo_id)?.ticker || "—" }}</strong>
          <span class="nome-ativo">{{ mapAtivo.get(data.ativo_id)?.nome }}</span>
        </span>
      </template>
    </Column>
    <Column header="Classe">
      <template #body="{ data }">
        <Tag :value="mapAtivo.get(data.ativo_id)?.classe?.toUpperCase()"
             :style="{ background: classeColor(mapAtivo.get(data.ativo_id)?.classe || ''), color: 'white' }" />
      </template>
    </Column>
    <Column header="Quantidade" sortable sortField="quantidade" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ Number(data.quantidade).toLocaleString("en-US") }}</span>
      </template>
    </Column>
    <Column header="Preço médio (USD)" sortable sortField="preco_medio" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">{{ fmtUSD(data.preco_medio_usd) }}</span>
      </template>
    </Column>
    <Column header="Cotação fech. (USD)" sortable sortField="cotacao_fechamento" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ fmtUSD(data.cotacao_fechamento_usd) }}</span>
      </template>
    </Column>
    <Column header="Valor USD" sortable sortField="valor_total" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">{{ fmtUSD(data.valor_total_usd) }}</span>
      </template>
    </Column>
    <Column header="Valor BRL" style="text-align: right">
      <template #body="{ data }">
        <strong class="tabular">{{ fmtBRL(data.valor_total_brl) }}</strong>
      </template>
    </Column>
    <Column header="Cotação USD/BRL">
      <template #body="{ data }">
        <span class="tabular value-muted">R$ {{ Number(data.cotacao_usd_brl).toFixed(4) }}</span>
      </template>
    </Column>
    <Column header="Ações" style="width: 7rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-resumo">
        <div><span class="lbl">Total USD:</span>
          <strong class="tabular value-muted">{{ fmtUSD(totais.usd) }}</strong>
        </div>
        <div><span class="lbl">Total BRL:</span>
          <strong class="tabular">{{ fmtBRL(totais.brl) }}</strong>
        </div>
        <div><span class="lbl">Ativos:</span> <strong>{{ lista.length }}</strong></div>
      </div>
    </template>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel"
          :header="editando ? 'Editar posição' : 'Nova posição'"
          modal :style="{ width: '540px' }">
    <div class="form">
      <label>Ativo</label>
      <Dropdown v-model="form.ativo_id" :options="ativosEUA"
                optionLabel="ticker" optionValue="id"
                :filter="true" filterPlaceholder="Buscar..."
                placeholder="Selecione..." />

      <div v-if="sugestao && sugestao.preco_medio > 0" class="sugestao-card">
        <div class="sug-header">
          <span>💡 <strong>Sugestão com base nos aportes USD</strong></span>
          <Button label="Aplicar" size="small" outlined @click="aplicarSugestao" />
        </div>
        <div class="sug-detalhes">
          <span>Quantidade: <strong>{{ sugestao.qtd.toLocaleString("en-US") }}</strong></span>
          <span>Preço médio: <strong>{{ fmtUSD(sugestao.preco_medio) }}</strong></span>
        </div>
      </div>

      <label>Quantidade</label>
      <InputNumber v-model="form.quantidade"
                   :minFractionDigits="0" :maxFractionDigits="8"
                   :min="0" locale="en-US" />

      <label>Preço médio (USD)</label>
      <InputNumber v-model="form.preco_medio_usd"
                   mode="currency" currency="USD" locale="en-US" />

      <label>Cotação de fechamento (USD)</label>
      <InputNumber v-model="form.cotacao_fechamento_usd"
                   mode="currency" currency="USD" locale="en-US" />

      <label>Cotação USD/BRL (opcional)</label>
      <InputNumber v-model="form.cotacao_usd_brl"
                   :minFractionDigits="4" :maxFractionDigits="4"
                   :min="0" locale="pt-BR"
                   placeholder="Deixe vazio para buscar no BCB" />
      <small class="hint">💡 Se vazio, busca cotação automaticamente no BCB</small>
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogVisivel = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvar" />
    </template>
  </Dialog>
</template>

<style scoped>
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
.hint { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
.ativo-tag { display: inline-flex; align-items: center; gap: 8px; }
.nome-ativo { color: var(--text-muted); font-size: var(--text-sm); }
.footer-resumo {
  display: flex; justify-content: flex-end; gap: var(--space-6);
  padding: var(--space-2) 0; font-size: var(--text-sm);
}
.footer-resumo .lbl { color: var(--text-muted); margin-right: 6px; }
.sugestao-card {
  background: var(--bg-elevated); border: 1px solid var(--border-default);
  border-left: 3px solid var(--brand-accent);
  border-radius: var(--radius-md); padding: var(--space-3);
  margin: var(--space-2) 0;
}
.sug-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-2);
}
.sug-detalhes {
  display: flex; gap: var(--space-4); font-size: var(--text-sm);
  color: var(--text-secondary);
}
</style>
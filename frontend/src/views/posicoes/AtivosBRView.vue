<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  posicoesBRService, type PosicaoBR
} from "@/services/posicoesBR"
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

const lista = ref<PosicaoBR[]>([])
const ativos = ref<Ativo[]>([])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<PosicaoBR>>({})
const sugestaoLoading = ref(false)
const sugestao = ref<{ qtd: number; preco_medio: number } | null>(null)

const ativosBR = computed(() =>
  ativos.value.filter(a => a.geografia === "BR" && a.classe !== "cripto")
)

const mapAtivo = computed(() => {
  const m = new Map<number, Ativo>()
  ativos.value.forEach(a => m.set(a.id, a))
  return m
})

const totalBRL = computed(() =>
  lista.value.reduce((acc, p) => acc + Number(p.valor_total), 0)
)

const classeColor = (c: string) => ({
  acao: "#10B981",
  etf: "#22C55E",
  fii: "#84CC16",
  fiagro: "#EAB308",
} as any)[c] || "#888"

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [pos, ats] = await Promise.all([
      posicoesBRService.listar(periodo.anoIdSelecionado, periodo.mesSelecionado),
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

async function buscarSugestaoPrecoMedio() {
  if (!form.value.ativo_id || !periodo.anoIdSelecionado) return
  sugestaoLoading.value = true
  try {
    const r = await posicoesBRService.precoMedioSugerido(
      form.value.ativo_id, periodo.anoIdSelecionado, periodo.mesSelecionado
    )
    sugestao.value = {
      qtd: r.quantidade_acumulada,
      preco_medio: r.preco_medio_sugerido,
    }
  } catch (e: any) {
    sugestao.value = null
  } finally {
    sugestaoLoading.value = false
  }
}

function aplicarSugestao() {
  if (!sugestao.value) return
  form.value.quantidade = sugestao.value.qtd
  form.value.preco_medio = sugestao.value.preco_medio
  toast.add({ severity: "info", summary: "Sugestão aplicada", life: 2500 })
}

watch(() => form.value.ativo_id, () => {
  if (form.value.ativo_id) buscarSugestaoPrecoMedio()
})

function abrirNovo() {
  editando.value = null
  sugestao.value = null
  form.value = {
    ano_id: periodo.anoIdSelecionado!,
    mes: periodo.mesSelecionado,
    ativo_id: ativosBR.value[0]?.id,
    quantidade: 0,
    preco_medio: 0,
    cotacao_fechamento: 0,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: PosicaoBR) {
  editando.value = row.id
  sugestao.value = null
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value)
      await posicoesBRService.atualizar(editando.value, form.value)
    else
      await posicoesBRService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: PosicaoBR) {
  if (!confirm(`Remover posição de ${mapAtivo.value.get(row.ativo_id)?.ticker}?`)) return
  try {
    await posicoesBRService.excluir(row.id)
    toast.add({ severity: "info", summary: "Removido", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function replicar() {
  if (!confirm(`Replicar posições do mês anterior para ${periodo.labelPeriodo}?`)) return
  try {
    const r = await posicoesBRService.replicarMesAnterior(
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
  <PageHeader title="🇧🇷 Posições de Ativos Nacionais (B3)"
              :subtitle="`Ações, ETFs, FIIs, Fiagro - ${periodo.labelPeriodo}`">
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
        <span class="tabular">{{ Number(data.quantidade).toLocaleString("pt-BR") }}</span>
      </template>
    </Column>
    <Column header="Preço médio" sortable sortField="preco_medio" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">{{ fmtBRL(data.preco_medio) }}</span>
      </template>
    </Column>
    <Column header="Cotação fechamento" sortable sortField="cotacao_fechamento" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ fmtBRL(data.cotacao_fechamento) }}</span>
      </template>
    </Column>
    <Column header="Valor total" sortable sortField="valor_total" style="text-align: right">
      <template #body="{ data }">
        <strong class="tabular">{{ fmtBRL(data.valor_total) }}</strong>
      </template>
    </Column>
    <Column header="Ações" style="width: 7rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total BR: <strong class="tabular">{{ fmtBRL(totalBRL) }}</strong>
        ({{ lista.length }} ativos)
      </div>
    </template>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel"
          :header="editando ? 'Editar posição' : 'Nova posição'"
          modal :style="{ width: '520px' }">
    <div class="form">
      <label>Ativo</label>
      <Dropdown v-model="form.ativo_id" :options="ativosBR"
                optionLabel="ticker" optionValue="id"
                :filter="true" filterPlaceholder="Buscar..."
                placeholder="Selecione..." />

      <!-- Sugestão de preço médio -->
      <div v-if="sugestao && sugestao.preco_medio > 0" class="sugestao-card">
        <div class="sug-header">
          <span>💡 <strong>Sugestão com base nos aportes</strong></span>
          <Button label="Aplicar" size="small" outlined @click="aplicarSugestao" />
        </div>
        <div class="sug-detalhes">
          <span>Quantidade: <strong>{{ sugestao.qtd.toLocaleString("pt-BR") }}</strong></span>
          <span>Preço médio: <strong>{{ fmtBRL(sugestao.preco_medio) }}</strong></span>
        </div>
      </div>

      <label>Quantidade</label>
      <InputNumber v-model="form.quantidade"
                   :minFractionDigits="0" :maxFractionDigits="8"
                   :min="0" locale="pt-BR" />

      <label>Preço médio (BRL)</label>
      <InputNumber v-model="form.preco_medio"
                   mode="currency" currency="BRL" locale="pt-BR" />

      <label>Cotação de fechamento (BRL)</label>
      <InputNumber v-model="form.cotacao_fechamento"
                   mode="currency" currency="BRL" locale="pt-BR" />
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
.ativo-tag { display: inline-flex; align-items: center; gap: 8px; }
.nome-ativo { color: var(--text-muted); font-size: var(--text-sm); }
.footer-total { text-align: right; font-size: var(--text-base); padding: var(--space-2) 0; }
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
<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { ativosService, type Ativo } from "@/services/ativos"
import { http } from "@/services/http"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"
import FiltroStatus from "@/components/FiltroStatus.vue"

const toast = useToast()
const lista = ref<Ativo[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Ativo>>({})
const filtroStatus = ref<"ativos" | "inativos" | "todos">("ativos")

const tipos = [
  { label: "Ação BR", value: "acao_br" }, { label: "BDR", value: "bdr" },
  { label: "FII", value: "fii" }, { label: "Fiagro", value: "fiagro" },
  { label: "ETF BR", value: "etf_br" }, { label: "Ação EUA", value: "acao_eua" },
  { label: "ETF EUA", value: "etf_eua" }, { label: "REIT", value: "reit" },
  { label: "Cripto", value: "cripto" },
]
const mercados = ["B3", "NYSE", "NASDAQ", "CRIPTO"].map(v => ({ label: v, value: v }))
const geografias = ["BR", "EUA", "GLOBAL"].map(v => ({ label: v, value: v }))
const classes = ["acao", "etf", "fii", "fiagro", "reit", "cripto"].map(v => ({ label: v, value: v }))
const moedas = ["BRL", "USD"].map(v => ({ label: v, value: v }))

const listaFiltrada = computed(() => {
  if (filtroStatus.value === "todos") return lista.value
  if (filtroStatus.value === "ativos") return lista.value.filter(a => a.ativo === 1)
  return lista.value.filter(a => a.ativo === 0)
})

async function carregar() {
  carregando.value = true
  try { lista.value = await ativosService.listar() }
  catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { ticker: "", nome: "", tipo: "acao_br", mercado: "B3",
                 geografia: "BR", classe: "acao", moeda: "BRL", setor: "" }
  dialogVisivel.value = true
}

function abrirEdicao(row: Ativo) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await ativosService.atualizar(editando.value, form.value)
    else await ativosService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: Ativo) {
  if (!confirm(`Inativar ${row.ticker}?`)) return
  try { await ativosService.inativar(row.id); await carregar() }
  catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

async function reativar(row: Ativo) {
  try {
    await http.post(`/ativos/${row.id}/reativar`)
    toast.add({ severity: "success", summary: `${row.ticker} reativado`, life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Ativos Financeiros" subtitle="Cadastro M08">
    <template #actions>
      <Button label="Novo Ativo" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <div class="filtros">
    <FiltroStatus v-model="filtroStatus" />
  </div>

  <DataTable :value="listaFiltrada" :loading="carregando" stripedRows :paginator="true" :rows="25">
    <Column field="ticker" header="Ticker" sortable />
    <Column field="nome" header="Nome" sortable />
    <Column field="tipo" header="Tipo" sortable />
    <Column field="mercado" header="Mercado" sortable />
    <Column field="geografia" header="Geografia" sortable />
    <Column field="classe" header="Classe" sortable />
    <Column field="moeda" header="Moeda" sortable />
    <Column header="Status" sortable sortField="ativo">
      <template #body="{ data }">
        <Tag :severity="data.ativo ? 'success' : 'secondary'"
             :value="data.ativo ? 'Ativo' : 'Inativo'" />
      </template>
    </Column>
    <Column header="Ações" style="width: 10rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button v-if="!data.ativo" icon="pi pi-check-circle" severity="success" text
                v-tooltip="'Reativar'" @click="reativar(data)" />
        <Button v-else icon="pi pi-trash" severity="danger" text
                v-tooltip="'Inativar'" @click="inativar(data)" />
      </template>
    </Column>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Ativo' : 'Novo Ativo'"
          modal :style="{ width: '500px' }">
    <div class="form">
      <label>Ticker</label>
      <InputText v-model="form.ticker" />
      <label>Nome</label>
      <InputText v-model="form.nome" />
      <label>Tipo</label>
      <Dropdown v-model="form.tipo" :options="tipos" optionLabel="label" optionValue="value" />
      <label>Mercado</label>
      <Dropdown v-model="form.mercado" :options="mercados" optionLabel="label" optionValue="value" />
      <label>Geografia</label>
      <Dropdown v-model="form.geografia" :options="geografias" optionLabel="label" optionValue="value" />
      <label>Classe</label>
      <Dropdown v-model="form.classe" :options="classes" optionLabel="label" optionValue="value" />
      <label>Moeda</label>
      <Dropdown v-model="form.moeda" :options="moedas" optionLabel="label" optionValue="value" />
      <label>Setor (opcional)</label>
      <InputText v-model="form.setor" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogVisivel = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvar" />
    </template>
  </Dialog>
</template>

<style scoped>
.filtros { display: flex; gap: var(--space-4); margin-bottom: var(--space-4); }
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
</style>
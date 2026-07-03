<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { instituicoesService, type Instituicao } from "@/services/instituicoes"
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
const lista = ref<Instituicao[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Instituicao>>({})
const filtroStatus = ref<"ativos" | "inativos" | "todos">("ativos")

const tipos = [
  { label: "Banco", value: "banco" }, { label: "Corretora", value: "corretora" },
  { label: "Exchange", value: "exchange" }, { label: "Outro", value: "outro" }
]
const paises = [
  { label: "Brasil (BR)", value: "BR" }, { label: "Estados Unidos (US)", value: "US" }
]

const listaFiltrada = computed(() => {
  if (filtroStatus.value === "todos") return lista.value
  if (filtroStatus.value === "ativos") return lista.value.filter(i => i.ativo === 1)
  return lista.value.filter(i => i.ativo === 0)
})

async function carregar() {
  carregando.value = true
  try { lista.value = await instituicoesService.listar() }
  catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { nome: "", tipo: "banco", pais: "BR" }
  dialogVisivel.value = true
}

function abrirEdicao(row: Instituicao) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await instituicoesService.atualizar(editando.value, form.value)
    else await instituicoesService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: Instituicao) {
  if (!confirm(`Inativar a instituição "${row.nome}"?`)) return
  try { await instituicoesService.inativar(row.id); await carregar() }
  catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

async function reativar(row: Instituicao) {
  try {
    await http.post(`/instituicoes/${row.id}/reativar`)
    toast.add({ severity: "success", summary: `${row.nome} reativada`, life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Instituições Financeiras" subtitle="Cadastro M04">
    <template #actions>
      <Button label="Nova Instituição" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <div class="filtros">
    <FiltroStatus v-model="filtroStatus" />
  </div>

  <DataTable :value="listaFiltrada" :loading="carregando" stripedRows>
    <Column field="nome" header="Nome" sortable />
    <Column field="tipo" header="Tipo" sortable />
    <Column field="pais" header="País" sortable />
    <Column header="Status" sortable sortField="ativo">
      <template #body="{ data }">
        <Tag :severity="data.ativo ? 'success' : 'secondary'"
             :value="data.ativo ? 'Ativa' : 'Inativa'" />
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

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Instituição' : 'Nova Instituição'"
          modal :style="{ width: '460px' }">
    <div class="form">
      <label>Nome</label>
      <InputText v-model="form.nome" />
      <label>Tipo</label>
      <Dropdown v-model="form.tipo" :options="tipos" optionLabel="label" optionValue="value" />
      <label>País</label>
      <Dropdown v-model="form.pais" :options="paises" optionLabel="label" optionValue="value" />
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
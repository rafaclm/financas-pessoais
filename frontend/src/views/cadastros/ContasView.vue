<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { contasService, type Conta } from "@/services/contas"
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
const lista = ref<Conta[]>([])
const instituicoes = ref<Instituicao[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Conta>>({})
const filtroStatus = ref<"ativos" | "inativos" | "todos">("ativos")

const tipos = [
  { label: "Conta Corrente", value: "corrente" },
  { label: "Investimento", value: "investimento" },
  { label: "Internacional", value: "internacional" },
  { label: "Outro", value: "outro" }
]
const moedas = [{ label: "BRL", value: "BRL" }, { label: "USD", value: "USD" }]

const listaFiltrada = computed(() => {
  if (filtroStatus.value === "todos") return lista.value
  if (filtroStatus.value === "ativos") return lista.value.filter(c => c.ativo === 1)
  return lista.value.filter(c => c.ativo === 0)
})

const mapInst = computed(() => {
  const m = new Map<number, string>()
  instituicoes.value.forEach(i => m.set(i.id, i.nome))
  return m
})

async function carregar() {
  carregando.value = true
  try {
    const [contas, insts] = await Promise.all([
      contasService.listar(false),
      instituicoesService.listar(false)
    ])
    lista.value = contas
    instituicoes.value = insts
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { nome: "", instituicao_id: undefined, tipo: "corrente", moeda: "BRL" }
  dialogVisivel.value = true
}

function abrirEdicao(row: Conta) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await contasService.atualizar(editando.value, form.value)
    else await contasService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: Conta) {
  if (!confirm(`Inativar a conta "${row.nome}"?`)) return
  try {
    await contasService.inativar(row.id)
    toast.add({ severity: "info", summary: "Inativada", life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

async function reativar(row: Conta) {
  try {
    await http.post(`/contas/${row.id}/reativar`)
    toast.add({ severity: "success", summary: `${row.nome} reativada`, life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Contas Correntes" subtitle="Cadastro M05">
    <template #actions>
      <Button label="Nova Conta" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <div class="filtros">
    <FiltroStatus v-model="filtroStatus" />
  </div>

  <DataTable :value="listaFiltrada" :loading="carregando" stripedRows>
    <Column field="nome" header="Nome" sortable />
    <Column header="Instituição" sortable sortField="instituicao_id">
      <template #body="{ data }">{{ mapInst.get(data.instituicao_id) || "—" }}</template>
    </Column>
    <Column field="tipo" header="Tipo" sortable />
    <Column field="moeda" header="Moeda" sortable />
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

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Conta' : 'Nova Conta'"
          modal :style="{ width: '480px' }">
    <div class="form">
      <label>Nome</label>
      <InputText v-model="form.nome" />
      <label>Instituição</label>
      <Dropdown v-model="form.instituicao_id" :options="instituicoes"
                optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      <label>Tipo</label>
      <Dropdown v-model="form.tipo" :options="tipos" optionLabel="label" optionValue="value" />
      <label>Moeda</label>
      <Dropdown v-model="form.moeda" :options="moedas" optionLabel="label" optionValue="value" />
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
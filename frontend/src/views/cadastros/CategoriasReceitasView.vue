<script setup lang="ts">
import { ref, onMounted } from "vue"
import { catRecService, type CategoriaReceita } from "@/services/categorias"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()
const lista = ref<CategoriaReceita[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<CategoriaReceita>>({ nome: "", recorrencia: "eventual", cor: "#28a745" })

const recorrencias = [
  { label: "Recorrente", value: "recorrente" },
  { label: "Eventual", value: "eventual" }
]

async function carregar() {
  carregando.value = true
  try { lista.value = await catRecService.listar() }
  catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { nome: "", recorrencia: "eventual", cor: "#28a745" }
  dialogVisivel.value = true
}

function abrirEdicao(row: CategoriaReceita) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await catRecService.atualizar(editando.value, form.value)
    else await catRecService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: CategoriaReceita) {
  try {
    await catRecService.inativar(row.id)
    toast.add({ severity: "info", summary: "Inativada", life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Categorias de Receitas" subtitle="Cadastro M03">
    <template #actions>
      <Button label="Nova Categoria" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column header="Nome" sortable sortField="nome">
      <template #body="{ data }">
        <span class="cat-pill" :style="{ background: (data.cor || '#28a745') + '33', color: data.cor || '#28a745' }">
          {{ data.nome }}
        </span>
      </template>
    </Column>
    <Column field="recorrencia" header="Recorrência" sortable />
    <Column header="Status">
      <template #body="{ data }">
        <Tag :severity="data.ativo ? 'success' : 'secondary'" :value="data.ativo ? 'Ativa' : 'Inativa'" />
      </template>
    </Column>
    <Column header="Ações" style="width: 10rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button v-if="data.ativo" icon="pi pi-trash" severity="danger" text @click="inativar(data)" />
      </template>
    </Column>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Categoria' : 'Nova Categoria'" modal :style="{ width: '460px' }">
    <div class="form">
      <label>Nome</label>
      <InputText v-model="form.nome" />
      <label>Recorrência</label>
      <Dropdown v-model="form.recorrencia" :options="recorrencias" optionLabel="label" optionValue="value" />
      <label>Cor (hex)</label>
      <InputText v-model="form.cor" placeholder="#28a745" />
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
.cat-pill { padding: 4px 10px; border-radius: var(--radius-full); font-size: var(--text-sm); font-weight: 500; }
</style>
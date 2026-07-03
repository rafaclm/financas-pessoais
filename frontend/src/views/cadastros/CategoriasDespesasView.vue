<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { catDespService, type CategoriaDespesa } from '@/services/categorias'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import Tag from 'primevue/tag'
import PageHeader from '@/components/PageHeader.vue'

const toast = useToast()
const lista = ref<CategoriaDespesa[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<CategoriaDespesa>>({
  nome: '', tipo: 'variavel', essencial: 0, cor: '#888888', icone: ''
})

const tipos = [{ label: 'Fixa', value: 'fixa' }, { label: 'Variável', value: 'variavel' }]

async function carregar() {
  carregando.value = true
  try { lista.value = await catDespService.listar() }
  catch (e: any) { toast.add({ severity: 'error', summary: 'Erro', detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { nome: '', tipo: 'variavel', essencial: 0, cor: '#888888' }
  dialogVisivel.value = true
}

function abrirEdicao(row: CategoriaDespesa) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await catDespService.atualizar(editando.value, form.value)
    else await catDespService.criar(form.value)
    toast.add({ severity: 'success', summary: 'Salvo', life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.message, life: 4000 })
  }
}

async function inativar(row: CategoriaDespesa) {
  try {
    await catDespService.inativar(row.id)
    toast.add({ severity: 'info', summary: 'Inativada', life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: 'error', summary: 'Erro', detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Categorias de Despesas" subtitle="Cadastro M02">
    <template #actions>
      <Button label="Nova Categoria" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column header="Nome" sortable sortField="nome">
      <template #body="{ data }">
        <span class="cat-pill" :style="{ background: data.cor + '33', color: data.cor }">
          {{ data.nome }}
        </span>
      </template>
    </Column>
    <Column field="tipo" header="Tipo" sortable />
    <Column header="Essencial">
      <template #body="{ data }">
        <Tag :severity="data.essencial ? 'info' : 'secondary'"
             :value="data.essencial ? 'Sim' : 'Não'" />
      </template>
    </Column>
    <Column header="Status">
      <template #body="{ data }">
        <Tag :severity="data.ativo ? 'success' : 'secondary'"
             :value="data.ativo ? 'Ativa' : 'Inativa'" />
      </template>
    </Column>
    <Column header="Ações" style="width: 10rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button v-if="data.ativo" icon="pi pi-trash" severity="danger" text @click="inativar(data)" />
      </template>
    </Column>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Categoria' : 'Nova Categoria'"
          modal :style="{ width: '460px' }">
    <div class="form">
      <label>Nome</label>
      <InputText v-model="form.nome" />
      <label>Tipo</label>
      <Dropdown v-model="form.tipo" :options="tipos" optionLabel="label" optionValue="value" />
      <label>Cor (hex)</label>
      <InputText v-model="form.cor" placeholder="#888888" />
      <div class="row">
        <Checkbox v-model="form.essencial" :binary="true" inputId="ess" />
        <label for="ess">Essencial</label>
      </div>
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
.row { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-3); }
.cat-pill {
  padding: 4px 10px; border-radius: var(--radius-full);
  font-size: var(--text-sm); font-weight: 500;
}
</style>
<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { produtosService, type ProdutoInvestimento } from "@/services/produtos"
import { instituicoesService, type Instituicao } from "@/services/instituicoes"
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
const lista = ref<ProdutoInvestimento[]>([])
const instituicoes = ref<Instituicao[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<ProdutoInvestimento>>({
  nome: "", categoria: "renda_fixa", instituicao_id: undefined, moeda: "BRL"
})

const categorias = [
  { label: "Renda Fixa", value: "renda_fixa" },
  { label: "Previdência", value: "previdencia" },
  { label: "FGTS", value: "fgts" },
  { label: "Fundo", value: "fundo" },
  { label: "Outro", value: "outro" }
]
const moedas = [{ label: "BRL", value: "BRL" }, { label: "USD", value: "USD" }]

const mapInst = computed(() => {
  const m = new Map<number, string>()
  instituicoes.value.forEach(i => m.set(i.id, i.nome))
  return m
})

const labelCat = (c: string) => categorias.find(x => x.value === c)?.label || c

async function carregar() {
  carregando.value = true
  try {
    const [prods, insts] = await Promise.all([
      produtosService.listar(),
      instituicoesService.listar(true)
    ])
    lista.value = prods
    instituicoes.value = insts
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { nome: "", categoria: "renda_fixa", instituicao_id: undefined, moeda: "BRL" }
  dialogVisivel.value = true
}

function abrirEdicao(row: ProdutoInvestimento) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await produtosService.atualizar(editando.value, form.value)
    else await produtosService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: ProdutoInvestimento) {
  try {
    await produtosService.inativar(row.id)
    toast.add({ severity: "info", summary: "Inativado", life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Produtos de Investimento" subtitle="Cadastro M07 — Renda Fixa, Previdência, FGTS, Fundos">
    <template #actions>
      <Button label="Novo Produto" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column field="nome" header="Nome" sortable />
    <Column header="Categoria" sortable sortField="categoria">
      <template #body="{ data }">{{ labelCat(data.categoria) }}</template>
    </Column>
    <Column header="Instituição">
      <template #body="{ data }">{{ mapInst.get(data.instituicao_id) || "—" }}</template>
    </Column>
    <Column field="moeda" header="Moeda" />
    <Column header="Status">
      <template #body="{ data }">
        <Tag :severity="data.ativo ? 'success' : 'secondary'" :value="data.ativo ? 'Ativo' : 'Inativo'" />
      </template>
    </Column>
    <Column header="Ações" style="width: 10rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button v-if="data.ativo" icon="pi pi-trash" severity="danger" text @click="inativar(data)" />
      </template>
    </Column>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Produto' : 'Novo Produto'" modal :style="{ width: '500px' }">
    <div class="form">
      <label>Nome</label>
      <InputText v-model="form.nome" placeholder="Ex.: CDB Itaú 110% CDI" />
      <label>Categoria</label>
      <Dropdown v-model="form.categoria" :options="categorias" optionLabel="label" optionValue="value" />
      <label>Instituição</label>
      <Dropdown v-model="form.instituicao_id" :options="instituicoes" optionLabel="nome" optionValue="id" placeholder="Selecione..." />
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
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
</style>
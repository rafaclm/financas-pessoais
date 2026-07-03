<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { cartoesService, type Cartao } from "@/services/cartoes"
import { instituicoesService, type Instituicao } from "@/services/instituicoes"
import { contasService, type Conta } from "@/services/contas"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()
const lista = ref<Cartao[]>([])
const instituicoes = ref<Instituicao[]>([])
const contas = ref<Conta[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Cartao>>({
  nome: "", instituicao_id: undefined,
  conta_pagamento_id: null, dia_fechamento: 1, dia_vencimento: 10
})

const mapInst = computed(() => {
  const m = new Map<number, string>()
  instituicoes.value.forEach(i => m.set(i.id, i.nome))
  return m
})

const mapConta = computed(() => {
  const m = new Map<number, string>()
  contas.value.forEach(c => m.set(c.id, c.nome))
  return m
})

async function carregar() {
  carregando.value = true
  try {
    const [cards, insts, ctas] = await Promise.all([
      cartoesService.listar(),
      instituicoesService.listar(true),
      contasService.listar(true)
    ])
    lista.value = cards
    instituicoes.value = insts
    contas.value = ctas
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { nome: "", instituicao_id: undefined, conta_pagamento_id: null, dia_fechamento: 1, dia_vencimento: 10 }
  dialogVisivel.value = true
}

function abrirEdicao(row: Cartao) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await cartoesService.atualizar(editando.value, form.value)
    else await cartoesService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: Cartao) {
  try {
    await cartoesService.inativar(row.id)
    toast.add({ severity: "info", summary: "Inativado", life: 2500 })
    await carregar()
  } catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message }) }
}

onMounted(carregar)
</script>

<template>
  <PageHeader title="Cartões de Crédito" subtitle="Cadastro M06">
    <template #actions>
      <Button label="Novo Cartão" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column field="nome" header="Nome" sortable />
    <Column header="Instituição">
      <template #body="{ data }">{{ mapInst.get(data.instituicao_id) || "—" }}</template>
    </Column>
    <Column header="Conta de Pagamento">
      <template #body="{ data }">
        {{ data.conta_pagamento_id ? mapConta.get(data.conta_pagamento_id) : "—" }}
      </template>
    </Column>
    <Column field="dia_fechamento" header="Fechamento" />
    <Column field="dia_vencimento" header="Vencimento" />
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

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Cartão' : 'Novo Cartão'" modal :style="{ width: '500px' }">
    <div class="form">
      <label>Nome</label>
      <InputText v-model="form.nome" placeholder="Ex.: Itaú Cartão" />
      <label>Instituição</label>
      <Dropdown v-model="form.instituicao_id" :options="instituicoes" optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      <label>Conta de Pagamento (opcional)</label>
      <Dropdown v-model="form.conta_pagamento_id" :options="contas" optionLabel="nome" optionValue="id" placeholder="Selecione..." showClear />
      <div class="row">
        <div class="col">
          <label>Dia de Fechamento</label>
          <InputNumber v-model="form.dia_fechamento" :min="1" :max="31" :useGrouping="false" />
        </div>
        <div class="col">
          <label>Dia de Vencimento</label>
          <InputNumber v-model="form.dia_vencimento" :min="1" :max="31" :useGrouping="false" />
        </div>
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
.row { display: flex; gap: var(--space-3); margin-top: var(--space-2); }
.col { display: flex; flex-direction: column; flex: 1; gap: var(--space-2); }
</style>
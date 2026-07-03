<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { anosService, type Ano } from "@/services/anos"
import { http } from "@/services/http"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Textarea from "primevue/textarea"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"
import FiltroStatus from "@/components/FiltroStatus.vue"

const toast = useToast()
const lista = ref<Ano[]>([])
const carregando = ref(false)
const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Ano>>({})
const filtroStatus = ref<"ativos" | "inativos" | "todos">("ativos")

const listaFiltrada = computed(() => {
  if (filtroStatus.value === "todos") return lista.value
  if (filtroStatus.value === "ativos") return lista.value.filter(a => a.ativo === 1)
  return lista.value.filter(a => a.ativo === 0)
})

async function carregar() {
  carregando.value = true
  try { lista.value = await anosService.listar() }
  catch (e: any) { toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 }) }
  finally { carregando.value = false }
}

function abrirNovo() {
  editando.value = null
  form.value = { ano: new Date().getFullYear(), saldo_inicial: 0, observacao: "" }
  dialogVisivel.value = true
}

function abrirEdicao(row: Ano) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) {
      await anosService.atualizar(editando.value, {
        saldo_inicial: form.value.saldo_inicial,
        observacao: form.value.observacao,
        ativo: form.value.ativo ?? 1,
      })
      toast.add({ severity: "success", summary: "Ano atualizado", life: 2500 })
    } else {
      await anosService.criar(form.value)
      toast.add({ severity: "success", summary: "Ano criado", life: 3000 })
    }
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function inativar(row: Ano) {
  if (!confirm(`Inativar o ano ${row.ano}?`)) return
  try {
    await anosService.inativar(row.id)
    toast.add({ severity: "info", summary: "Inativado", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function reativar(row: Ano) {
  try {
    await http.post(`/anos/${row.id}/reativar`)
    toast.add({ severity: "success", summary: `Ano ${row.ano} reativado`, life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

onMounted(carregar)
</script>

<template>
  <PageHeader title="Anos" subtitle="Cadastro de anos contábeis (M01)">
    <template #actions>
      <Button label="Novo Ano" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <div class="filtros">
    <FiltroStatus v-model="filtroStatus" />
  </div>

  <DataTable :value="listaFiltrada" :loading="carregando" stripedRows>
    <Column field="ano" header="Ano" sortable />
    <Column header="Saldo inicial" sortable sortField="saldo_inicial">
      <template #body="{ data }">
        <span class="tabular">{{ fmtBRL(data.saldo_inicial) }}</span>
      </template>
    </Column>
    <Column field="observacao" header="Observação" sortable />
    <Column header="Status" sortable sortField="ativo">
      <template #body="{ data }">
        <Tag :severity="data.ativo ? 'success' : 'secondary'"
             :value="data.ativo ? 'Ativo' : 'Inativo'" />
      </template>
    </Column>
    <Column header="Ações" style="width: 10rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text v-tooltip="'Editar'"
                @click="abrirEdicao(data)" />
        <!-- 🆕 Botão de Reativar só aparece em inativos -->
        <Button v-if="!data.ativo" icon="pi pi-check-circle" severity="success" text
                v-tooltip="'Reativar'" @click="reativar(data)" />
        <Button v-else icon="pi pi-trash" severity="danger" text
                v-tooltip="'Inativar'" @click="inativar(data)" />
      </template>
    </Column>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel"
          :header="editando ? `Editar Ano ${form.ano}` : 'Novo Ano'"
          modal :style="{ width: '460px' }">
    <div class="form">
      <label>Ano</label>
      <InputNumber v-model="form.ano" :useGrouping="false" :min="2000" :max="2100"
                   :disabled="!!editando" />
      <label>Saldo inicial (R$)</label>
      <InputNumber v-model="form.saldo_inicial" mode="currency" currency="BRL" locale="pt-BR" />
      <label>Observação</label>
      <Textarea v-model="form.observacao" rows="2" />
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
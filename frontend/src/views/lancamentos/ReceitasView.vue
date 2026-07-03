<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import { receitasService, type Receita } from "@/services/receitas"
import { catRecService, type CategoriaReceita } from "@/services/categorias"
import { contasService, type Conta } from "@/services/contas"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Checkbox from "primevue/checkbox"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"
import DialogReplicar from "@/components/DialogReplicar.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref<Receita[]>([])
const categorias = ref<CategoriaReceita[]>([])
const contas = ref<Conta[]>([])
const carregando = ref(false)

const dialogVisivel = ref(false)
const dialogReplicar = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Receita>>({})

const mapCat = computed(() => {
  const m = new Map<number, CategoriaReceita>()
  categorias.value.forEach(c => m.set(c.id, c))
  return m
})
const mapConta = computed(() => {
  const m = new Map<number, string>()
  contas.value.forEach(c => m.set(c.id, c.nome))
  return m
})

const totalMes = computed(() =>
  lista.value.reduce((acc, r) => acc + Number(r.valor), 0)
)

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [recs, cats, cts] = await Promise.all([
      receitasService.listar({ ano_id: periodo.anoIdSelecionado, mes: periodo.mesSelecionado }),
      categorias.value.length ? Promise.resolve(categorias.value) : catRecService.listar(true),
      contas.value.length ? Promise.resolve(contas.value) : contasService.listar(true),
    ])
    lista.value = recs
    if (!categorias.value.length) categorias.value = cats
    if (!contas.value.length) contas.value = cts
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })

function abrirNovo() {
  editando.value = null
  form.value = {
    ano_id: periodo.anoIdSelecionado!,
    mes: periodo.mesSelecionado,
    categoria_id: categorias.value[0]?.id,
    conta_id: contas.value[0]?.id,
    valor: 0,
    descricao: "",
    recorrente: 0,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: Receita) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value) await receitasService.atualizar(editando.value, form.value)
    else await receitasService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: Receita) {
  if (!confirm(`Excluir receita de ${fmtBRL(row.valor)}?`)) return
  try {
    await receitasService.excluir(row.id)
    toast.add({ severity: "info", summary: "Excluída", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="💚 Receitas" :subtitle="`Lançamentos de ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="🔁 Replicar mês" outlined @click="dialogReplicar = true" />
      <Button label="Nova Receita" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column header="Categoria">
      <template #body="{ data }">
        <span class="cat-pill"
              :style="{
                background: (mapCat.get(data.categoria_id)?.cor || '#28a745') + '33',
                color: mapCat.get(data.categoria_id)?.cor || '#28a745'
              }">
          {{ mapCat.get(data.categoria_id)?.nome || "—" }}
        </span>
      </template>
    </Column>
    <Column header="Conta">
      <template #body="{ data }">{{ mapConta.get(data.conta_id) || "—" }}</template>
    </Column>
    <Column field="descricao" header="Descrição" />
    <Column header="Valor" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-positive">{{ fmtBRL(data.valor) }}</span>
      </template>
    </Column>
    <Column header="Recorrente">
      <template #body="{ data }">
        <Tag v-if="data.recorrente" severity="info" value="🔁 Recorrente" />
      </template>
    </Column>
    <Column header="Ações" style="width: 8rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total do mês: <strong class="tabular value-positive">{{ fmtBRL(totalMes) }}</strong>
        ({{ lista.length }} lançamentos)
      </div>
    </template>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Receita' : 'Nova Receita'"
          modal :style="{ width: '500px' }">
    <div class="form">
      <label>Categoria</label>
      <Dropdown v-model="form.categoria_id" :options="categorias"
                optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      <label>Conta de destino</label>
      <Dropdown v-model="form.conta_id" :options="contas"
                optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      <label>Valor (R$)</label>
      <InputNumber v-model="form.valor" mode="currency" currency="BRL" locale="pt-BR" />
      <label>Descrição (opcional)</label>
      <InputText v-model="form.descricao" />
      <div class="row">
        <Checkbox v-model="form.recorrente" :binary="true" inputId="rec"
                  :trueValue="1" :falseValue="0" />
        <label for="rec">🔁 Lançamento recorrente (será replicado no próximo mês)</label>
      </div>
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogVisivel = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvar" />
    </template>
  </Dialog>

  <DialogReplicar v-model:visible="dialogReplicar" @concluido="carregar" />
</template>

<style scoped>
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
.row { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-3); }
.row label { margin: 0 !important; cursor: pointer; }
.cat-pill { padding: 4px 10px; border-radius: var(--radius-full); font-size: var(--text-sm); font-weight: 500; }
.footer-total { text-align: right; font-size: var(--text-base); padding: var(--space-2) 0; }
</style>
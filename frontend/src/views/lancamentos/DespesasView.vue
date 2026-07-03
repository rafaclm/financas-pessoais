<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import { despesasService, type Despesa } from "@/services/despesas"
import { catDespService, type CategoriaDespesa } from "@/services/categorias"
import { contasService, type Conta } from "@/services/contas"
import { cartoesService, type Cartao } from "@/services/cartoes"
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

const lista = ref<Despesa[]>([])
const categorias = ref<CategoriaDespesa[]>([])
const contas = ref<Conta[]>([])
const cartoes = ref<Cartao[]>([])
const carregando = ref(false)

const dialogVisivel = ref(false)
const dialogReplicar = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Despesa>>({})

const origemOptions = [
  { label: "Conta", value: "conta" },
  { label: "Cartão", value: "cartao" }
]

const mapCat = computed(() => {
  const m = new Map<number, CategoriaDespesa>()
  categorias.value.forEach(c => m.set(c.id, c))
  return m
})
const mapConta = computed(() => {
  const m = new Map<number, string>()
  contas.value.forEach(c => m.set(c.id, c.nome))
  return m
})
const mapCartao = computed(() => {
  const m = new Map<number, string>()
  cartoes.value.forEach(c => m.set(c.id, c.nome))
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
    const [desps, cats, cts, cards] = await Promise.all([
      despesasService.listar({ ano_id: periodo.anoIdSelecionado, mes: periodo.mesSelecionado }),
      categorias.value.length ? Promise.resolve(categorias.value) : catDespService.listar(true),
      contas.value.length ? Promise.resolve(contas.value) : contasService.listar(true),
      cartoes.value.length ? Promise.resolve(cartoes.value) : cartoesService.listar(true),
    ])
    lista.value = desps
    if (!categorias.value.length) categorias.value = cats
    if (!contas.value.length) contas.value = cts
    if (!cartoes.value.length) cartoes.value = cards
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
    origem_tipo: "conta",
    conta_id: contas.value[0]?.id,
    cartao_id: null,
    valor: 0,
    descricao: "",
    recorrente: 0,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: Despesa) {
  if (row.auto_pagamento_cartao === 1) {
    toast.add({
      severity: "warn",
      summary: "Despesa automática",
      detail: "Esta despesa foi gerada por pagamento de cartão. Edite na tela de Pagamento de Cartão.",
      life: 5000
    })
    return
  }
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  // Limpa o id inativo conforme origem_tipo
  if (form.value.origem_tipo === "conta") form.value.cartao_id = null
  else form.value.conta_id = null

  try {
    if (editando.value) await despesasService.atualizar(editando.value, form.value)
    else await despesasService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: Despesa) {
  if (row.auto_pagamento_cartao === 1) {
    toast.add({
      severity: "warn",
      summary: "Despesa automática",
      detail: "Exclua o Pagamento de Cartão correspondente.",
      life: 5000
    })
    return
  }
  if (!confirm(`Excluir despesa de ${fmtBRL(row.valor)}?`)) return
  try {
    await despesasService.excluir(row.id)
    toast.add({ severity: "info", summary: "Excluída", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="❤️ Despesas" :subtitle="`Lançamentos de ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="🔁 Replicar mês" outlined @click="dialogReplicar = true" />
      <Button label="Nova Despesa" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows
             :paginator="true" :rows="50">
    <Column header="Categoria">
      <template #body="{ data }">
        <span class="cat-pill"
              :style="{
                background: (mapCat.get(data.categoria_id)?.cor || '#EF4444') + '33',
                color: mapCat.get(data.categoria_id)?.cor || '#EF4444'
              }">
          {{ mapCat.get(data.categoria_id)?.nome || "—" }}
        </span>
      </template>
    </Column>
    <Column header="Origem">
      <template #body="{ data }">
        <span v-if="data.origem_tipo === 'conta'">👛 {{ mapConta.get(data.conta_id) || "—" }}</span>
        <span v-else>💳 {{ mapCartao.get(data.cartao_id) || "—" }}</span>
      </template>
    </Column>
    <Column field="descricao" header="Descrição" />
    <Column header="Valor" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-negative">{{ fmtBRL(data.valor) }}</span>
      </template>
    </Column>
    <Column header="Flags">
      <template #body="{ data }">
        <Tag v-if="data.recorrente" severity="info" value="🔁" />
        <Tag v-if="data.auto_pagamento_cartao" severity="warning" value="🤖 Auto" />
      </template>
    </Column>
    <Column header="Ações" style="width: 8rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)"
                :disabled="data.auto_pagamento_cartao === 1" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)"
                :disabled="data.auto_pagamento_cartao === 1" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total do mês: <strong class="tabular value-negative">{{ fmtBRL(totalMes) }}</strong>
        ({{ lista.length }} lançamentos)
      </div>
    </template>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar Despesa' : 'Nova Despesa'"
          modal :style="{ width: '500px' }">
    <div class="form">
      <label>Categoria</label>
      <Dropdown v-model="form.categoria_id" :options="categorias"
                optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      <label>Origem</label>
      <Dropdown v-model="form.origem_tipo" :options="origemOptions"
                optionLabel="label" optionValue="value" />
      <template v-if="form.origem_tipo === 'conta'">
        <label>Conta</label>
        <Dropdown v-model="form.conta_id" :options="contas"
                  optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      </template>
      <template v-else>
        <label>Cartão</label>
        <Dropdown v-model="form.cartao_id" :options="cartoes"
                  optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      </template>
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
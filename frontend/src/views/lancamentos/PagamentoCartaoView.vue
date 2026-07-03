<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  pagamentosCartaoService, type PagamentoCartao
} from "@/services/pagamentosCartao"
import { cartoesService, type Cartao } from "@/services/cartoes"
import { contasService, type Conta } from "@/services/contas"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Message from "primevue/message"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref<PagamentoCartao[]>([])
const cartoes = ref<Cartao[]>([])
const contas = ref<Conta[]>([])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<PagamentoCartao>>({})

const mapCartao = computed(() => {
  const m = new Map<number, string>()
  cartoes.value.forEach(c => m.set(c.id, c.nome))
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
    const [lst, cards, cts] = await Promise.all([
      pagamentosCartaoService.listar({
        ano_id: periodo.anoIdSelecionado, mes: periodo.mesSelecionado
      }),
      cartoes.value.length ? Promise.resolve(cartoes.value) : cartoesService.listar(true),
      contas.value.length ? Promise.resolve(contas.value) : contasService.listar(true),
    ])
    lista.value = lst
    if (!cartoes.value.length) cartoes.value = cards
    if (!contas.value.length) contas.value = cts
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })

function cartaoSugerido(): { cartao_id: number | undefined; conta_id: number | undefined } {
  const card = cartoes.value[0]
  if (!card) return { cartao_id: undefined, conta_id: contas.value[0]?.id }
  return {
    cartao_id: card.id,
    conta_id: card.conta_pagamento_id ?? contas.value[0]?.id
  }
}

function abrirNovo() {
  editando.value = null
  const sug = cartaoSugerido()
  form.value = {
    ano_id: periodo.anoIdSelecionado!,
    mes: periodo.mesSelecionado,
    cartao_id: sug.cartao_id,
    conta_id: sug.conta_id,
    valor: 0,
    descricao: "",
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: PagamentoCartao) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

// Quando troca o cartão, sugere automaticamente a conta de pagamento associada
function aoTrocarCartao(novoId: number) {
  form.value.cartao_id = novoId
  const card = cartoes.value.find(c => c.id === novoId)
  if (card?.conta_pagamento_id) form.value.conta_id = card.conta_pagamento_id
}

async function salvar() {
  try {
    if (editando.value)
      await pagamentosCartaoService.atualizar(editando.value, form.value)
    else
      await pagamentosCartaoService.criar(form.value)
    toast.add({
      severity: "success", summary: "Salvo",
      detail: "Despesa automática criada/atualizada na categoria Cartão.",
      life: 3500
    })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: PagamentoCartao) {
  if (!confirm(
    `Excluir pagamento de ${fmtBRL(row.valor)}?\n\n`
    + `A despesa automática vinculada também será removida.`
  )) return
  try {
    await pagamentosCartaoService.excluir(row.id)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="💳 Pagamento de Cartão"
              :subtitle="`Faturas pagas em ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="Novo pagamento" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <Message severity="info" :closable="false" class="msg-info">
    Ao registrar um pagamento, uma <strong>despesa automática</strong> é criada na
    categoria <strong>"Cartão"</strong> do mesmo mês — você não precisa lançar manualmente.
  </Message>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column header="Cartão">
      <template #body="{ data }">
        <span class="cart-tag">💳 {{ mapCartao.get(data.cartao_id) || "—" }}</span>
      </template>
    </Column>
    <Column header="Conta debitada">
      <template #body="{ data }">{{ mapConta.get(data.conta_id) || "—" }}</template>
    </Column>
    <Column field="descricao" header="Descrição">
      <template #body="{ data }">{{ data.descricao || "—" }}</template>
    </Column>
    <Column header="Valor" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-negative">{{ fmtBRL(data.valor) }}</span>
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
        Total pago em cartões no mês:
        <strong class="tabular value-negative">{{ fmtBRL(totalMes) }}</strong>
        ({{ lista.length }} pagamento{{ lista.length !== 1 ? "s" : "" }})
      </div>
    </template>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel"
          :header="editando ? 'Editar pagamento' : 'Novo pagamento de cartão'"
          modal :style="{ width: '500px' }">
    <div class="form">
      <label>Cartão</label>
      <Dropdown :modelValue="form.cartao_id" @update:modelValue="aoTrocarCartao"
                :options="cartoes" optionLabel="nome" optionValue="id"
                placeholder="Selecione..." />

      <label>Conta debitada</label>
      <Dropdown v-model="form.conta_id" :options="contas"
                optionLabel="nome" optionValue="id" placeholder="Selecione..." />

      <label>Valor da fatura (R$)</label>
      <InputNumber v-model="form.valor" mode="currency" currency="BRL" locale="pt-BR" />

      <label>Descrição (opcional)</label>
      <InputText v-model="form.descricao" placeholder="Ex.: Fatura 06/2026" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogVisivel = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvar" />
    </template>
  </Dialog>
</template>

<style scoped>
.msg-info { margin-bottom: var(--space-4); }
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
.cart-tag { font-weight: 500; }
.footer-total { text-align: right; font-size: var(--text-base); padding: var(--space-2) 0; }
</style>
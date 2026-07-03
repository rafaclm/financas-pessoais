<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  saldosInvService, type SaldoInvestimento
} from "@/services/saldosInvestimentos"
import { produtosService, type ProdutoInvestimento } from "@/services/produtos"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import InputNumber from "primevue/inputnumber"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref<SaldoInvestimento[]>([])
const produtos = ref<ProdutoInvestimento[]>([])
const carregando = ref(false)
const salvando = ref(false)
const edicao = ref<Record<number, { saldo: number; cotacao_usd_brl: number | null }>>({})

const totalBRL = computed(() =>
  lista.value.reduce((acc, s) => acc + Number(s.saldo_brl), 0)
)

const linhasMontadas = computed(() => {
  return produtos.value.map(p => {
    const existente = lista.value.find(s => s.produto_id === p.id)
    const edit = edicao.value[p.id]
    return {
      produto: p,
      existente,
      saldo: edit?.saldo ?? Number(existente?.saldo ?? 0),
      cotacao: edit?.cotacao_usd_brl ?? existente?.cotacao_usd_brl ?? null,
      saldo_brl: existente?.saldo_brl ?? 0,
    }
  })
})

const labelCategoria = (c: string) => ({
  renda_fixa: "Renda Fixa",
  previdencia: "Previdência",
  fgts: "FGTS",
  fundo: "Fundo",
  outro: "Outro"
} as any)[c] || c

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [saldos, prods] = await Promise.all([
      saldosInvService.listar(periodo.anoIdSelecionado, periodo.mesSelecionado),
      produtos.value.length ? Promise.resolve(produtos.value) : produtosService.listar(true),
    ])
    lista.value = saldos
    if (!produtos.value.length) produtos.value = prods
    edicao.value = {}
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })

function alterouSaldo(produto_id: number, valor: number) {
  if (!edicao.value[produto_id]) edicao.value[produto_id] = { saldo: 0, cotacao_usd_brl: null }
  edicao.value[produto_id].saldo = valor
}

function alterouCotacao(produto_id: number, valor: number) {
  if (!edicao.value[produto_id]) edicao.value[produto_id] = { saldo: 0, cotacao_usd_brl: null }
  edicao.value[produto_id].cotacao_usd_brl = valor
}

async function salvarTudo() {
  const itens = linhasMontadas.value
    .filter(l => edicao.value[l.produto.id] !== undefined || !l.existente)
    .map(l => ({
      ano_id: periodo.anoIdSelecionado!,
      mes: periodo.mesSelecionado,
      produto_id: l.produto.id,
      saldo: l.saldo,
      cotacao_usd_brl: l.cotacao,
    }))

  if (itens.length === 0) {
    toast.add({ severity: "info", summary: "Nada para salvar", life: 2500 })
    return
  }

  salvando.value = true
  try {
    await saldosInvService.lote(itens as any)
    toast.add({ severity: "success", summary: `${itens.length} saldos salvos`, life: 3000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally {
    salvando.value = false
  }
}

async function replicar() {
  if (!confirm(`Replicar saldos do mês anterior para ${periodo.labelPeriodo}?`)) return
  try {
    const r = await saldosInvService.replicarMesAnterior(
      periodo.anoIdSelecionado!, periodo.mesSelecionado
    )
    toast.add({ severity: "success", summary: "Replicado", detail: r.mensagem, life: 4000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(item: SaldoInvestimento) {
  if (!confirm(`Remover saldo deste produto?`)) return
  try {
    await saldosInvService.excluir(item.id)
    toast.add({ severity: "info", summary: "Removido", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="📈 Saldos de Investimentos"
              :subtitle="`Renda Fixa, Previdência, FGTS, Fundos - ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="🔁 Replicar mês anterior" outlined @click="replicar" />
      <Button label="Salvar saldos" icon="pi pi-check"
              :loading="salvando" @click="salvarTudo" />
    </template>
  </PageHeader>

  <DataTable :value="linhasMontadas" :loading="carregando" stripedRows>
    <Column header="Produto">
      <template #body="{ data }">
        <strong>{{ data.produto.nome }}</strong>
        <Tag :value="labelCategoria(data.produto.categoria)" severity="info" class="cat-tag" />
        <Tag :value="data.produto.moeda" severity="secondary" class="cat-tag" />
      </template>
    </Column>
    <Column header="Saldo">
      <template #body="{ data }">
        <InputNumber
          :modelValue="data.saldo"
          @update:modelValue="(v: number) => alterouSaldo(data.produto.id, v)"
          mode="currency" :currency="data.produto.moeda" locale="pt-BR" />
      </template>
    </Column>
    <Column header="Cotação USD/BRL (se USD)">
      <template #body="{ data }">
        <InputNumber v-if="data.produto.moeda === 'USD'"
          :modelValue="data.cotacao"
          @update:modelValue="(v: number) => alterouCotacao(data.produto.id, v)"
          :minFractionDigits="4" :maxFractionDigits="4"
          placeholder="Auto" locale="pt-BR" />
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Saldo em BRL" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ fmtBRL(data.saldo_brl) }}</span>
      </template>
    </Column>
    <Column header="Status">
      <template #body="{ data }">
        <Tag v-if="data.existente" severity="success" value="✓ Salvo" />
        <Tag v-else severity="warning" value="Pendente" />
      </template>
    </Column>
    <Column header="Ações" style="width: 6rem">
      <template #body="{ data }">
        <Button v-if="data.existente" icon="pi pi-trash" severity="danger"
                text @click="excluir(data.existente)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total de Investimentos: <strong class="tabular">{{ fmtBRL(totalBRL) }}</strong>
      </div>
    </template>
  </DataTable>
</template>

<style scoped>
.cat-tag { margin-left: var(--space-2); }
.footer-total { text-align: right; font-size: var(--text-base); padding: var(--space-2) 0; }
</style>
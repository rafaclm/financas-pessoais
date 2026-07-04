<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  saldosInvestimentosService,
  type SaldoInvestimentoComVariacao
} from "@/services/saldosInvestimentos"
import { produtosService, type Produto } from "@/services/produtos"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import InputNumber from "primevue/inputnumber"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"
import { TrendingUp, TrendingDown, Minus } from "lucide-vue-next"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref([] as SaldoInvestimentoComVariacao[])
const produtos = ref([] as Produto[])
const carregando = ref(false)
const salvando = ref(false)

const edicao = ref({} as Record<number, { saldo: number; cotacao_usd_brl: number | null }>)

const linhasMontadas = computed(() => {
  return lista.value.map(item => {
    const edit = edicao.value[item.produto_id]
    return {
      ...item,
      saldo_edit: edit?.saldo ?? item.saldo,
      cotacao_edit: edit?.cotacao_usd_brl ?? item.cotacao_usd_brl,
    }
  })
})

const totalBRL = computed(() =>
  lista.value.reduce((acc, s) => acc + Number(s.saldo_brl), 0)
)

const totalMesAnterior = computed(() =>
  lista.value.reduce((acc, s) => acc + Number(s.saldo_brl_mes_anterior), 0)
)

const variacaoTotal = computed(() => {
  if (totalMesAnterior.value === 0) return null
  return {
    valor: totalBRL.value - totalMesAnterior.value,
    pct: (totalBRL.value - totalMesAnterior.value) / totalMesAnterior.value * 100,
  }
})

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

const fmtPct = (v: number | null) =>
  v === null || v === undefined ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [saldos, prods] = await Promise.all([
      saldosInvestimentosService.listarComVariacao(
        periodo.anoIdSelecionado, periodo.mesSelecionado
      ),
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
    .filter(l => edicao.value[l.produto_id] !== undefined || !l.existe)
    .map(l => ({
      ano_id: periodo.anoIdSelecionado!,
      mes: periodo.mesSelecionado,
      produto_id: l.produto_id,
      saldo: l.saldo_edit,
      cotacao_usd_brl: l.cotacao_edit,
    }))

  if (itens.length === 0) {
    toast.add({ severity: "info", summary: "Nada para salvar", life: 2500 })
    return
  }

  salvando.value = true
  try {
    await saldosInvestimentosService.lote({ itens })
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
    const r = await saldosInvestimentosService.replicarMesAnterior(
      periodo.anoIdSelecionado!, periodo.mesSelecionado
    )
    toast.add({ severity: "success", summary: "Replicado", detail: r.mensagem, life: 4000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(item: SaldoInvestimentoComVariacao) {
  if (!item.saldo_id) return
  if (!confirm(`Remover saldo deste produto?`)) return
  try {
    await saldosInvestimentosService.excluir(item.saldo_id)
    toast.add({ severity: "info", summary: "Removido", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="📈 Saldos de Investimentos"
              :subtitle="`Posição de produtos financeiros • ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="Replicar mês anterior" icon="pi pi-history" outlined @click="replicar" />
      <Button label="Salvar saldos" icon="pi pi-check"
              :loading="salvando" @click="salvarTudo" />
    </template>
  </PageHeader>

  <DataTable :value="linhasMontadas" :loading="carregando" stripedRows>
    <Column header="Produto" style="min-width: 220px">
      <template #body="{ data }">
        <div class="produto-cell">
          <strong>{{ data.produto_nome }}</strong>
          <span class="produto-cat">{{ data.produto_categoria }}</span>
        </div>
      </template>
    </Column>

    <Column header="Moeda">
      <template #body="{ data }">
        <Tag :value="data.produto_moeda"
             :severity="data.produto_moeda === 'USD' ? 'info' : 'secondary'" />
      </template>
    </Column>

    <Column header="Saldo">
      <template #body="{ data }">
        <InputNumber
          :modelValue="data.saldo_edit"
          @update:modelValue="(v) => alterouSaldo(data.produto_id, v)"
          mode="currency" :currency="data.produto_moeda" locale="pt-BR" />
      </template>
    </Column>

    <Column header="Cotação USD/BRL">
      <template #body="{ data }">
        <InputNumber v-if="data.produto_moeda === 'USD'"
          :modelValue="data.cotacao_edit"
          @update:modelValue="(v) => alterouCotacao(data.produto_id, v)"
          :minFractionDigits="4" :maxFractionDigits="4"
          placeholder="Auto" locale="pt-BR" />
        <span v-else class="value-muted">—</span>
      </template>
    </Column>

    <Column header="Saldo em BRL" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular numero-destaque">{{ fmtBRL(data.saldo_brl) }}</span>
      </template>
    </Column>

    <!-- 🆕 NOVA COLUNA: Variação % -->
    <Column header="Var. %" style="text-align: right; min-width: 110px">
      <template #body="{ data }">
        <span v-if="data.variacao_pct !== null" class="variacao"
              :class="data.variacao_pct >= 0 ? 'value-positive' : 'value-negative'">
          <TrendingUp v-if="data.variacao_pct > 0" :size="14" />
          <TrendingDown v-else-if="data.variacao_pct < 0" :size="14" />
          <Minus v-else :size="14" />
          <span class="tabular">{{ fmtPct(data.variacao_pct) }}</span>
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>

    <!-- 🆕 NOVA COLUNA: Variação R$ -->
    <Column header="Var. R$" style="text-align: right; min-width: 130px">
      <template #body="{ data }">
        <span v-if="data.variacao_valor !== null" class="tabular"
              :class="data.variacao_valor >= 0 ? 'value-positive' : 'value-negative'">
          {{ data.variacao_valor > 0 ? '+' : '' }}{{ fmtBRL(data.variacao_valor) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>

    <Column header="Status">
      <template #body="{ data }">
        <span v-if="data.existe" class="badge-status salvo">
          <i class="pi pi-check" style="font-size: 10px"></i> Salvo
        </span>
        <span v-else class="badge-status pendente">
          <i class="pi pi-clock" style="font-size: 10px"></i> Pendente
        </span>
      </template>
    </Column>

    <Column header="Ações" style="width: 5rem">
      <template #body="{ data }">
        <Button v-if="data.existe" icon="pi pi-trash" severity="danger"
                text @click="excluir(data)" />
      </template>
    </Column>

    <template #footer>
      <div class="footer-total">
        <div class="footer-linha">
          <span class="lbl">Total consolidado:</span>
          <strong class="tabular numero-destaque">{{ fmtBRL(totalBRL) }}</strong>
        </div>
        <div v-if="variacaoTotal" class="footer-linha">
          <span class="lbl">Variação vs mês anterior:</span>
          <span class="tabular variacao"
                :class="variacaoTotal.pct >= 0 ? 'value-positive' : 'value-negative'">
            <TrendingUp v-if="variacaoTotal.pct > 0" :size="14" />
            <TrendingDown v-else-if="variacaoTotal.pct < 0" :size="14" />
            <Minus v-else :size="14" />
            {{ fmtPct(variacaoTotal.pct) }}
            ({{ variacaoTotal.valor > 0 ? '+' : '' }}{{ fmtBRL(variacaoTotal.valor) }})
          </span>
        </div>
      </div>
    </template>
  </DataTable>
</template>

<style scoped>
.produto-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.produto-cat {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: capitalize;
}

.variacao {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
}

.footer-total {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-end;
  padding: var(--space-3) 0;
}

.footer-linha {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
}

.footer-linha .lbl {
  color: var(--text-muted);
}
</style>
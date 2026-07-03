<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  posicoesCriptoService, type PosicaoCripto
} from "@/services/posicoesCripto"
import { ativosService, type Ativo } from "@/services/ativos"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import { TrendingUp, TrendingDown, Minus } from "lucide-vue-next"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref<PosicaoCripto[]>([])
const ativos = ref<Ativo[]>([])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<PosicaoCripto>>({})

const ativosCripto = computed(() => ativos.value.filter(a => a.classe === "cripto"))

const mapAtivo = computed(() => {
  const m = new Map<number, Ativo>()
  ativos.value.forEach(a => m.set(a.id, a))
  return m
})

const totais = computed(() => {
  const brl = lista.value.reduce((acc, p) => acc + Number(p.saldo_brl), 0)
  const usd = lista.value.reduce((acc, p) => acc + Number(p.saldo_usd), 0)
  return { brl, usd, qtd: lista.value.length }
})

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)
const fmtUSD = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v || 0)
const fmtPct = (v: number | null) =>
  v === null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [pos, ats] = await Promise.all([
      posicoesCriptoService.listar(periodo.anoIdSelecionado, periodo.mesSelecionado),
      ativos.value.length ? Promise.resolve(ativos.value) : ativosService.listar({ apenas_ativos: true }),
    ])
    lista.value = pos
    if (!ativos.value.length) ativos.value = ats
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
    ativo_id: ativosCripto.value[0]?.id,
    quantidade: 0,
    saldo_brl: 0,
    cotacao_usd_brl: undefined,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: PosicaoCripto) {
  editando.value = row.id
  form.value = { ...row }
  dialogVisivel.value = true
}

async function salvar() {
  try {
    if (editando.value)
      await posicoesCriptoService.atualizar(editando.value, form.value)
    else
      await posicoesCriptoService.criar(form.value)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: PosicaoCripto) {
  if (!confirm(`Remover posição de ${mapAtivo.value.get(row.ativo_id)?.ticker}?`)) return
  try {
    await posicoesCriptoService.excluir(row.id)
    toast.add({ severity: "info", summary: "Removido", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

async function replicar() {
  if (!confirm(`Replicar posições do mês anterior para ${periodo.labelPeriodo}?`)) return
  try {
    const r = await posicoesCriptoService.replicarMesAnterior(
      periodo.anoIdSelecionado!, periodo.mesSelecionado
    )
    toast.add({ severity: "success", summary: "Replicado", detail: r.mensagem, life: 4000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

function classeVariacao(v: number | null) {
  if (v === null || v === 0) return "var-neutra"
  return v > 0 ? "var-positiva" : "var-negativa"
}
</script>

<template>
  <PageHeader title="₿ Criptoativos"
              :subtitle="`Posição de ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="🔁 Replicar mês anterior" outlined @click="replicar" />
      <Button label="Nova posição" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column header="Ativo">
      <template #body="{ data }">
        <span class="ativo-tag">
          <strong>{{ mapAtivo.get(data.ativo_id)?.ticker || "—" }}</strong>
          <span class="nome-ativo">{{ mapAtivo.get(data.ativo_id)?.nome }}</span>
        </span>
      </template>
    </Column>
    <Column header="Quantidade" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ Number(data.quantidade).toLocaleString("pt-BR", { maximumFractionDigits: 8 }) }}</span>
      </template>
    </Column>
    <Column header="Saldo BRL" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ fmtBRL(data.saldo_brl) }}</span>
      </template>
    </Column>
    <Column header="Saldo USD" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">{{ fmtUSD(data.saldo_usd) }}</span>
      </template>
    </Column>
    <Column header="Cotação USD/BRL">
      <template #body="{ data }">
        <span class="tabular value-muted">R$ {{ Number(data.cotacao_usd_brl).toFixed(4) }}</span>
      </template>
    </Column>
    <Column header="Variação vs. mês ant.">
      <template #body="{ data }">
        <span :class="classeVariacao(data.variacao_pct)" class="variacao">
          <TrendingUp v-if="data.variacao_pct !== null && data.variacao_pct > 0" :size="14" />
          <TrendingDown v-else-if="data.variacao_pct !== null && data.variacao_pct < 0" :size="14" />
          <Minus v-else :size="14" />
          {{ fmtPct(data.variacao_pct) }}
        </span>
      </template>
    </Column>
    <Column header="Ações" style="width: 7rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-resumo">
        <div><span class="lbl">Total BRL:</span>
          <strong class="tabular">{{ fmtBRL(totais.brl) }}</strong>
        </div>
        <div><span class="lbl">Total USD:</span>
          <strong class="tabular value-muted">{{ fmtUSD(totais.usd) }}</strong>
        </div>
        <div><span class="lbl">Ativos:</span>
          <strong>{{ totais.qtd }}</strong>
        </div>
      </div>
    </template>
  </DataTable>

  <Dialog v-model:visible="dialogVisivel"
          :header="editando ? 'Editar posição' : 'Nova posição'"
          modal :style="{ width: '500px' }">
    <div class="form">
      <label>Ativo</label>
      <Dropdown v-model="form.ativo_id" :options="ativosCripto"
                optionLabel="ticker" optionValue="id"
                placeholder="Selecione..." />

      <label>Quantidade</label>
      <InputNumber v-model="form.quantidade"
                   :minFractionDigits="0" :maxFractionDigits="8"
                   :min="0" locale="pt-BR" />

      <label>Saldo em BRL</label>
      <InputNumber v-model="form.saldo_brl"
                   mode="currency" currency="BRL" locale="pt-BR" />

      <label>Cotação USD/BRL (opcional)</label>
      <InputNumber v-model="form.cotacao_usd_brl"
                   :minFractionDigits="4" :maxFractionDigits="4"
                   :min="0" locale="pt-BR"
                   placeholder="Deixe vazio para buscar no BCB" />
      <small class="hint">💡 Se vazio, busca cotação automaticamente</small>
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
.hint { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
.ativo-tag { display: inline-flex; align-items: center; gap: 8px; }
.nome-ativo { color: var(--text-muted); font-size: var(--text-sm); }
.variacao { display: inline-flex; align-items: center; gap: 4px; font-weight: 500; }
.var-positiva { color: var(--success); }
.var-negativa { color: var(--danger); }
.var-neutra { color: var(--text-muted); }
.footer-resumo {
  display: flex; justify-content: flex-end; gap: var(--space-6);
  padding: var(--space-2) 0; font-size: var(--text-sm);
}
.footer-resumo .lbl { color: var(--text-muted); margin-right: 6px; }
</style>
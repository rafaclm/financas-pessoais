<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  aportesService, type Aporte,
  type ResumoMensalAportes, type ResumoPorAtivo
} from "@/services/aportes"
import { ativosService, type Ativo } from "@/services/ativos"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import DatePicker from "primevue/datepicker"
import Panel from "primevue/panel"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref([] as Aporte[])
const ativos = ref([] as Ativo[])
const resumoMensal = ref([] as ResumoMensalAportes[])
const porAtivo = ref([] as ResumoPorAtivo[])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Aporte> & { dataObj?: Date }>({})

const filtroAtivo = ref(null as number | null)
const filtroTipo = ref(null as string | null)

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
const tiposOp = [
  { label: "🛒 Compra", value: "compra" },
  { label: "💵 Venda", value: "venda" }
]
const moedas = [{ label: "BRL", value: "BRL" }, { label: "USD", value: "USD" }]

const mapAtivo = computed(() => {
  const m = new Map<number, Ativo>()
  ativos.value.forEach(a => m.set(a.id, a))
  return m
})

const listaFiltrada = computed(() => {
  return lista.value.filter(a => {
    if (filtroAtivo.value && a.ativo_id !== filtroAtivo.value) return false
    if (filtroTipo.value && a.tipo_operacao !== filtroTipo.value) return false
    return true
  })
})

const totalMes = computed(() => {
  const totalBRL = listaFiltrada.value.reduce((acc, a) => acc + Number(a.valor_total_brl), 0)
  const totalCompras = listaFiltrada.value.filter(a => a.tipo_operacao === "compra")
    .reduce((acc, a) => acc + Number(a.valor_total_brl), 0)
  const totalVendas = listaFiltrada.value.filter(a => a.tipo_operacao === "venda")
    .reduce((acc, a) => acc + Number(a.valor_total_brl), 0)
  return { qtd: listaFiltrada.value.length, valor: totalBRL, compras: totalCompras, vendas: totalVendas }
})

const valorTotalCalc = computed(() => {
  const qtd = Number(form.value.quantidade || 0)
  const preco = Number(form.value.preco_unitario || 0)
  const taxas = Number(form.value.taxas || 0)
  return qtd * preco + taxas
})

const valorTotalBRLCalc = computed(() => {
  if (form.value.moeda === "USD") {
    const cot = Number(form.value.cotacao_usd_brl || 0)
    return valorTotalCalc.value * cot
  }
  return valorTotalCalc.value
})

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)
const fmtUSD = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v || 0)
const fmtData = (d: string) => {
  if (!d) return "—"
  const [a, m, dia] = d.split("-")
  return `${dia}/${m}/${a}`
}

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [lst, ats, rm, pa] = await Promise.all([
      aportesService.listar({ ano_id: periodo.anoIdSelecionado, mes: periodo.mesSelecionado }),
      ativos.value.length ? Promise.resolve(ativos.value) : ativosService.listar({ apenas_ativos: true }),
      aportesService.resumoMensal(periodo.anoIdSelecionado),
      aportesService.porAtivo(periodo.anoIdSelecionado),
    ])
    lista.value = lst
    if (!ativos.value.length) ativos.value = ats
    resumoMensal.value = rm
    porAtivo.value = pa
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })

function abrirNovo() {
  editando.value = null
  const hoje = new Date()
  const dataPadrao = new Date(
    periodo.anoAtual?.ano || hoje.getFullYear(),
    periodo.mesSelecionado - 1,
    Math.min(hoje.getDate(), 28)
  )
  form.value = {
    ano_id: periodo.anoIdSelecionado!,
    mes: periodo.mesSelecionado,
    dataObj: dataPadrao,
    ativo_id: ativos.value[0]?.id,
    tipo_operacao: "compra",
    quantidade: 0,
    preco_unitario: 0,
    taxas: 0,
    moeda: "BRL",
    descricao: "",
    cotacao_usd_brl: null,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: Aporte) {
  editando.value = row.id
  form.value = { ...row, dataObj: new Date(row.data + "T12:00:00") }
  dialogVisivel.value = true
}

async function salvar() {
  if (!form.value.dataObj) {
    toast.add({ severity: "warn", summary: "Data obrigatória", life: 3000 })
    return
  }
  const d = form.value.dataObj
  const dataStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
  const mesDaData = d.getMonth() + 1
  const anoDaData = d.getFullYear()
  const anoCorrespondente = periodo.anosDisponiveis.find(a => a.ano === anoDaData)
  if (!anoCorrespondente) {
    toast.add({
      severity: "warn", summary: "Ano não cadastrado",
      detail: `O ano ${anoDaData} não está cadastrado. Cadastre em Cadastros > Anos.`, life: 5000
    })
    return
  }
  const payload: any = {
    ...form.value,
    data: dataStr,
    mes: mesDaData,
    ano_id: anoCorrespondente.id,
  }
  delete payload.dataObj
  if (payload.moeda === "BRL") payload.cotacao_usd_brl = null

  try {
    if (editando.value) await aportesService.atualizar(editando.value, payload)
    else await aportesService.criar(payload)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: Aporte) {
  if (!confirm(`Excluir aporte de ${row.tipo_operacao} de ${fmtBRL(row.valor_total_brl)}?`)) return
  try {
    await aportesService.excluir(row.id)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

function flagPorGeografia(geo: string) {
  if (geo === "BR") return "🇧🇷"
  if (geo === "EUA") return "🇺🇸"
  return "🌐"
}
</script>

<template>
  <PageHeader title="🛒 Aportes em Bolsa"
              :subtitle="`Operações de ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="Novo aporte" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <div class="filtros">
    <div class="filtro-grupo">
      <label>Ativo</label>
      <Dropdown v-model="filtroAtivo" :options="ativos"
                optionLabel="ticker" optionValue="id"
                placeholder="Todos" showClear
                :pt="{ root: { style: 'min-width: 160px' } }" />
    </div>
    <div class="filtro-grupo">
      <label>Operação</label>
      <Dropdown v-model="filtroTipo" :options="tiposOp"
                optionLabel="label" optionValue="value"
                placeholder="Todas" showClear
                :pt="{ root: { style: 'min-width: 160px' } }" />
    </div>
  </div>

  <DataTable :value="listaFiltrada" :loading="carregando" stripedRows :paginator="true" :rows="25">
    <Column header="Data" sortable sortField="data">
      <template #body="{ data }">{{ fmtData(data.data) }}</template>
    </Column>
    <Column header="Ativo">
      <template #body="{ data }">
        <span class="ativo-tag">
          {{ flagPorGeografia(mapAtivo.get(data.ativo_id)?.geografia || "") }}
          <strong>{{ mapAtivo.get(data.ativo_id)?.ticker || "—" }}</strong>
        </span>
      </template>
    </Column>
    <Column header="Operação">
      <template #body="{ data }">
        <Tag :severity="data.tipo_operacao === 'compra' ? 'success' : 'warning'"
             :value="data.tipo_operacao === 'compra' ? '🛒 Compra' : '💵 Venda'" />
      </template>
    </Column>
    <Column header="Quantidade" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ Number(data.quantidade).toLocaleString("pt-BR") }}</span>
      </template>
    </Column>
    <Column header="Preço" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">
          {{ data.moeda === "USD" ? fmtUSD(data.preco_unitario) : fmtBRL(data.preco_unitario) }}
        </span>
      </template>
    </Column>
    <Column header="Moeda / Cotação">
      <template #body="{ data }">
        <div class="moeda-info">
          <Tag :value="data.moeda" :severity="data.moeda === 'USD' ? 'info' : 'secondary'" />
          <span v-if="data.cotacao_usd_brl" class="cotacao-tag">
            R$ {{ Number(data.cotacao_usd_brl).toFixed(4) }}
          </span>
        </div>
      </template>
    </Column>
    <Column header="Total (BRL)" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular"
              :class="data.tipo_operacao === 'compra' ? 'value-negative' : 'value-positive'">
          {{ fmtBRL(data.valor_total_brl) }}
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
        <div><span class="lbl">🛒 Compras:</span>
          <strong class="tabular value-negative">{{ fmtBRL(totalMes.compras) }}</strong>
        </div>
        <div><span class="lbl">💵 Vendas:</span>
          <strong class="tabular value-positive">{{ fmtBRL(totalMes.vendas) }}</strong>
        </div>
        <div><span class="lbl">Total operações:</span>
          <strong>{{ totalMes.qtd }}</strong>
        </div>
      </div>
    </template>
  </DataTable>

  <Panel header="📅 Resumo mensal do ano" toggleable :collapsed="true" class="painel-resumo">
    <DataTable v-if="resumoMensal.length" :value="resumoMensal" stripedRows>
      <Column header="Mês">
        <template #body="{ data }">{{ MESES[data.mes - 1] }}</template>
      </Column>
      <Column header="🛒 Compras" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular value-negative">{{ fmtBRL(data.total_compras_brl) }}</span>
          <span class="qtd-tag">({{ data.qtd_compras }})</span>
        </template>
      </Column>
      <Column header="💵 Vendas" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular value-positive">{{ fmtBRL(data.total_vendas_brl) }}</span>
          <span class="qtd-tag">({{ data.qtd_vendas }})</span>
        </template>
      </Column>
      <Column header="Total ops" style="text-align: center">
        <template #body="{ data }">{{ data.qtd_operacoes }}</template>
      </Column>
    </DataTable>
    <div v-else class="vazio">Sem dados anuais ainda.</div>
  </Panel>

  <Panel header="📊 Resumo anual por ativo" toggleable :collapsed="true" class="painel-resumo">
    <DataTable v-if="porAtivo.length" :value="porAtivo" stripedRows>
      <Column header="Ativo">
        <template #body="{ data }">
          <span class="ativo-tag">
            {{ flagPorGeografia(mapAtivo.get(data.ativo_id)?.geografia || "") }}
            <strong>{{ data.ticker }}</strong>
          </span>
        </template>
      </Column>
      <Column field="nome" header="Nome" />
      <Column header="Operações" style="text-align: center">
        <template #body="{ data }">{{ data.qtd_operacoes }}</template>
      </Column>
      <Column header="Total Aportado (BRL)" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular">{{ fmtBRL(data.total_brl) }}</span>
        </template>
      </Column>
    </DataTable>
    <div v-else class="vazio">Sem aportes no ano.</div>
  </Panel>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar aporte' : 'Novo aporte'"
          modal :style="{ width: '560px' }">
    <div class="form">
      <label>📅 Data da operação</label>
      <DatePicker v-model="form.dataObj" dateFormat="dd/mm/yy" showIcon />

      <label>Ativo</label>
      <Dropdown v-model="form.ativo_id" :options="ativos"
                optionLabel="ticker" optionValue="id"
                :filter="true" filterPlaceholder="Buscar ativo..."
                placeholder="Selecione..." />

      <label>Tipo de operação</label>
      <Dropdown v-model="form.tipo_operacao" :options="tiposOp"
                optionLabel="label" optionValue="value" />

      <div class="row">
        <div class="col">
          <label>Quantidade</label>
          <InputNumber v-model="form.quantidade" :minFractionDigits="0"
                       :maxFractionDigits="8" :min="0" locale="pt-BR" />
        </div>
        <div class="col">
          <label>Preço unitário</label>
          <InputNumber v-model="form.preco_unitario" :minFractionDigits="2"
                       :maxFractionDigits="8" :min="0" locale="pt-BR" />
        </div>
      </div>

      <div class="row">
        <div class="col">
          <label>Taxas</label>
          <InputNumber v-model="form.taxas" mode="currency"
                       :currency="form.moeda" locale="pt-BR" />
        </div>
        <div class="col">
          <label>Moeda</label>
          <Dropdown v-model="form.moeda" :options="moedas"
                    optionLabel="label" optionValue="value" />
        </div>
      </div>

      <template v-if="form.moeda === 'USD'">
        <label>Cotação USD/BRL (opcional)</label>
        <InputNumber v-model="form.cotacao_usd_brl"
                     :minFractionDigits="4" :maxFractionDigits="4"
                     :min="0" locale="pt-BR"
                     placeholder="Deixe vazio para buscar automaticamente no BCB" />
        <small class="hint">💡 Se vazio, o sistema busca a cotação no Banco Central</small>
      </template>

      <div class="totais-calc">
        <div>
          <span class="lbl">Total {{ form.moeda }}:</span>
          <strong class="tabular">
            {{ form.moeda === "USD" ? fmtUSD(valorTotalCalc) : fmtBRL(valorTotalCalc) }}
          </strong>
        </div>
        <div v-if="form.moeda === 'USD' && form.cotacao_usd_brl">
          <span class="lbl">Total BRL:</span>
          <strong class="tabular">{{ fmtBRL(valorTotalBRLCalc) }}</strong>
        </div>
      </div>

      <label>Descrição (opcional)</label>
      <InputText v-model="form.descricao" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogVisivel = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvar" />
    </template>
  </Dialog>
</template>

<style scoped>
.filtros { display: flex; gap: var(--space-4); margin-bottom: var(--space-4); }
.filtro-grupo { display: flex; flex-direction: column; gap: var(--space-1); }
.filtro-grupo label { font-size: var(--text-xs); color: var(--text-muted); text-transform: uppercase; }
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
.row { display: flex; gap: var(--space-3); }
.col { display: flex; flex-direction: column; flex: 1; gap: var(--space-2); }
.hint { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
.totais-calc {
  margin-top: var(--space-3); padding: var(--space-3);
  background: var(--bg-elevated); border-radius: var(--radius-md);
  display: flex; justify-content: space-between; gap: var(--space-4); font-size: var(--text-sm);
}
.totais-calc .lbl { color: var(--text-muted); margin-right: 6px; }
.ativo-tag { display: inline-flex; align-items: center; gap: 6px; }
.moeda-info { display: flex; align-items: center; gap: var(--space-2); }
.cotacao-tag { font-size: var(--text-xs); color: var(--text-muted); }
.qtd-tag { color: var(--text-muted); font-size: var(--text-xs); margin-left: 4px; }
.footer-resumo {
  display: flex; justify-content: flex-end; gap: var(--space-6);
  padding: var(--space-2) 0; font-size: var(--text-sm);
}
.footer-resumo .lbl { color: var(--text-muted); margin-right: 6px; }
.painel-resumo { margin-top: var(--space-6); }
.vazio { padding: var(--space-6); text-align: center; color: var(--text-muted); }
</style>
<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  proventosService, type Provento,
  type ResumoMensalProventos, type ResumoAnualProventos,
  type ResumoProventosPorAtivo
} from "@/services/proventos"
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

const lista = ref([] as Provento[])
const ativos = ref([] as Ativo[])
const resumoMensal = ref([] as ResumoMensalProventos[])
const resumoAnual = ref(null as ResumoAnualProventos | null)
const porAtivo = ref([] as ResumoProventosPorAtivo[])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Provento> & { dataObj?: Date }>({})

const filtroAtivo = ref(null as number | null)
const filtroTipo = ref(null as string | null)

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

const tipos = [
  { label: "💵 Dividendo", value: "dividendo" },
  { label: "💼 JCP", value: "jcp" },
  { label: "📈 Rendimento", value: "rendimento" },
  { label: "₿ Juros Cripto", value: "juros_cripto" },
  { label: "📦 Outro", value: "outro" },
]
const moedas = [{ label: "BRL", value: "BRL" }, { label: "USD", value: "USD" }]

const mapAtivo = computed(() => {
  const m = new Map<number, Ativo>()
  ativos.value.forEach(a => m.set(a.id, a))
  return m
})

const listaFiltrada = computed(() => {
  return lista.value.filter(p => {
    if (filtroAtivo.value && p.ativo_id !== filtroAtivo.value) return false
    if (filtroTipo.value && p.tipo !== filtroTipo.value) return false
    return true
  })
})

const totalMes = computed(() =>
  listaFiltrada.value.reduce((acc, p) => acc + Number(p.valor_liquido_brl), 0)
)

const valorBRLCalc = computed(() => {
  if (form.value.moeda === "USD") {
    return Number(form.value.valor_liquido || 0) * Number(form.value.cotacao_usd_brl || 0)
  }
  return Number(form.value.valor_liquido || 0)
})

// 🆕 Valor por cota — calculado em tempo real no formulário
const valorPorCotaCalc = computed(() => {
  const qtd = Number(form.value.quantidade_cotas || 0)
  const liq = Number(form.value.valor_liquido || 0)
  return qtd > 0 ? liq / qtd : 0
})

// 🆕 Helper para calcular valor/cota de uma linha da listagem
function valorPorCotaLista(p: Provento): number {
  if (!p.quantidade_cotas || p.quantidade_cotas <= 0) return 0
  return Number(p.valor_liquido) / Number(p.quantidade_cotas)
}

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)
const fmtUSD = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v || 0)
const fmtData = (d: string) => {
  if (!d) return "—"
  const [a, m, dia] = d.split("-")
  return `${dia}/${m}/${a}`
}

const labelTipo = (t: string) => tipos.find(x => x.value === t)?.label || t

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [lst, ats, rm, ra, pa] = await Promise.all([
      proventosService.listar({
        ano_id: periodo.anoIdSelecionado,
        mes: periodo.mesSelecionado
      }),
      ativos.value.length ? Promise.resolve(ativos.value) : ativosService.listar({ apenas_ativos: true }),
      proventosService.resumoMensal(periodo.anoIdSelecionado),
      proventosService.resumoAnual(periodo.anoIdSelecionado),
      proventosService.porAtivo(periodo.anoIdSelecionado),
    ])
    lista.value = lst
    if (!ativos.value.length) ativos.value = ats
    resumoMensal.value = rm
    resumoAnual.value = ra
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
    tipo: "dividendo",
    valor_bruto: 0,
    valor_liquido: 0,
    quantidade_cotas: null,
    moeda: "BRL",
    descricao: "",
    cotacao_usd_brl: null,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: Provento) {
  editando.value = row.id
  form.value = {
    ...row,
    dataObj: new Date(row.data + "T12:00:00"),
  }
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
      severity: "warn",
      summary: "Ano não cadastrado",
      detail: `Cadastre o ano ${anoDaData} em Cadastros > Anos.`,
      life: 5000
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
  // Conta foi removida - força null
  payload.conta_id = null
  if (payload.moeda === "BRL") payload.cotacao_usd_brl = null
  // quantidade_cotas: se vier 0 ou vazio, manda null (campo opcional)
  if (!payload.quantidade_cotas || payload.quantidade_cotas <= 0) {
    payload.quantidade_cotas = null
  }

  try {
    if (editando.value)
      await proventosService.atualizar(editando.value, payload)
    else
      await proventosService.criar(payload)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: Provento) {
  if (!confirm(`Excluir provento de ${fmtBRL(row.valor_liquido_brl)}?`)) return
  try {
    await proventosService.excluir(row.id)
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
  <PageHeader title="💎 Proventos"
              :subtitle="`Recebimentos de ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="Novo provento" icon="pi pi-plus" @click="abrirNovo" />
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
      <label>Tipo</label>
      <Dropdown v-model="filtroTipo" :options="tipos"
                optionLabel="label" optionValue="value"
                placeholder="Todos" showClear
                :pt="{ root: { style: 'min-width: 180px' } }" />
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
    <Column header="Tipo">
      <template #body="{ data }">{{ labelTipo(data.tipo) }}</template>
    </Column>
    <!-- 🆕 Coluna Qtd Cotas -->
    <Column header="Qtd Cotas" style="text-align: right">
      <template #body="{ data }">
        <span v-if="data.quantidade_cotas" class="tabular">
          {{ Number(data.quantidade_cotas).toLocaleString("pt-BR", { maximumFractionDigits: 8 }) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <!-- 🆕 Coluna Valor/Cota (calculada) -->
    <Column header="Valor/Cota" style="text-align: right">
      <template #body="{ data }">
        <span v-if="data.quantidade_cotas && data.quantidade_cotas > 0"
              class="tabular value-muted">
          {{ data.moeda === "USD"
            ? fmtUSD(valorPorCotaLista(data))
            : fmtBRL(valorPorCotaLista(data)) }}
        </span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Bruto" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">
          {{ data.moeda === "USD" ? fmtUSD(data.valor_bruto) : fmtBRL(data.valor_bruto) }}
        </span>
      </template>
    </Column>
    <Column header="Líquido" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-positive">
          {{ data.moeda === "USD" ? fmtUSD(data.valor_liquido) : fmtBRL(data.valor_liquido) }}
        </span>
      </template>
    </Column>
    <Column header="Moeda">
      <template #body="{ data }">
        <Tag :value="data.moeda" :severity="data.moeda === 'USD' ? 'info' : 'secondary'" />
      </template>
    </Column>
    <Column header="Total (BRL)" style="text-align: right">
      <template #body="{ data }">
        <strong class="tabular value-positive">{{ fmtBRL(data.valor_liquido_brl) }}</strong>
      </template>
    </Column>
    <Column header="Ações" style="width: 7rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total do mês: <strong class="tabular value-positive">{{ fmtBRL(totalMes) }}</strong>
        ({{ listaFiltrada.length }} recebimento{{ listaFiltrada.length !== 1 ? "s" : "" }})
      </div>
    </template>
  </DataTable>

  <Panel header="💚 Renda passiva mensal" toggleable :collapsed="false" class="painel-resumo">
    <div v-if="resumoAnual" class="cards-anuais">
      <div class="card-anual">
        <span class="lbl">Total acumulado no ano</span>
        <strong class="tabular value-positive">{{ fmtBRL(resumoAnual.total_acumulado_brl) }}</strong>
      </div>
      <div class="card-anual">
        <span class="lbl">Média mensal</span>
        <strong class="tabular">{{ fmtBRL(resumoAnual.media_mensal_brl) }}</strong>
      </div>
      <div class="card-anual">
        <span class="lbl">Maior mês</span>
        <strong>{{ resumoAnual.maior_mes ? MESES[resumoAnual.maior_mes - 1] : "—" }}</strong>
        <span class="hint">{{ fmtBRL(resumoAnual.maior_valor) }}</span>
      </div>
      <div class="card-anual">
        <span class="lbl">Total recebimentos</span>
        <strong>{{ resumoAnual.qtd_total }}</strong>
      </div>
    </div>

    <DataTable v-if="resumoMensal.length" :value="resumoMensal" stripedRows class="tabela-rp">
      <Column header="Mês">
        <template #body="{ data }">
          <span :class="{ destacar: data.mes === resumoAnual?.maior_mes }">
            {{ MESES[data.mes - 1] }}
            <span v-if="data.mes === resumoAnual?.maior_mes" class="star">⭐</span>
          </span>
        </template>
      </Column>
      <Column header="Recebimentos" style="text-align: center">
        <template #body="{ data }">{{ data.qtd }}</template>
      </Column>
      <Column header="Total (BRL)" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular value-positive">{{ fmtBRL(data.total_brl) }}</span>
        </template>
      </Column>
    </DataTable>
    <div v-else class="vazio">Sem proventos no ano ainda.</div>
  </Panel>

  <Panel header="📊 Proventos por ativo (anual)" toggleable :collapsed="true" class="painel-resumo">
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
      <Column header="Recebimentos" style="text-align: center">
        <template #body="{ data }">{{ data.qtd }}</template>
      </Column>
      <Column header="Total (BRL)" style="text-align: right">
        <template #body="{ data }">
          <strong class="tabular value-positive">{{ fmtBRL(data.total_brl) }}</strong>
        </template>
      </Column>
    </DataTable>
    <div v-else class="vazio">Sem dados.</div>
  </Panel>

  <Dialog v-model:visible="dialogVisivel" :header="editando ? 'Editar provento' : 'Novo provento'"
          modal :style="{ width: '560px' }">
    <div class="form">
      <label>📅 Data de pagamento</label>
      <DatePicker v-model="form.dataObj" dateFormat="dd/mm/yy" showIcon />

      <label>Ativo</label>
      <Dropdown v-model="form.ativo_id" :options="ativos"
                optionLabel="ticker" optionValue="id"
                :filter="true" filterPlaceholder="Buscar..."
                placeholder="Selecione..." />

      <label>Tipo</label>
      <Dropdown v-model="form.tipo" :options="tipos"
                optionLabel="label" optionValue="value" />

      <div class="row">
        <div class="col">
          <label>Valor bruto</label>
          <InputNumber v-model="form.valor_bruto"
                       mode="currency" :currency="form.moeda" locale="pt-BR" />
        </div>
        <div class="col">
          <label>Valor líquido</label>
          <InputNumber v-model="form.valor_liquido"
                       mode="currency" :currency="form.moeda" locale="pt-BR" />
        </div>
      </div>

      <label>Moeda</label>
      <Dropdown v-model="form.moeda" :options="moedas"
                optionLabel="label" optionValue="value" />

      <!-- 🆕 Quantidade de cotas (agora persistida no banco!) -->
      <label>Quantidade de cotas no momento (opcional)</label>
      <InputNumber v-model="form.quantidade_cotas"
                   :minFractionDigits="0" :maxFractionDigits="8"
                   :min="0" locale="pt-BR"
                   placeholder="Ex.: 100" />
      <small class="hint">
        💡 Informe a quantidade de cotas que você tinha quando recebeu o provento.
        O valor por cota será calculado e exibido na listagem.
      </small>

      <div v-if="(form.quantidade_cotas || 0) > 0 && (form.valor_liquido || 0) > 0"
           class="valor-cota-calc">
        <span class="lbl">💰 Valor por cota:</span>
        <strong class="tabular">
          {{ form.moeda === "USD" ? fmtUSD(valorPorCotaCalc) : fmtBRL(valorPorCotaCalc) }}
        </strong>
      </div>

      <template v-if="form.moeda === 'USD'">
        <label>Cotação USD/BRL (opcional)</label>
        <InputNumber v-model="form.cotacao_usd_brl"
                     :minFractionDigits="4" :maxFractionDigits="4"
                     :min="0" locale="pt-BR"
                     placeholder="Deixe vazio para buscar no BCB" />
        <small class="hint">💡 Se vazio, busca cotação automaticamente</small>
      </template>

      <div v-if="form.moeda === 'USD' && form.cotacao_usd_brl" class="totais-calc">
        <span class="lbl">Valor líquido em BRL:</span>
        <strong class="tabular">{{ fmtBRL(valorBRLCalc) }}</strong>
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
  display: flex; justify-content: space-between; font-size: var(--text-sm);
}
.totais-calc .lbl { color: var(--text-muted); margin-right: 6px; }
.valor-cota-calc {
  margin-top: var(--space-2); padding: var(--space-3);
  background: var(--bg-elevated); border-radius: var(--radius-md);
  display: flex; justify-content: space-between; font-size: var(--text-sm);
  border-left: 3px solid var(--brand-accent);
}
.valor-cota-calc .lbl { color: var(--text-muted); }
.ativo-tag { display: inline-flex; align-items: center; gap: 6px; }
.footer-total { text-align: right; font-size: var(--text-base); padding: var(--space-2) 0; }
.painel-resumo { margin-top: var(--space-6); }
.vazio { padding: var(--space-6); text-align: center; color: var(--text-muted); }
.cards-anuais {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-3); margin-bottom: var(--space-4);
}
.card-anual {
  background: var(--bg-elevated); padding: var(--space-4);
  border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 4px;
}
.card-anual .lbl { font-size: var(--text-xs); color: var(--text-muted); text-transform: uppercase; }
.card-anual strong { font-size: var(--text-lg); }
.card-anual .hint { font-size: var(--text-xs); color: var(--text-muted); }
.tabela-rp { margin-top: var(--space-3); }
.destacar { font-weight: 600; }
.star { margin-left: 6px; }
</style>
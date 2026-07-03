<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import {
  combustivelService, type Combustivel, type ResumoCombustivelMes
} from "@/services/combustivel"
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
import DatePicker from "primevue/datepicker"
import Panel from "primevue/panel"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref([] as Combustivel[])
const resumo = ref([] as ResumoCombustivelMes[])
const contas = ref([] as Conta[])
const cartoes = ref([] as Cartao[])
const carregando = ref(false)

const dialogVisivel = ref(false)
const editando = ref<number | null>(null)
const form = ref<Partial<Combustivel> & { dataObj?: Date }>({})
const origemTipo = ref<"conta" | "cartao">("conta")

const ultimoVeiculo = computed(() =>
  lista.value.length > 0 ? lista.value[0].veiculo : ""
)

const precoLitroForm = computed(() => {
  const litros = Number(form.value.litros || 0)
  const valor = Number(form.value.valor_total || 0)
  return litros > 0 ? valor / litros : 0
})

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

const totalMes = computed(() => ({
  valor: lista.value.reduce((acc, r) => acc + Number(r.valor_total), 0),
  litros: lista.value.reduce((acc, r) => acc + Number(r.litros), 0),
  qtd: lista.value.length,
}))

const precoMedioMes = computed(() =>
  totalMes.value.litros > 0 ? totalMes.value.valor / totalMes.value.litros : 0
)

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

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)
const fmtLitros = (v: number) =>
  v.toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 })
const fmtData = (d: string) => {
  if (!d) return "—"
  const [a, m, dia] = d.split("-")
  return `${dia}/${m}/${a}`
}

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [lst, res, cts, cards] = await Promise.all([
      combustivelService.listar({ ano_id: periodo.anoIdSelecionado, mes: periodo.mesSelecionado }),
      combustivelService.resumoAnual(periodo.anoIdSelecionado),
      contas.value.length ? Promise.resolve(contas.value) : contasService.listar(true),
      cartoes.value.length ? Promise.resolve(cartoes.value) : cartoesService.listar(true),
    ])
    lista.value = lst
    resumo.value = res
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
  origemTipo.value = "conta"
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
    litros: 0,
    valor_total: 0,
    posto: "",
    veiculo: ultimoVeiculo.value || "",
    conta_id: contas.value[0]?.id,
    cartao_id: null,
  }
  dialogVisivel.value = true
}

function abrirEdicao(row: Combustivel) {
  editando.value = row.id
  origemTipo.value = row.cartao_id ? "cartao" : "conta"
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
      severity: "warn", summary: "Ano não cadastrado",
      detail: `Cadastre o ano ${anoDaData} em Cadastros > Anos.`, life: 5000
    })
    return
  }

  if (origemTipo.value === "conta") form.value.cartao_id = null
  else form.value.conta_id = null

  const payload: any = {
    ...form.value,
    data: dataStr,
    mes: mesDaData,
    ano_id: anoCorrespondente.id,
  }
  delete payload.dataObj

  try {
    if (editando.value) await combustivelService.atualizar(editando.value, payload)
    else await combustivelService.criar(payload)
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogVisivel.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(row: Combustivel) {
  if (!confirm(`Excluir abastecimento de ${fmtBRL(row.valor_total)}?`)) return
  try {
    await combustivelService.excluir(row.id)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="⛽ Combustível" :subtitle="`Abastecimentos de ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="Novo abastecimento" icon="pi pi-plus" @click="abrirNovo" />
    </template>
  </PageHeader>

  <DataTable :value="lista" :loading="carregando" stripedRows>
    <Column header="Data" sortable sortField="data">
      <template #body="{ data }">{{ fmtData(data.data) }}</template>
    </Column>
    <Column field="posto" header="Posto">
      <template #body="{ data }">{{ data.posto || "—" }}</template>
    </Column>
    <Column header="Litros" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular">{{ fmtLitros(data.litros) }} L</span>
      </template>
    </Column>
    <Column header="R$/litro" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-muted">{{ fmtBRL(data.preco_litro) }}</span>
      </template>
    </Column>
    <Column field="veiculo" header="Veículo">
      <template #body="{ data }">{{ data.veiculo || "—" }}</template>
    </Column>
    <Column header="Pago com">
      <template #body="{ data }">
        <span v-if="data.conta_id">👛 {{ mapConta.get(data.conta_id) || "—" }}</span>
        <span v-else-if="data.cartao_id">💳 {{ mapCartao.get(data.cartao_id) || "—" }}</span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Total" style="text-align: right">
      <template #body="{ data }">
        <span class="tabular value-negative">{{ fmtBRL(data.valor_total) }}</span>
      </template>
    </Column>
    <Column header="Ações" style="width: 8rem">
      <template #body="{ data }">
        <Button icon="pi pi-pencil" text @click="abrirEdicao(data)" />
        <Button icon="pi pi-trash" severity="danger" text @click="excluir(data)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-resumo">
        <div><span class="lbl">Total do mês:</span>
          <strong class="tabular value-negative">{{ fmtBRL(totalMes.valor) }}</strong>
        </div>
        <div><span class="lbl">Litros:</span>
          <strong class="tabular">{{ fmtLitros(totalMes.litros) }} L</strong>
        </div>
        <div><span class="lbl">R$/litro médio:</span>
          <strong class="tabular">{{ fmtBRL(precoMedioMes) }}</strong>
        </div>
        <div><span class="lbl">Abastecimentos:</span>
          <strong>{{ totalMes.qtd }}</strong>
        </div>
      </div>
    </template>
  </DataTable>

  <Panel header="📊 Resumo do ano" toggleable :collapsed="true" class="painel-resumo">
    <div v-if="resumo.length === 0" class="vazio">
      Sem dados anuais ainda. Comece registrando seus abastecimentos!
    </div>
    <DataTable v-else :value="resumo" stripedRows>
      <Column header="Mês">
        <template #body="{ data }">{{ MESES[data.mes - 1] }}</template>
      </Column>
      <Column header="Abastecimentos" style="text-align: center">
        <template #body="{ data }">{{ data.qtd_abastecimentos }}</template>
      </Column>
      <Column header="Total litros" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular">{{ fmtLitros(data.total_litros) }} L</span>
        </template>
      </Column>
      <Column header="Total gasto" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular value-negative">{{ fmtBRL(data.total_valor) }}</span>
        </template>
      </Column>
      <Column header="R$/litro médio" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular value-muted">{{ fmtBRL(data.preco_medio_litro) }}</span>
        </template>
      </Column>
    </DataTable>
  </Panel>

  <Dialog v-model:visible="dialogVisivel"
          :header="editando ? 'Editar abastecimento' : 'Novo abastecimento'"
          modal :style="{ width: '540px' }">
    <div class="form">
      <label>📅 Data do abastecimento</label>
      <DatePicker v-model="form.dataObj" dateFormat="dd/mm/yy" showIcon />

      <label>Posto (opcional)</label>
      <InputText v-model="form.posto" placeholder="Ex.: Shell, Ipiranga..." />

      <label>Veículo (opcional)</label>
      <InputText v-model="form.veiculo" placeholder="Ex.: Corolla" />

      <div class="row">
        <div class="col">
          <label>Litros</label>
          <InputNumber v-model="form.litros" :minFractionDigits="3" :maxFractionDigits="3"
                       :min="0" locale="pt-BR" />
        </div>
        <div class="col">
          <label>Valor total (R$)</label>
          <InputNumber v-model="form.valor_total" mode="currency" currency="BRL" locale="pt-BR" />
        </div>
      </div>

      <div class="preco-calc">
        💡 R$/litro: <strong class="tabular">{{ fmtBRL(precoLitroForm) }}</strong>
      </div>

      <label>Pago com</label>
      <Dropdown v-model="origemTipo"
                :options="[{label:'Conta', value:'conta'}, {label:'Cartão', value:'cartao'}]"
                optionLabel="label" optionValue="value" />

      <template v-if="origemTipo === 'conta'">
        <label>Conta</label>
        <Dropdown v-model="form.conta_id" :options="contas"
                  optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      </template>
      <template v-else>
        <label>Cartão</label>
        <Dropdown v-model="form.cartao_id" :options="cartoes"
                  optionLabel="nome" optionValue="id" placeholder="Selecione..." />
      </template>
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
.row { display: flex; gap: var(--space-3); }
.col { display: flex; flex-direction: column; flex: 1; gap: var(--space-2); }
.preco-calc {
  margin-top: var(--space-2); padding: var(--space-3);
  background: var(--bg-elevated); border-radius: var(--radius-md);
  font-size: var(--text-sm); color: var(--text-secondary);
}
.footer-resumo {
  display: flex; justify-content: flex-end; gap: var(--space-6);
  padding: var(--space-2) 0; font-size: var(--text-sm);
}
.footer-resumo .lbl { color: var(--text-muted); margin-right: 6px; }
.painel-resumo { margin-top: var(--space-6); }
.vazio { padding: var(--space-6); text-align: center; color: var(--text-muted); }
</style>
<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import { saldosContasService } from "@/services/saldosContas"
import type { SaldoConta } from "@/services/saldosContas"
import { contasService } from "@/services/contas"
import type { Conta } from "@/services/contas"
import { instituicoesService } from "@/services/instituicoes"
import type { Instituicao } from "@/services/instituicoes"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import InputNumber from "primevue/inputnumber"
import PageHeader from "@/components/PageHeader.vue"

const periodo = usePeriodoStore()
const toast = useToast()

const lista = ref([] as SaldoConta[])
const contas = ref([] as Conta[])
const instituicoes = ref([] as Instituicao[])
const carregando = ref(false)
const salvando = ref(false)

const edicao = ref({} as Record<number, { saldo: number; cotacao_usd_brl: number | null }>)

const totalBRL = computed(() =>
  lista.value.reduce((acc, s) => acc + Number(s.saldo_brl), 0)
)

const mapInstituicao = computed(() => {
  const m = new Map<number, Instituicao>()
  instituicoes.value.forEach(i => m.set(i.id, i))
  return m
})

const linhasMontadas = computed(() => {
  return contas.value.map(c => {
    const existente = lista.value.find(s => s.conta_id === c.id)
    const edit = edicao.value[c.id]
    const inst = mapInstituicao.value.get(c.instituicao_id)
    return {
      conta: c,
      instituicao: inst,
      existente,
      saldo: edit?.saldo ?? Number(existente?.saldo ?? 0),
      cotacao: edit?.cotacao_usd_brl ?? existente?.cotacao_usd_brl ?? null,
      saldo_brl: existente?.saldo_brl ?? 0,
    }
  })
})

const fmtBRL = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v || 0)

// 🆕 Classe CSS para barra colorida por instituição
function classeBarra(instNome: string | undefined): string {
  if (!instNome) return "linha-com-barra"
  const n = instNome.toLowerCase()
  if (n.includes("itau") || n.includes("itaú")) return "linha-com-barra barra-itau"
  if (n.includes("bradesco")) return "linha-com-barra barra-bradesco"
  if (n.includes("nomad")) return "linha-com-barra barra-nomad"
  if (n.includes("avenue")) return "linha-com-barra barra-avenue"
  if (n.includes("mercado") || n.includes("livre")) return "linha-com-barra barra-mercadolivre"
  if (n.includes("caixa")) return "linha-com-barra barra-caixa"
  return "linha-com-barra"
}

async function carregar() {
  if (!periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const [saldos, cts, insts] = await Promise.all([
      saldosContasService.listar(periodo.anoIdSelecionado, periodo.mesSelecionado),
      contas.value.length ? Promise.resolve(contas.value) : contasService.listar(true),
      instituicoes.value.length ? Promise.resolve(instituicoes.value) : instituicoesService.listar(true),
    ])
    lista.value = saldos
    if (!contas.value.length) contas.value = cts
    if (!instituicoes.value.length) instituicoes.value = insts
    edicao.value = {}
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

watch(() => periodo.versao, carregar, { immediate: true })

function alterouSaldo(conta_id: number, valor: number) {
  if (!edicao.value[conta_id]) edicao.value[conta_id] = { saldo: 0, cotacao_usd_brl: null }
  edicao.value[conta_id].saldo = valor
}

function alterouCotacao(conta_id: number, valor: number) {
  if (!edicao.value[conta_id]) edicao.value[conta_id] = { saldo: 0, cotacao_usd_brl: null }
  edicao.value[conta_id].cotacao_usd_brl = valor
}

async function salvarTudo() {
  const itens = linhasMontadas.value
    .filter(l => edicao.value[l.conta.id] !== undefined || !l.existente)
    .map(l => ({
      ano_id: periodo.anoIdSelecionado!,
      mes: periodo.mesSelecionado,
      conta_id: l.conta.id,
      saldo: l.saldo,
      cotacao_usd_brl: l.cotacao,
    }))

  if (itens.length === 0) {
    toast.add({ severity: "info", summary: "Nada para salvar", life: 2500 })
    return
  }

  salvando.value = true
  try {
    await saldosContasService.lote(itens as any)
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
    const r = await saldosContasService.replicarMesAnterior(
      periodo.anoIdSelecionado!, periodo.mesSelecionado
    )
    toast.add({ severity: "success", summary: "Replicado", detail: r.mensagem, life: 4000 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  }
}

async function excluir(item: SaldoConta) {
  if (!confirm(`Remover saldo desta conta?`)) return
  try {
    await saldosContasService.excluir(item.id)
    toast.add({ severity: "info", summary: "Removido", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="💰 Saldos de Contas Correntes"
              :subtitle="`Posição consolidada de ativos líquidos • ${periodo.labelPeriodo}`">
    <template #actions>
      <Button label="Replicar mês anterior" icon="pi pi-history" outlined @click="replicar" />
      <Button label="Salvar saldos" icon="pi pi-check"
              :loading="salvando" @click="salvarTudo" />
    </template>
  </PageHeader>

  <DataTable :value="linhasMontadas" :loading="carregando" stripedRows>
    <Column header="Conta" style="min-width: 260px">
      <template #body="{ data }">
        <div :class="classeBarra(data.instituicao?.nome)">
          <div class="conta-info">
            <div class="conta-nome">
              <strong>{{ data.conta.nome }}</strong>
              <span class="tag-classe" :class="data.conta.moeda === 'BRL' ? 'acao' : 'etf'"
                    style="margin-left: 8px">
                {{ data.conta.moeda }}
              </span>
            </div>
            <span class="conta-tipo">{{ data.conta.tipo }}</span>
          </div>
        </div>
      </template>
    </Column>
    <Column header="Saldo">
      <template #body="{ data }">
        <InputNumber
          :modelValue="data.saldo"
          @update:modelValue="(v) => alterouSaldo(data.conta.id, v)"
          mode="currency" :currency="data.conta.moeda" locale="pt-BR" />
      </template>
    </Column>
    <Column header="Cotação USD/BRL">
      <template #body="{ data }">
        <InputNumber v-if="data.conta.moeda === 'USD'"
          :modelValue="data.cotacao"
          @update:modelValue="(v) => alterouCotacao(data.conta.id, v)"
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
    <Column header="Status">
      <template #body="{ data }">
        <span v-if="data.existente" class="badge-status salvo">
          <i class="pi pi-check" style="font-size: 10px"></i> Salvo
        </span>
        <span v-else class="badge-status pendente">
          <i class="pi pi-clock" style="font-size: 10px"></i> Pendente
        </span>
      </template>
    </Column>
    <Column header="Ações" style="width: 5rem">
      <template #body="{ data }">
        <Button v-if="data.existente" icon="pi pi-trash" severity="danger"
                text @click="excluir(data.existente)" />
      </template>
    </Column>
    <template #footer>
      <div class="footer-total">
        Total consolidado:
        <strong class="tabular numero-destaque">{{ fmtBRL(totalBRL) }}</strong>
      </div>
    </template>
  </DataTable>
</template>

<style scoped>
.conta-info { display: flex; flex-direction: column; gap: 2px; }
.conta-nome { display: flex; align-items: center; }
.conta-tipo {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: capitalize;
}
.footer-total {
  text-align: right;
  font-size: var(--text-base);
  padding: var(--space-3) 0;
}
</style>
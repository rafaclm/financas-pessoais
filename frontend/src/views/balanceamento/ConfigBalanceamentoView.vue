<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import {
  balanceamentoService,
  type BalGeografia, type BalClasse, type BalAtivo
} from "@/services/balanceamento"
import { ativosService } from "@/services/ativos"
import type { Ativo } from "@/services/ativos"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputNumber from "primevue/inputnumber"
import Dropdown from "primevue/dropdown"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()

const geos = ref([] as BalGeografia[])
const classes = ref([] as BalClasse[])
const ativosCfg = ref([] as BalAtivo[])
const ativos = ref([] as Ativo[])
const carregando = ref(false)

// Dialogs
const dialogGeo = ref(false)
const dialogClasse = ref(false)
const dialogAtivo = ref(false)

const formGeo = ref({} as Partial<BalGeografia> & { editId?: number })
const formClasse = ref({} as Partial<BalClasse> & { editId?: number })
const formAtivo = ref({} as Partial<BalAtivo> & { editId?: number })

const opcoesGeo = [
  { label: "🇧🇷 Brasil (BR)", value: "BR" },
  { label: "🇺🇸 EUA", value: "EUA" },
  { label: "🌐 Global", value: "GLOBAL" },
]
const opcoesClasse = [
  { label: "Ação", value: "acao" },
  { label: "ETF", value: "etf" },
  { label: "FII", value: "fii" },
  { label: "Fiagro", value: "fiagro" },
  { label: "REIT", value: "reit" },
  { label: "Cripto", value: "cripto" },
]

const mapAtivo = computed(() => {
  const m = new Map<number, Ativo>()
  ativos.value.forEach(a => m.set(a.id, a))
  return m
})

// Soma total das geografias
const somaGeo = computed(() =>
  geos.value.filter(g => g.ativo === 1).reduce((acc, g) => acc + Number(g.percentual_alvo), 0)
)
const somaGeoOK = computed(() => Math.abs(somaGeo.value - 100) <= 0.01)

// Soma de classes por geografia
const somaClassePorGeo = computed(() => {
  const m: Record<string, number> = {}
  classes.value.filter(c => c.ativo === 1).forEach(c => {
    m[c.geografia] = (m[c.geografia] || 0) + Number(c.percentual_alvo)
  })
  return m
})

// Soma de ativos
const somaAtivos = computed(() =>
  ativosCfg.value.filter(a => a.ativo === 1)
    .reduce((acc, a) => acc + Number(a.percentual_alvo_carteira), 0)
)

const fmt = (v: number) => v.toFixed(2) + "%"

async function carregar() {
  carregando.value = true
  try {
    const [g, c, a, ats] = await Promise.all([
      balanceamentoService.listarGeografia(),
      balanceamentoService.listarClasse(),
      balanceamentoService.listarAtivo(),
      ativos.value.length ? Promise.resolve(ativos.value) : ativosService.listar({ apenas_ativos: true }),
    ])
    geos.value = g
    classes.value = c
    ativosCfg.value = a
    if (!ativos.value.length) ativos.value = ats
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

// ===== GEOGRAFIA =====
function abrirNovaGeo() {
  formGeo.value = { geografia: "BR", percentual_alvo: 0, ativo: 1 }
  dialogGeo.value = true
}
function abrirEditarGeo(row: BalGeografia) {
  formGeo.value = { ...row, editId: row.id }
  dialogGeo.value = true
}
async function salvarGeo() {
  try {
    if (formGeo.value.editId) {
      await balanceamentoService.atualizarGeografia(formGeo.value.editId, {
        percentual_alvo: formGeo.value.percentual_alvo,
        ativo: formGeo.value.ativo,
      })
    } else {
      await balanceamentoService.criarGeografia(formGeo.value)
    }
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogGeo.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
async function excluirGeo(row: BalGeografia) {
  if (!confirm(`Excluir meta de ${row.geografia}?`)) return
  try {
    await balanceamentoService.excluirGeografia(row.id)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

// ===== CLASSE =====
function abrirNovaClasse() {
  formClasse.value = { geografia: "BR", classe: "acao", percentual_alvo: 0, ativo: 1 }
  dialogClasse.value = true
}
function abrirEditarClasse(row: BalClasse) {
  formClasse.value = { ...row, editId: row.id }
  dialogClasse.value = true
}
async function salvarClasse() {
  try {
    if (formClasse.value.editId) {
      await balanceamentoService.atualizarClasse(formClasse.value.editId, {
        percentual_alvo: formClasse.value.percentual_alvo,
        ativo: formClasse.value.ativo,
      })
    } else {
      await balanceamentoService.criarClasse(formClasse.value)
    }
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogClasse.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
async function excluirClasse(row: BalClasse) {
  if (!confirm(`Excluir meta ${row.geografia}/${row.classe}?`)) return
  try {
    await balanceamentoService.excluirClasse(row.id)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

// ===== ATIVO =====
function abrirNovoAtivo() {
  formAtivo.value = { ativo_id: ativos.value[0]?.id, percentual_alvo_carteira: 0, ativo: 1 }
  dialogAtivo.value = true
}
function abrirEditarAtivo(row: BalAtivo) {
  formAtivo.value = { ...row, editId: row.id }
  dialogAtivo.value = true
}
async function salvarAtivo() {
  try {
    if (formAtivo.value.editId) {
      await balanceamentoService.atualizarAtivo(formAtivo.value.editId, {
        percentual_alvo_carteira: formAtivo.value.percentual_alvo_carteira,
        ativo: formAtivo.value.ativo,
      })
    } else {
      await balanceamentoService.criarAtivo(formAtivo.value)
    }
    toast.add({ severity: "success", summary: "Salvo", life: 2500 })
    dialogAtivo.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
async function excluirAtivo(row: BalAtivo) {
  const a = mapAtivo.value.get(row.ativo_id)
  if (!confirm(`Excluir meta de ${a?.ticker || row.ativo_id}?`)) return
  try {
    await balanceamentoService.excluirAtivo(row.id)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}
</script>

<template>
  <PageHeader title="⚙️ Configuração de Metas"
              subtitle="Defina os alvos de alocação da sua carteira de renda variável" />

  <!-- NÍVEL 1 — GEOGRAFIA -->
  <section class="bloco">
    <div class="bloco-header">
      <h2>🌎 Nível 1 — Por Geografia</h2>
      <div class="header-info">
        <Tag :severity="somaGeoOK ? 'success' : 'warning'"
             :value="`Soma: ${somaGeo.toFixed(2)}%`" />
        <Button label="Nova meta" icon="pi pi-plus" @click="abrirNovaGeo" />
      </div>
    </div>
    <DataTable :value="geos" :loading="carregando" stripedRows>
      <Column header="Geografia">
        <template #body="{ data }">
          <strong>{{ data.geografia === "BR" ? "🇧🇷 Brasil" :
            data.geografia === "EUA" ? "🇺🇸 EUA" : "🌐 " + data.geografia }}</strong>
        </template>
      </Column>
      <Column header="% Alvo" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular">{{ fmt(Number(data.percentual_alvo)) }}</span>
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :severity="data.ativo ? 'success' : 'secondary'"
               :value="data.ativo ? 'Ativo' : 'Inativo'" />
        </template>
      </Column>
      <Column header="Ações" style="width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text @click="abrirEditarGeo(data)" />
          <Button icon="pi pi-trash" severity="danger" text @click="excluirGeo(data)" />
        </template>
      </Column>
    </DataTable>
  </section>

  <!-- NÍVEL 2 — CLASSE -->
  <section class="bloco">
    <div class="bloco-header">
      <h2>🧩 Nível 2 — Por Classe de Ativo</h2>
      <Button label="Nova meta" icon="pi pi-plus" @click="abrirNovaClasse" />
    </div>
    <div v-for="(soma, g) in somaClassePorGeo" :key="g" class="soma-classe">
      <span>{{ g === "BR" ? "🇧🇷 Brasil" : g === "EUA" ? "🇺🇸 EUA" : g }}:</span>
      <Tag :severity="Math.abs(soma - 100) <= 0.01 ? 'success' : 'warning'"
           :value="`${soma.toFixed(2)}%`" />
    </div>
    <DataTable :value="classes" :loading="carregando" stripedRows>
      <Column header="Geografia">
        <template #body="{ data }">
          {{ data.geografia === "BR" ? "🇧🇷 BR" : data.geografia === "EUA" ? "🇺🇸 EUA" : data.geografia }}
        </template>
      </Column>
      <Column header="Classe">
        <template #body="{ data }">
          <Tag :value="data.classe.toUpperCase()" severity="info" />
        </template>
      </Column>
      <Column header="% Alvo" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular">{{ fmt(Number(data.percentual_alvo)) }}</span>
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :severity="data.ativo ? 'success' : 'secondary'"
               :value="data.ativo ? 'Ativo' : 'Inativo'" />
        </template>
      </Column>
      <Column header="Ações" style="width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text @click="abrirEditarClasse(data)" />
          <Button icon="pi pi-trash" severity="danger" text @click="excluirClasse(data)" />
        </template>
      </Column>
    </DataTable>
  </section>

  <!-- NÍVEL 3 — ATIVO -->
  <section class="bloco">
    <div class="bloco-header">
      <h2>🎯 Nível 3 — Ativos Estratégicos (opcional)</h2>
      <div class="header-info">
        <Tag severity="info" :value="`Soma: ${somaAtivos.toFixed(2)}%`" />
        <Button label="Nova meta" icon="pi pi-plus" @click="abrirNovoAtivo" />
      </div>
    </div>
    <p class="hint">💡 Defina aqui apenas os ativos individuais que quer monitorar. Os demais ficam livres.</p>
    <DataTable :value="ativosCfg" :loading="carregando" stripedRows>
      <Column header="Ativo">
        <template #body="{ data }">
          <strong>{{ mapAtivo.get(data.ativo_id)?.ticker || "—" }}</strong>
          <span class="nome-ativo">{{ mapAtivo.get(data.ativo_id)?.nome }}</span>
        </template>
      </Column>
      <Column header="Classe">
        <template #body="{ data }">{{ mapAtivo.get(data.ativo_id)?.classe }}</template>
      </Column>
      <Column header="% da Carteira" style="text-align: right">
        <template #body="{ data }">
          <span class="tabular">{{ fmt(Number(data.percentual_alvo_carteira)) }}</span>
        </template>
      </Column>
      <Column header="Status">
        <template #body="{ data }">
          <Tag :severity="data.ativo ? 'success' : 'secondary'"
               :value="data.ativo ? 'Ativo' : 'Inativo'" />
        </template>
      </Column>
      <Column header="Ações" style="width: 8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" text @click="abrirEditarAtivo(data)" />
          <Button icon="pi pi-trash" severity="danger" text @click="excluirAtivo(data)" />
        </template>
      </Column>
    </DataTable>
  </section>

  <!-- DIALOGS -->
  <Dialog v-model:visible="dialogGeo" :header="formGeo.editId ? 'Editar' : 'Nova meta'"
          modal :style="{ width: '440px' }">
    <div class="form">
      <label>Geografia</label>
      <Dropdown v-model="formGeo.geografia" :options="opcoesGeo"
                optionLabel="label" optionValue="value"
                :disabled="!!formGeo.editId" />
      <label>Percentual alvo (%)</label>
      <InputNumber v-model="formGeo.percentual_alvo"
                   :min="0" :max="100" :minFractionDigits="2" :maxFractionDigits="2" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogGeo = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvarGeo" />
    </template>
  </Dialog>

  <Dialog v-model:visible="dialogClasse" :header="formClasse.editId ? 'Editar' : 'Nova meta'"
          modal :style="{ width: '440px' }">
    <div class="form">
      <label>Geografia</label>
      <Dropdown v-model="formClasse.geografia" :options="opcoesGeo"
                optionLabel="label" optionValue="value"
                :disabled="!!formClasse.editId" />
      <label>Classe</label>
      <Dropdown v-model="formClasse.classe" :options="opcoesClasse"
                optionLabel="label" optionValue="value"
                :disabled="!!formClasse.editId" />
      <label>Percentual alvo (%) — dentro da geografia</label>
      <InputNumber v-model="formClasse.percentual_alvo"
                   :min="0" :max="100" :minFractionDigits="2" :maxFractionDigits="2" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogClasse = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvarClasse" />
    </template>
  </Dialog>

  <Dialog v-model:visible="dialogAtivo" :header="formAtivo.editId ? 'Editar' : 'Nova meta'"
          modal :style="{ width: '480px' }">
    <div class="form">
      <label>Ativo</label>
      <Dropdown v-model="formAtivo.ativo_id" :options="ativos"
                optionLabel="ticker" optionValue="id"
                :filter="true" filterPlaceholder="Buscar..."
                :disabled="!!formAtivo.editId" />
      <label>Percentual alvo (% da carteira total RV)</label>
      <InputNumber v-model="formAtivo.percentual_alvo_carteira"
                   :min="0" :max="100" :minFractionDigits="2" :maxFractionDigits="2" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogAtivo = false" />
      <Button label="Salvar" icon="pi pi-check" @click="salvarAtivo" />
    </template>
  </Dialog>
</template>

<style scoped>
.bloco { margin-bottom: var(--space-8); }
.bloco-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-3);
}
.bloco-header h2 { font-size: var(--text-lg); color: var(--text-primary); }
.header-info { display: flex; gap: var(--space-3); align-items: center; }
.soma-classe {
  display: inline-flex; gap: var(--space-2); align-items: center;
  margin: var(--space-1) var(--space-4) var(--space-2) 0;
  font-size: var(--text-sm); color: var(--text-secondary);
}
.hint { font-size: var(--text-sm); color: var(--text-muted); margin-bottom: var(--space-3); }
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
.nome-ativo { color: var(--text-muted); font-size: var(--text-sm); margin-left: var(--space-2); }
</style>
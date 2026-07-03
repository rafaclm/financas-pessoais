<script setup lang="ts">
import { ref, watch } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import { replicacaoService } from "@/services/replicacao"
import { useToast } from "primevue/usetoast"
import Dialog from "primevue/dialog"
import Button from "primevue/button"
import Checkbox from "primevue/checkbox"
import Dropdown from "primevue/dropdown"

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: "update:visible", v: boolean): void
  (e: "concluido"): void
}>()

const periodo = usePeriodoStore()
const toast = useToast()

const replicar_receitas = ref(true)
const replicar_despesas = ref(true)
const apenas_recorrentes = ref(true)
const force = ref(false)
const carregando = ref(false)

// Define origem como mês anterior por padrão
const anoOrigemId = ref<number | null>(null)
const mesOrigem = ref<number>(1)

watch(() => props.visible, (v) => {
  if (v && periodo.anoIdSelecionado) {
    const mesAtual = periodo.mesSelecionado
    if (mesAtual === 1) {
      // janeiro -> dezembro do ano anterior
      const idx = periodo.anosDisponiveis.findIndex(a => a.id === periodo.anoIdSelecionado)
      const anoAnt = periodo.anosDisponiveis.find(
        a => a.ano === (periodo.anosDisponiveis[idx]?.ano || 0) - 1
      )
      anoOrigemId.value = anoAnt ? anoAnt.id : periodo.anoIdSelecionado
      mesOrigem.value = 12
    } else {
      anoOrigemId.value = periodo.anoIdSelecionado
      mesOrigem.value = mesAtual - 1
    }
  }
})

async function executar() {
  if (!anoOrigemId.value || !periodo.anoIdSelecionado) return
  carregando.value = true
  try {
    const r = await replicacaoService.replicar({
      ano_origem_id: anoOrigemId.value,
      mes_origem: mesOrigem.value,
      ano_destino_id: periodo.anoIdSelecionado,
      mes_destino: periodo.mesSelecionado,
      replicar_receitas: replicar_receitas.value,
      replicar_despesas: replicar_despesas.value,
      apenas_recorrentes: apenas_recorrentes.value,
      force: force.value,
    })
    toast.add({
      severity: "success", summary: "Replicação concluída",
      detail: r.mensagem, life: 5000
    })
    emit("concluido")
    emit("update:visible", false)
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <Dialog :visible="visible" @update:visible="(v: boolean) => emit('update:visible', v)"
          modal header="🔁 Replicar lançamentos do mês anterior"
          :style="{ width: '500px' }">
    <div class="form">
      <p class="info">
        Origem: <strong>{{ periodo.MESES[mesOrigem - 1] }} / {{
          periodo.anosDisponiveis.find(a => a.id === anoOrigemId)?.ano || "?"
        }}</strong><br>
        Destino: <strong>{{ periodo.labelPeriodo }}</strong>
      </p>

      <label>Origem (mês)</label>
      <Dropdown v-model="mesOrigem"
                :options="periodo.MESES.map((m, i) => ({ label: m, value: i + 1 }))"
                optionLabel="label" optionValue="value" />

      <label>Origem (ano)</label>
      <Dropdown v-model="anoOrigemId"
                :options="periodo.anosDisponiveis.map(a => ({ label: a.ano, value: a.id }))"
                optionLabel="label" optionValue="value" />

      <div class="opcoes">
        <div class="opt"><Checkbox v-model="replicar_receitas" :binary="true" inputId="rec" />
          <label for="rec">Replicar receitas</label></div>
        <div class="opt"><Checkbox v-model="replicar_despesas" :binary="true" inputId="desp" />
          <label for="desp">Replicar despesas</label></div>
        <div class="opt"><Checkbox v-model="apenas_recorrentes" :binary="true" inputId="rec2" />
          <label for="rec2">Apenas itens marcados como recorrentes</label></div>
        <div class="opt warn"><Checkbox v-model="force" :binary="true" inputId="force" />
          <label for="force">⚠ Forçar (sobrescrever se já houver lançamentos)</label></div>
      </div>
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="emit('update:visible', false)" />
      <Button :label="carregando ? 'Replicando...' : '✅ Replicar'"
              :loading="carregando" @click="executar" />
    </template>
  </Dialog>
</template>

<style scoped>
.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); }
.info {
  background: var(--bg-elevated); padding: var(--space-3);
  border-radius: var(--radius-md); font-size: var(--text-sm);
}
.opcoes { display: flex; flex-direction: column; gap: var(--space-3); margin-top: var(--space-4); }
.opt { display: flex; align-items: center; gap: var(--space-2); }
.opt label { margin: 0 !important; cursor: pointer; }
.warn { color: var(--warning); }
</style>
<script setup lang="ts">
import { onMounted, computed } from "vue"
import { usePeriodoStore } from "@/stores/periodo"
import Dropdown from "primevue/dropdown"
import { Calendar } from "lucide-vue-next"

const periodo = usePeriodoStore()

onMounted(async () => {
  if (periodo.anosDisponiveis.length === 0) await periodo.carregarAnos()
})

const optionsMes = computed(() =>
  periodo.MESES.map((nome, idx) => ({ label: nome, value: idx + 1 }))
)
const optionsAno = computed(() =>
  periodo.anosDisponiveis.map(a => ({ label: a.ano, value: a.id }))
)
</script>

<template>
  <div class="seletor">
    <Calendar :size="18" class="icone" />
    <Dropdown
      :modelValue="periodo.mesSelecionado"
      @update:modelValue="(v: number) => periodo.definir(periodo.anoIdSelecionado!, v)"
      :options="optionsMes"
      optionLabel="label"
      optionValue="value"
      class="dd-mes"
      :pt="{ root: { style: 'min-width: 130px' } }"
    />
    <Dropdown
      :modelValue="periodo.anoIdSelecionado"
      @update:modelValue="(v: number) => periodo.definir(v, periodo.mesSelecionado)"
      :options="optionsAno"
      optionLabel="label"
      optionValue="value"
      class="dd-ano"
      :pt="{ root: { style: 'min-width: 100px' } }"
    />
  </div>
</template>

<style scoped>
.seletor {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 4px 10px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}
.icone {
  color: var(--brand-primary);
}
</style>
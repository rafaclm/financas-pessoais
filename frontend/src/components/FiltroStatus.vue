<script setup lang="ts">
import Dropdown from "primevue/dropdown"

interface Props {
  modelValue: "ativos" | "inativos" | "todos"
  showLabel?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  showLabel: true,
})

const emit = defineEmits<{
  (e: "update:modelValue", v: "ativos" | "inativos" | "todos"): void
}>()

const opcoes = [
  { label: "✅ Ativos", value: "ativos" },
  { label: "🚫 Inativos", value: "inativos" },
  { label: "📋 Todos", value: "todos" },
]
</script>

<template>
  <div class="filtro-status">
    <label v-if="showLabel">Status</label>
    <Dropdown
      :modelValue="modelValue"
      @update:modelValue="(v: any) => emit('update:modelValue', v)"
      :options="opcoes"
      optionLabel="label"
      optionValue="value"
      :pt="{ root: { style: 'min-width: 150px' } }" />
  </div>
</template>

<style scoped>
.filtro-status {
  display: flex; flex-direction: column; gap: var(--space-1);
}
.filtro-status label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
}
</style>
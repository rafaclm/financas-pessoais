<script setup lang="ts">
import { computed } from "vue"
import { TrendingUp, TrendingDown, Minus } from "lucide-vue-next"

interface Props {
  label: string
  valor: number
  icone?: string
  cor?: string
  variacao?: number | null
  moeda?: "BRL" | "USD"
  subtitulo?: string
}
const props = withDefaults(defineProps<Props>(), {
  moeda: "BRL", cor: "var(--brand-primary)"
})

const formatado = computed(() => {
  return new Intl.NumberFormat(props.moeda === "BRL" ? "pt-BR" : "en-US", {
    style: "currency",
    currency: props.moeda
  }).format(props.valor || 0)
})

const variacaoFmt = computed(() =>
  props.variacao !== null && props.variacao !== undefined
    ? `${props.variacao > 0 ? "+" : ""}${props.variacao.toFixed(1)}%`
    : null
)
const variacaoClasse = computed(() => {
  if (props.variacao === null || props.variacao === undefined) return ""
  if (props.variacao > 0) return "var-positiva"
  if (props.variacao < 0) return "var-negativa"
  return "var-neutra"
})
</script>

<template>
  <div class="card-kpi">
    <div class="header">
      <span class="icone" v-if="icone">{{ icone }}</span>
      <span class="label">{{ label }}</span>
    </div>
    <div class="valor tabular" :style="{ color: cor }">{{ formatado }}</div>
    <div v-if="variacaoFmt" class="variacao" :class="variacaoClasse">
      <TrendingUp v-if="(variacao ?? 0) > 0" :size="14" />
      <TrendingDown v-else-if="(variacao ?? 0) < 0" :size="14" />
      <Minus v-else :size="14" />
      {{ variacaoFmt }}
      <span v-if="subtitulo" class="subt">{{ subtitulo }}</span>
    </div>
    <div v-else-if="subtitulo" class="subt-only">{{ subtitulo }}</div>
  </div>
</template>

<style scoped>
.card-kpi {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex; flex-direction: column; gap: var(--space-2);
  transition: border-color 200ms;
}
.card-kpi:hover { border-color: var(--border-default); }
.header { display: flex; align-items: center; gap: var(--space-2); }
.icone { font-size: var(--text-lg); }
.label {
  font-size: var(--text-xs); font-weight: 500;
  text-transform: uppercase; color: var(--text-muted);
  letter-spacing: 0.05em;
}
.valor { font-size: var(--text-2xl); font-weight: 700; }
.variacao {
  display: flex; align-items: center; gap: 4px;
  font-size: var(--text-sm); font-weight: 500;
}
.var-positiva { color: var(--success); }
.var-negativa { color: var(--danger); }
.var-neutra { color: var(--text-muted); }
.subt { color: var(--text-muted); margin-left: var(--space-1); font-weight: 400; }
.subt-only { font-size: var(--text-xs); color: var(--text-muted); }
</style>
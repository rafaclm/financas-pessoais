<script setup lang="ts">
import { ref, watch, onMounted } from "vue"

interface Props {
  valor: number
  duracao?: number  // ms
  formato?: "brl" | "pct" | "numero"
  decimais?: number
}
const props = withDefaults(defineProps<Props>(), {
  duracao: 1200,
  formato: "brl",
  decimais: 2,
})

const valorExibido = ref(0)

function easeOutQuart(t: number): number {
  return 1 - Math.pow(1 - t, 4)
}

function animar(valorAlvo: number) {
  const inicio = valorExibido.value
  const delta = valorAlvo - inicio
  const tInicio = performance.now()

  function passo(agora: number) {
    const decorrido = agora - tInicio
    const progresso = Math.min(decorrido / props.duracao, 1)
    const easedProgresso = easeOutQuart(progresso)
    valorExibido.value = inicio + delta * easedProgresso
    if (progresso < 1) {
      requestAnimationFrame(passo)
    } else {
      valorExibido.value = valorAlvo
    }
  }

  requestAnimationFrame(passo)
}

function formatar(v: number): string {
  if (props.formato === "brl") {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: props.decimais,
      maximumFractionDigits: props.decimais,
    }).format(v)
  }
  if (props.formato === "pct") {
    const sinal = v > 0 ? "+" : ""
    return `${sinal}${v.toFixed(props.decimais)}%`
  }
  return v.toFixed(props.decimais)
}

onMounted(() => animar(props.valor))
watch(() => props.valor, (novo) => animar(novo))
</script>

<template>
  <span class="kpi-animado tabular">{{ formatar(valorExibido) }}</span>
</template>

<style scoped>
.kpi-animado {
  font-variant-numeric: tabular-nums;
}
</style>
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, nextTick, computed } from "vue"
import { Chart, registerables } from "chart.js"
import { useTemaStore } from "@/stores/tema"

Chart.register(...registerables)

interface Props {
  type: "line" | "bar" | "doughnut" | "pie"
  data: any
  options?: any
  // Callback chamado ao clicar em um item
  onItemClick?: (item: { datasetIndex: number; index: number; label: string }) => void
}
const props = defineProps<Props>()

const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
const tema = useTemaStore()

// Cores adaptativas baseadas no tema atual
const cores = computed(() => {
  const ehEscuro = tema.tema === "dark"
  return {
    texto: ehEscuro ? "#CBD5E1" : "#475569",
    textoSecundario: ehEscuro ? "#94A3B8" : "#64748B",
    grade: ehEscuro ? "rgba(148, 163, 184, 0.1)" : "rgba(100, 116, 139, 0.15)",
    tooltipBg: ehEscuro ? "rgba(15, 23, 42, 0.95)" : "rgba(255, 255, 255, 0.98)",
    tooltipTitulo: ehEscuro ? "#F1F5F9" : "#0F172A",
    tooltipTexto: ehEscuro ? "#CBD5E1" : "#334155",
    tooltipBorda: ehEscuro ? "#334155" : "#CBD5E1",
  }
})

async function renderizar() {
  await nextTick()
  if (!canvas.value) return

  if (chart) {
    try { chart.destroy() } catch (e) { console.warn(e) }
    chart = null
  }

  if (!props.data || !props.data.datasets || props.data.datasets.length === 0) {
    return
  }

  try {
    chart = new Chart(canvas.value, {
      type: props.type,
      data: props.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1000,
          easing: "easeOutQuart",
        },
        onClick: (event, elements) => {
          if (elements.length > 0 && props.onItemClick) {
            const el = elements[0]
            const label = props.data.labels[el.index]
            props.onItemClick({
              datasetIndex: el.datasetIndex,
              index: el.index,
              label: String(label),
            })
          }
        },
        onHover: (event, elements) => {
          if (canvas.value) {
            canvas.value.style.cursor =
              elements.length > 0 && props.onItemClick ? "pointer" : "default"
          }
        },
        plugins: {
          legend: {
            labels: { color: cores.value.texto, padding: 12 }
          },
          tooltip: {
            backgroundColor: cores.value.tooltipBg,
            titleColor: cores.value.tooltipTitulo,
            bodyColor: cores.value.tooltipTexto,
            borderColor: cores.value.tooltipBorda,
            borderWidth: 1,
            padding: 12,
            titleFont: { size: 13, weight: "bold" },
            bodyFont: { size: 12 },
            cornerRadius: 8,
            boxPadding: 6,
          }
        },
        ...props.options,
      }
    })
  } catch (e) {
    console.error("Erro ao renderizar gráfico:", e)
  }
}

onMounted(renderizar)

watch(() => props.data, renderizar, { deep: true })
watch(() => props.options, renderizar, { deep: true })
// Re-renderiza quando o tema muda
watch(() => tema.tema, renderizar)

onBeforeUnmount(() => {
  if (chart) {
    try { chart.destroy() } catch (e) { console.warn(e) }
  }
})
</script>

<template>
  <div class="grafico-wrapper">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<style scoped>
.grafico-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 250px;
}
</style>
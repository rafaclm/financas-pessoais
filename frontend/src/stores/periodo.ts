import { defineStore } from "pinia"
import { ref, computed, watch } from "vue"
import { anosService, type Ano } from "@/services/anos"

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

export const usePeriodoStore = defineStore("periodo", () => {
  const anosDisponiveis = ref<Ano[]>([])
  const anoIdSelecionado = ref<number | null>(null)
  const mesSelecionado = ref<number>(new Date().getMonth() + 1)
  // Token incrementado a cada mudança para que telas observem e recarreguem
  const versao = ref(0)

  const anoAtual = computed(() =>
    anosDisponiveis.value.find(a => a.id === anoIdSelecionado.value)
  )

  const labelMes = computed(() => MESES[mesSelecionado.value - 1])
  const labelPeriodo = computed(() =>
    anoAtual.value ? `${labelMes.value} / ${anoAtual.value.ano}` : "Sem período"
  )

  async function carregarAnos() {
    anosDisponiveis.value = await anosService.listar(true)
    if (!anoIdSelecionado.value && anosDisponiveis.value.length > 0) {
      const anoCorrente = new Date().getFullYear()
      const ano = anosDisponiveis.value.find(a => a.ano === anoCorrente)
        || anosDisponiveis.value[0]
      anoIdSelecionado.value = ano.id
    }
  }

  function definir(anoId: number, mes: number) {
    anoIdSelecionado.value = anoId
    mesSelecionado.value = mes
  }

  // Quando muda ano ou mês, incrementa a versao
  watch([anoIdSelecionado, mesSelecionado], () => {
    versao.value++
  })

  return {
    anosDisponiveis, anoIdSelecionado, mesSelecionado, versao,
    anoAtual, labelMes, labelPeriodo, MESES,
    carregarAnos, definir,
  }
})
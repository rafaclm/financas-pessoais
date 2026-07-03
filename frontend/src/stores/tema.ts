import { defineStore } from "pinia"
import { ref, watch } from "vue"

export const useTemaStore = defineStore("tema", () => {
  const tema = ref<"dark" | "light">("dark")

  // Recupera tema salvo
  const salvo = localStorage.getItem("tema") as "dark" | "light" | null
  if (salvo) {
    tema.value = salvo
  }

  function aplicar() {
    document.documentElement.classList.remove("theme-dark", "theme-light")
    document.documentElement.classList.add(`theme-${tema.value}`)
    localStorage.setItem("tema", tema.value)
  }

  function toggle() {
    tema.value = tema.value === "dark" ? "light" : "dark"
  }

  // Aplica ao inicializar
  aplicar()

  // Aplica sempre que mudar
  watch(tema, aplicar)

  return { tema, toggle }
})
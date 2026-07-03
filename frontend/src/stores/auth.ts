import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { authService } from "@/services/auth"
import type { Usuario, LoginPayload, RegisterPayload } from "@/services/auth"

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(null)
  const usuario = ref<Usuario | null>(null)

  const autenticado = computed(() => !!token.value)
  const nome = computed(() => usuario.value?.nome || "")
  const email = computed(() => usuario.value?.email || "")
  const iniciais = computed(() => {
    const n = usuario.value?.nome || ""
    const partes = n.trim().split(/\s+/)
    if (partes.length >= 2) return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
    return n.slice(0, 2).toUpperCase()
  })

  function init() {
    try {
      const t = localStorage.getItem("auth_token")
      const u = localStorage.getItem("auth_user")
      if (t) token.value = t
      if (u) usuario.value = JSON.parse(u)
    } catch (e) {
      console.warn("Falha ao restaurar auth do localStorage:", e)
    }
  }

  function persistir(t: string, u: Usuario) {
    token.value = t
    usuario.value = u
    try {
      localStorage.setItem("auth_token", t)
      localStorage.setItem("auth_user", JSON.stringify(u))
    } catch (e) {
      console.warn("Falha ao salvar auth no localStorage:", e)
    }
  }

  async function login(payload: LoginPayload) {
    const resp = await authService.login(payload)
    persistir(resp.access_token, resp.usuario)
    return resp
  }

  async function registrar(payload: RegisterPayload) {
    const resp = await authService.registrar(payload)
    persistir(resp.access_token, resp.usuario)
    return resp
  }

  async function recarregarPerfil() {
    if (!token.value) return
    try {
      const u = await authService.perfil()
      usuario.value = u
      localStorage.setItem("auth_user", JSON.stringify(u))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    usuario.value = null
    try {
      localStorage.removeItem("auth_token")
      localStorage.removeItem("auth_user")
    } catch { /* ignore */ }
  }

  return {
    token, usuario, autenticado, nome, email, iniciais,
    init, login, registrar, recarregarPerfil, logout,
  }
})

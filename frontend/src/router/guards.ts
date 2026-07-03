import type { RouteLocationNormalized } from "vue-router"
import { useAuthStore } from "@/stores/auth"

/**
 * Guard que protege rotas privadas.
 * Se não estiver autenticado, redireciona para /login preservando o destino.
 */
export function requerAutenticacao(to: RouteLocationNormalized) {
  const auth = useAuthStore()
  if (!auth.autenticado) {
    return {
      path: "/login",
      query: { redirect: to.fullPath },
    }
  }
  return true
}

/**
 * Guard para rotas públicas (login/registro).
 * Se JÁ estiver autenticado, redireciona para a home.
 */
export function apenasNaoAutenticado(_to: RouteLocationNormalized) {
  const auth = useAuthStore()
  if (auth.autenticado) {
    return { path: "/" }
  }
  return true
}
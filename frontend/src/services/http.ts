import axios, { AxiosError, InternalAxiosRequestConfig } from "axios"

// Detecta URL da API:
// - Se VITE_API_URL estiver definido → usa ele
// - Senao → usa /api/v1 (proxy do Vite em dev)
const API_URL = import.meta.env.VITE_API_URL || "/api/v1"

export const http = axios.create({
  baseURL: API_URL,
  timeout: 30000,
})

// Interceptor de request: adiciona token JWT automaticamente
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("auth_token")
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor de response: trata erros comuns
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expirado ou invalido — forca logout
      localStorage.removeItem("auth_token")
      localStorage.removeItem("auth_user")
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login"
      }
    }
    const detail = (error.response?.data as any)?.detail
    if (detail && typeof detail === "string") {
      error.message = detail
    }
    return Promise.reject(error)
  }
)
import { http } from "./http"

export interface Usuario {
  id: number
  email: string
  nome: string
  ativo: boolean
  admin: boolean
  ultimo_login: string | null
  criado_em: string
  atualizado_em: string
}

export interface LoginPayload {
  email: string
  senha: string
}

export interface RegisterPayload {
  email: string
  nome: string
  senha: string
  codigo_cadastro: string
}

export interface TokenResposta {
  access_token: string
  token_type: string
  expires_in_days: number
  usuario: Usuario
}

export interface TrocarSenhaPayload {
  senha_atual: string
  senha_nova: string
}

export const authService = {
  login: (payload: LoginPayload) =>
    http.post<TokenResposta>("/auth/login", payload).then(r => r.data),

  registrar: (payload: RegisterPayload) =>
    http.post<TokenResposta>("/auth/register", payload).then(r => r.data),

  perfil: () =>
    http.get<Usuario>("/auth/me").then(r => r.data),

  alterarSenha: (payload: TrocarSenhaPayload) =>
    http.post("/auth/alterar-senha", payload).then(r => r.data),
}
import { http } from "./http"

export interface BackupInfo {
  nome: string
  tamanho_bytes: number
  tamanho_legivel: string
  criado_em: string
  descricao: string | null
}

export interface ResultadoBackup {
  nome: string
  tamanho_bytes: number
  tamanho_legivel: string
  descricao: string | null
  mensagem: string
}

export interface ResultadoRestauracao {
  mensagem: string
  backup_seguranca_criado: string
  aviso: string
}

export const backupService = {
  listar: () =>
    http.get<BackupInfo[]>("/backup").then(r => r.data),

  criar: (descricao?: string) =>
    http.post<ResultadoBackup>("/backup", { descricao: descricao || null })
      .then(r => r.data),

  downloadUrl: (nome: string) =>
    `/api/v1/backup/${encodeURIComponent(nome)}/download`,

  excluir: (nome: string) =>
    http.delete(`/backup/${encodeURIComponent(nome)}`),

  restaurar: (nome: string) =>
    http.post<ResultadoRestauracao>(`/backup/${encodeURIComponent(nome)}/restaurar`)
      .then(r => r.data),

  upload: (arquivo: File, descricao?: string) => {
    const fd = new FormData()
    fd.append("arquivo", arquivo)
    if (descricao) fd.append("descricao", descricao)
    return http.post<ResultadoBackup>("/backup/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" }
    }).then(r => r.data)
  },
}
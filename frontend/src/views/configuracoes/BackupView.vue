<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { backupService } from "@/services/backup"
import type { BackupInfo } from "@/services/backup"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import DataTable from "primevue/datatable"
import Column from "primevue/column"
import Dialog from "primevue/dialog"
import InputText from "primevue/inputtext"
import ProgressSpinner from "primevue/progressspinner"
import Message from "primevue/message"
import Tag from "primevue/tag"
import PageHeader from "@/components/PageHeader.vue"

const toast = useToast()
const lista = ref([] as BackupInfo[])
const carregando = ref(false)
const processando = ref(false)

// Dialog: criar backup
const dialogCriar = ref(false)
const descricaoCriar = ref("")

// Dialog: upload
const dialogUpload = ref(false)
const arquivoUpload = ref<File | null>(null)
const descricaoUpload = ref("")

// Dialog: restaurar (confirmação dupla)
const dialogRestaurar = ref(false)
const backupRestaurar = ref<BackupInfo | null>(null)
const confirmacaoRestaurar = ref("")
const palavraConfirmacao = "RESTAURAR"

async function carregar() {
  carregando.value = true
  try {
    lista.value = await backupService.listar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

// === Criar backup ===
function abrirCriar() {
  descricaoCriar.value = ""
  dialogCriar.value = true
}

async function criarBackup() {
  processando.value = true
  try {
    const r = await backupService.criar(descricaoCriar.value || undefined)
    toast.add({
      severity: "success",
      summary: "Backup criado",
      detail: `${r.nome} (${r.tamanho_legivel})`,
      life: 4000
    })
    dialogCriar.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally {
    processando.value = false
  }
}

// === Download ===
function baixar(item: BackupInfo) {
  const url = backupService.downloadUrl(item.nome)
  // Cria link temporário e clica
  const a = document.createElement("a")
  a.href = url
  a.download = item.nome
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  toast.add({
    severity: "info",
    summary: "Download iniciado",
    detail: `Guarde o arquivo em local seguro!`,
    life: 3000
  })
}

// === Excluir ===
async function excluir(item: BackupInfo) {
  if (!confirm(`Excluir o backup "${item.nome}"?\n\nEsta ação não pode ser desfeita.`)) return
  try {
    await backupService.excluir(item.nome)
    toast.add({ severity: "info", summary: "Excluído", life: 2500 })
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 4000 })
  }
}

// === Restaurar (com confirmação dupla) ===
function abrirRestaurar(item: BackupInfo) {
  backupRestaurar.value = item
  confirmacaoRestaurar.value = ""
  dialogRestaurar.value = true
}

const podeRestaurar = computed(() =>
  confirmacaoRestaurar.value === palavraConfirmacao
)

async function executarRestaurar() {
  if (!backupRestaurar.value || !podeRestaurar.value) return
  processando.value = true
  try {
    const r = await backupService.restaurar(backupRestaurar.value.nome)
    toast.add({
      severity: "success",
      summary: "Banco restaurado!",
      detail: r.aviso,
      life: 12000,
      closable: true
    })
    dialogRestaurar.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally {
    processando.value = false
  }
}

// === Upload ===
function abrirUpload() {
  arquivoUpload.value = null
  descricaoUpload.value = ""
  dialogUpload.value = true
}

function selecionarArquivo(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    arquivoUpload.value = input.files[0]
  }
}

async function enviarUpload() {
  if (!arquivoUpload.value) {
    toast.add({ severity: "warn", summary: "Selecione um arquivo", life: 2500 })
    return
  }
  processando.value = true
  try {
    const r = await backupService.upload(arquivoUpload.value, descricaoUpload.value || undefined)
    toast.add({
      severity: "success",
      summary: "Upload concluído",
      detail: `${r.nome} (${r.tamanho_legivel})`,
      life: 4000
    })
    dialogUpload.value = false
    await carregar()
  } catch (e: any) {
    toast.add({ severity: "error", summary: "Erro", detail: e.message, life: 5000 })
  } finally {
    processando.value = false
  }
}

const fmtData = (d: string) => {
  const dt = new Date(d)
  return dt.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
}
</script>

<template>
  <PageHeader title="💾 Backup e Restore"
              subtitle="Proteja seus dados financeiros — crie backups frequentemente">
    <template #actions>
      <Button label="📤 Importar .db" outlined @click="abrirUpload" />
      <Button label="💾 Criar backup agora" icon="pi pi-save"
              @click="abrirCriar" />
    </template>
  </PageHeader>

  <Message severity="info" :closable="false" class="info-msg">
    💡 <strong>Dica:</strong> Faça um backup <strong>antes</strong> de qualquer importação grande
    ou mudança importante. Depois, baixe o arquivo e guarde em local seguro
    (HD externo, Google Drive, etc.).
  </Message>

  <div v-if="carregando" class="loading"><ProgressSpinner /></div>

  <DataTable v-else :value="lista" stripedRows :paginator="lista.length > 20" :rows="20">
    <Column header="Nome do arquivo">
      <template #body="{ data }">
        <span class="nome-arquivo">📄 {{ data.nome }}</span>
      </template>
    </Column>
    <Column header="Criado em" sortable sortField="criado_em">
      <template #body="{ data }">{{ fmtData(data.criado_em) }}</template>
    </Column>
    <Column header="Tamanho" sortable sortField="tamanho_bytes">
      <template #body="{ data }">
        <Tag :value="data.tamanho_legivel" severity="secondary" />
      </template>
    </Column>
    <Column header="Descrição">
      <template #body="{ data }">
        <span v-if="data.descricao">{{ data.descricao }}</span>
        <span v-else class="value-muted">—</span>
      </template>
    </Column>
    <Column header="Ações" style="width: 14rem">
      <template #body="{ data }">
        <div class="acoes">
          <Button icon="pi pi-download" text rounded
                  v-tooltip="'Baixar arquivo'"
                  @click="baixar(data)" />
          <Button icon="pi pi-refresh" text rounded severity="warn"
                  v-tooltip="'Restaurar este backup'"
                  @click="abrirRestaurar(data)" />
          <Button icon="pi pi-trash" text rounded severity="danger"
                  v-tooltip="'Excluir backup'"
                  @click="excluir(data)" />
        </div>
      </template>
    </Column>
    <template #empty>
      <div class="vazio">
        Nenhum backup ainda. Clique em <strong>"💾 Criar backup agora"</strong> para começar.
      </div>
    </template>
  </DataTable>

  <!-- Dialog: Criar -->
  <Dialog v-model:visible="dialogCriar" header="💾 Criar novo backup" modal
          :style="{ width: '460px' }">
    <div class="form">
      <p>Será criado um backup completo do seu banco de dados.</p>
      <label>Descrição (opcional)</label>
      <InputText v-model="descricaoCriar"
                 placeholder="Ex.: Antes de importar planilha 2024" />
      <small class="hint">💡 A descrição ajuda você a lembrar o que tem nesse backup.</small>
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogCriar = false" />
      <Button :label="processando ? 'Criando...' : 'Criar backup'"
              icon="pi pi-check" :loading="processando" @click="criarBackup" />
    </template>
  </Dialog>

  <!-- Dialog: Upload -->
  <Dialog v-model:visible="dialogUpload" header="📤 Importar arquivo de backup" modal
          :style="{ width: '500px' }">
    <div class="form">
      <p>Selecione um arquivo <strong>.db</strong> que você guardou em outro lugar.</p>
      <Message severity="info" :closable="false">
        Este arquivo será adicionado à lista de backups (não restaura automaticamente).
        Depois, você pode clicar em "Restaurar" para usar este backup.
      </Message>

      <label>Arquivo .db</label>
      <input type="file" accept=".db" @change="selecionarArquivo" class="file-input" />
      <small v-if="arquivoUpload" class="hint">
        ✓ Selecionado: <strong>{{ arquivoUpload.name }}</strong>
        ({{ (arquivoUpload.size / 1024).toFixed(2) }} KB)
      </small>

      <label>Descrição (opcional)</label>
      <InputText v-model="descricaoUpload"
                 placeholder="Ex.: Backup do HD externo de 15/06" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogUpload = false" />
      <Button :label="processando ? 'Enviando...' : 'Enviar'"
              icon="pi pi-upload" :loading="processando" @click="enviarUpload" />
    </template>
  </Dialog>

  <!-- Dialog: Restaurar (CRÍTICO - confirmação dupla) -->
  <Dialog v-model:visible="dialogRestaurar"
          header="⚠️ Restaurar backup — Operação Crítica" modal
          :style="{ width: '560px' }" :closable="!processando">
    <div class="form">
      <Message severity="warn" :closable="false">
        <strong>Atenção!</strong> Esta operação vai <strong>substituir</strong> todos os seus
        dados atuais pelos dados do backup selecionado.
      </Message>

      <div class="info-restaurar">
        <div><strong>Backup escolhido:</strong> {{ backupRestaurar?.nome }}</div>
        <div><strong>Criado em:</strong> {{ backupRestaurar ? fmtData(backupRestaurar.criado_em) : "" }}</div>
        <div v-if="backupRestaurar?.descricao">
          <strong>Descrição:</strong> {{ backupRestaurar.descricao }}
        </div>
      </div>

      <Message severity="success" :closable="false">
        🛡️ <strong>Segurança automática:</strong> antes de restaurar, o sistema vai criar
        um backup do estado atual (você pode voltar atrás depois).
      </Message>

      <label>Para confirmar, digite <strong>{{ palavraConfirmacao }}</strong> abaixo:</label>
      <InputText v-model="confirmacaoRestaurar"
                 :placeholder="palavraConfirmacao"
                 :class="{ 'invalid-confirm': confirmacaoRestaurar && !podeRestaurar }" />
    </div>
    <template #footer>
      <Button label="Cancelar" text @click="dialogRestaurar = false"
              :disabled="processando" />
      <Button :label="processando ? 'Restaurando...' : 'Restaurar agora'"
              icon="pi pi-refresh" severity="warn"
              :loading="processando" :disabled="!podeRestaurar"
              @click="executarRestaurar" />
    </template>
  </Dialog>
</template>

<style scoped>
.info-msg { margin-bottom: var(--space-4); }
.loading { display: flex; justify-content: center; padding: var(--space-12); }

.nome-arquivo {
  font-family: ui-monospace, monospace; font-size: var(--text-sm);
  color: var(--text-primary);
}

.acoes { display: flex; gap: var(--space-1); }

.vazio {
  padding: var(--space-12); text-align: center; color: var(--text-muted);
}

.form { display: flex; flex-direction: column; gap: var(--space-2); }
.form p { font-size: var(--text-sm); color: var(--text-secondary); margin-bottom: var(--space-2); }
.form label { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-3); }
.hint { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }

.file-input {
  padding: var(--space-2); background: var(--bg-elevated);
  border: 1px solid var(--border-default); border-radius: var(--radius-md);
  color: var(--text-primary);
}

.info-restaurar {
  background: var(--bg-elevated); padding: var(--space-3);
  border-radius: var(--radius-md); font-size: var(--text-sm);
  display: flex; flex-direction: column; gap: var(--space-1);
  margin: var(--space-3) 0;
}

.invalid-confirm { border-color: var(--danger) !important; }
</style>
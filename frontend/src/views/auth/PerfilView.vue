<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
import { authService } from "@/services/auth"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import PageHeader from "@/components/PageHeader.vue"
import { User, Mail, Shield, Calendar, Key, Eye, EyeOff, Save } from "lucide-vue-next"

const auth = useAuthStore()
const toast = useToast()

const senhaAtual = ref("")
const senhaNova = ref("")
const senhaNovaConfirmar = ref("")
const mostrarSenhaAtual = ref(false)
const mostrarSenhaNova = ref(false)
const carregando = ref(false)

const senhaNovaValida = computed(() => {
  const s = senhaNova.value
  return s.length >= 8 && /[a-zA-Z]/.test(s) && /\d/.test(s)
})

const senhasIguais = computed(() =>
  senhaNova.value && senhaNova.value === senhaNovaConfirmar.value
)

const formValido = computed(() =>
  senhaAtual.value && senhaNovaValida.value && senhasIguais.value
)

const dataFormatada = computed(() => {
  const dt = auth.usuario?.criado_em
  if (!dt) return "—"
  return new Date(dt).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "long", year: "numeric"
  })
})

const ultimoLoginFormatado = computed(() => {
  const dt = auth.usuario?.ultimo_login
  if (!dt) return "Primeiro acesso"
  return new Date(dt).toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  })
})

onMounted(() => {
  auth.recarregarPerfil()
})

async function alterarSenha() {
  if (!formValido.value) return

  carregando.value = true
  try {
    await authService.alterarSenha({
      senha_atual: senhaAtual.value,
      senha_nova: senhaNova.value,
    })
    toast.add({
      severity: "success",
      summary: "Senha alterada com sucesso!",
      detail: "Use a nova senha da próxima vez que fizer login",
      life: 5000
    })
    // Limpa formulario
    senhaAtual.value = ""
    senhaNova.value = ""
    senhaNovaConfirmar.value = ""
  } catch (e: any) {
    toast.add({
      severity: "error",
      summary: "Erro ao alterar senha",
      detail: e.message || "Verifique a senha atual",
      life: 5000
    })
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <PageHeader title="👤 Meu Perfil" subtitle="Gerencie sua conta e segurança" />

  <div class="perfil-grid">
    <!-- Card com informações da conta -->
    <div class="card-info">
      <div class="avatar-grande">{{ auth.iniciais }}</div>
      <h2>{{ auth.nome }}</h2>
      <p class="email-perfil">{{ auth.email }}</p>

      <div class="info-lista">
        <div class="info-item">
          <div class="info-icon"><User :size="16" /></div>
          <div class="info-conteudo">
            <span class="info-label">Perfil</span>
            <span class="info-valor">{{ auth.usuario?.admin ? "Administrador" : "Usuário" }}</span>
          </div>
        </div>

        <div class="info-item">
          <div class="info-icon"><Shield :size="16" /></div>
          <div class="info-conteudo">
            <span class="info-label">Status</span>
            <span class="info-valor">
              <span v-if="auth.usuario?.ativo" class="badge-status ativo">✓ Ativa</span>
              <span v-else class="badge-status inativo">✗ Inativa</span>
            </span>
          </div>
        </div>

        <div class="info-item">
          <div class="info-icon"><Calendar :size="16" /></div>
          <div class="info-conteudo">
            <span class="info-label">Membro desde</span>
            <span class="info-valor">{{ dataFormatada }}</span>
          </div>
        </div>

        <div class="info-item">
          <div class="info-icon"><Mail :size="16" /></div>
          <div class="info-conteudo">
            <span class="info-label">Último login</span>
            <span class="info-valor tabular">{{ ultimoLoginFormatado }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Card de alterar senha -->
    <div class="card-senha">
      <div class="card-header">
        <div class="card-icon">
          <Key :size="20" />
        </div>
        <div>
          <h3>Alterar Senha</h3>
          <p class="hint">Mantenha sua conta segura com senhas fortes</p>
        </div>
      </div>

      <form @submit.prevent="alterarSenha" class="form-senha">
        <div class="campo">
          <label>Senha atual</label>
          <div class="input-senha-wrapper">
            <InputText
              v-model="senhaAtual"
              :type="mostrarSenhaAtual ? 'text' : 'password'"
              placeholder="Digite sua senha atual"
              class="input-full"
            />
            <button type="button" class="btn-mostrar"
                    @click="mostrarSenhaAtual = !mostrarSenhaAtual">
              <Eye v-if="!mostrarSenhaAtual" :size="16" />
              <EyeOff v-else :size="16" />
            </button>
          </div>
        </div>

        <div class="campo">
          <label>Nova senha</label>
          <div class="input-senha-wrapper">
            <InputText
              v-model="senhaNova"
              :type="mostrarSenhaNova ? 'text' : 'password'"
              placeholder="Mínimo 8 caracteres"
              class="input-full"
            />
            <button type="button" class="btn-mostrar"
                    @click="mostrarSenhaNova = !mostrarSenhaNova">
              <Eye v-if="!mostrarSenhaNova" :size="16" />
              <EyeOff v-else :size="16" />
            </button>
          </div>
          <small class="hint-requisito" :class="{ valid: senhaNovaValida }">
            {{ senhaNovaValida ? '✓' : '○' }} 8+ caracteres, com letras e números
          </small>
        </div>

        <div class="campo">
          <label>Confirme a nova senha</label>
          <div class="input-senha-wrapper">
            <InputText
              v-model="senhaNovaConfirmar"
              :type="mostrarSenhaNova ? 'text' : 'password'"
              placeholder="Digite novamente"
              class="input-full"
            />
          </div>
          <small v-if="senhaNovaConfirmar" class="hint-requisito"
                 :class="{ valid: senhasIguais }">
            {{ senhasIguais ? '✓ Senhas coincidem' : '✗ Senhas não coincidem' }}
          </small>
        </div>

        <Button
          type="submit"
          :loading="carregando"
          :disabled="!formValido"
          class="btn-salvar"
        >
          <Save :size="16" style="margin-right: 8px" />
          Alterar senha
        </Button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.perfil-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: var(--space-6);
  align-items: start;
}

@media (max-width: 900px) {
  .perfil-grid {
    grid-template-columns: 1fr;
  }
}

/* Card de info */
.card-info {
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: 32px;
  text-align: center;
}

.avatar-grande {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 28px;
  margin: 0 auto 20px;
  box-shadow: var(--shadow-glow-primary);
}

.card-info h2 {
  font-size: var(--text-xl);
  color: var(--text-primary);
  margin-bottom: 4px;
}

.email-perfil {
  color: var(--text-muted);
  font-size: var(--text-sm);
  margin-bottom: 32px;
  font-family: var(--font-mono);
}

.info-lista {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  text-align: left;
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.info-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--brand-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-conteudo {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.info-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}

.info-valor {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: 500;
}

.badge-status {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
}

.badge-status.ativo {
  background: var(--success-bg);
  color: var(--success);
}

.badge-status.inativo {
  background: var(--danger-bg);
  color: var(--danger);
}

/* Card de senha */
.card-senha {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: 32px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.card-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--gradient-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-header h3 {
  font-size: var(--text-lg);
  color: var(--text-primary);
  margin-bottom: 2px;
}

.card-header .hint {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.form-senha {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.campo label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
}

:deep(.input-full) {
  width: 100%;
  height: 42px;
  padding: 0 14px;
}

.input-senha-wrapper {
  position: relative;
}

.input-senha-wrapper :deep(.input-full) {
  padding-right: 42px;
}

.btn-mostrar {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  transition: color 200ms ease;
}

.btn-mostrar:hover {
  color: var(--brand-primary);
}

.hint-requisito {
  font-size: var(--text-xs);
  color: var(--text-muted);
  padding-left: 4px;
}

.hint-requisito.valid {
  color: var(--success);
}

.btn-salvar {
  height: 44px;
  margin-top: var(--space-2);
}
</style>
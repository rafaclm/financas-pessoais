<script setup lang="ts">
import { ref, computed } from "vue"
import { useRouter, RouterLink } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import { UserPlus, ArrowLeft, Key, Eye, EyeOff } from "lucide-vue-next"

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const email = ref("")
const nome = ref("")
const senha = ref("")
const codigoCadastro = ref("")
const mostrarSenha = ref(false)
const carregando = ref(false)

const senhaValida = computed(() => {
  const s = senha.value
  return s.length >= 8 &&
    /[a-zA-Z]/.test(s) &&
    /\d/.test(s)
})

const formValido = computed(() =>
  email.value && nome.value && senhaValida.value && codigoCadastro.value
)

async function fazerRegistro() {
  if (!formValido.value) {
    toast.add({
      severity: "warn",
      summary: "Preencha todos os campos",
      detail: "Senha precisa ter 8+ caracteres, letras e números",
      life: 4000
    })
    return
  }

  carregando.value = true
  try {
    await auth.registrar({
      email: email.value,
      nome: nome.value,
      senha: senha.value,
      codigo_cadastro: codigoCadastro.value,
    })
    toast.add({
      severity: "success",
      summary: `Bem-vindo, ${nome.value}!`,
      detail: "Sua conta foi criada com sucesso",
      life: 4000
    })
    router.push("/")
  } catch (e: any) {
    toast.add({
      severity: "error",
      summary: "Falha no cadastro",
      detail: e.message || "Verifique os dados e tente novamente",
      life: 6000
    })
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div class="registro-card">
    <div class="registro-header">
      <div class="brand-badge">
        <UserPlus :size="24" />
      </div>
      <h1>Criar Conta</h1>
      <p class="subtitle">Cadastre-se para começar a usar</p>
    </div>

    <form @submit.prevent="fazerRegistro" class="registro-form">
      <div class="campo">
        <label>Nome</label>
        <InputText
          v-model="nome"
          placeholder="Seu nome completo"
          autofocus
          class="input-full"
        />
      </div>

      <div class="campo">
        <label>E-mail</label>
        <InputText
          v-model="email"
          type="email"
          placeholder="seu@email.com"
          class="input-full"
        />
      </div>

      <div class="campo">
        <label>Senha</label>
        <div class="input-senha-wrapper">
          <InputText
            v-model="senha"
            :type="mostrarSenha ? 'text' : 'password'"
            placeholder="Mínimo 8 caracteres"
            class="input-full"
          />
          <button
            type="button"
            class="btn-mostrar-senha"
            @click="mostrarSenha = !mostrarSenha"
          >
            <Eye v-if="!mostrarSenha" :size="18" />
            <EyeOff v-else :size="18" />
          </button>
        </div>
        <small class="hint" :class="{ valid: senhaValida }">
          {{ senhaValida ? '✓' : '○' }} 8+ caracteres, com letras e números
        </small>
      </div>

      <div class="campo campo-codigo">
        <label>
          <Key :size="14" style="display: inline; margin-right: 4px" />
          Código de cadastro
        </label>
        <InputText
          v-model="codigoCadastro"
          placeholder="Código de acesso ao sistema"
          class="input-full"
        />
        <small class="hint">🔒 Código secreto fornecido pelo administrador</small>
      </div>

      <Button
        type="submit"
        :loading="carregando"
        :disabled="!formValido"
        class="btn-criar"
      >
        <UserPlus :size="18" style="margin-right: 8px" />
        Criar minha conta
      </Button>

      <RouterLink to="/login" class="link-voltar">
        <ArrowLeft :size="14" />
        Já tenho conta — Fazer login
      </RouterLink>
    </form>
  </div>
</template>

<style scoped>
.registro-card {
  background: var(--bg-glass-strong);
  backdrop-filter: blur(30px) saturate(180%);
  -webkit-backdrop-filter: blur(30px) saturate(180%);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: 40px;
  box-shadow: var(--shadow-lg), var(--shadow-glow-primary);
  animation: entrar 500ms cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes entrar {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.registro-header {
  text-align: center;
  margin-bottom: 32px;
}

.brand-badge {
  width: 56px; height: 56px;
  border-radius: var(--radius-lg);
  background: var(--gradient-primary);
  display: flex; align-items: center; justify-content: center;
  color: white;
  margin: 0 auto var(--space-4);
  box-shadow: var(--shadow-glow-primary);
}

.registro-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.subtitle {
  color: var(--text-muted);
  font-size: var(--text-sm);
  margin-top: 4px;
}

.registro-form {
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

.campo-codigo label {
  color: var(--brand-primary);
}

:deep(.input-full) {
  width: 100%;
  height: 42px;
  padding: 0 14px;
  font-family: var(--font-ui);
  font-size: var(--text-base);
}

.input-senha-wrapper {
  position: relative;
  display: flex;
}

.input-senha-wrapper :deep(.input-full) {
  padding-right: 44px;
}

.btn-mostrar-senha {
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

.btn-mostrar-senha:hover {
  color: var(--brand-primary);
}

.hint {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.hint.valid {
  color: var(--success);
}

.btn-criar {
  width: 100%;
  height: 48px;
  font-size: var(--text-base) !important;
  font-weight: 600 !important;
  margin-top: var(--space-2);
}

.link-voltar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  border-radius: var(--radius-md);
  transition: all 200ms ease;
}

.link-voltar:hover {
  color: var(--brand-primary);
  background: var(--bg-hover);
}
</style>
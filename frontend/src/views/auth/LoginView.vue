<script setup lang="ts">
import { ref } from "vue"
import { useRouter, RouterLink } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useToast } from "primevue/usetoast"
import Button from "primevue/button"
import InputText from "primevue/inputtext"
import { Sparkles, LogIn, ArrowRight, Eye, EyeOff } from "lucide-vue-next"

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const email = ref("")
const senha = ref("")
const mostrarSenha = ref(false)
const carregando = ref(false)

async function fazerLogin() {
  if (!email.value || !senha.value) {
    toast.add({
      severity: "warn",
      summary: "Preencha e-mail e senha",
      life: 3000
    })
    return
  }

  carregando.value = true
  try {
    await auth.login({ email: email.value, senha: senha.value })
    toast.add({
      severity: "success",
      summary: `Bem-vindo, ${auth.nome}!`,
      life: 3000
    })
    const destino = router.currentRoute.value.query.redirect as string || "/"
    router.push(destino)
  } catch (e: any) {
    toast.add({
      severity: "error",
      summary: "Falha no login",
      detail: e.message || "Verifique e-mail e senha",
      life: 5000
    })
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div class="login-card">
    <div class="login-header">
      <div class="brand-badge">
        <Sparkles :size="24" />
      </div>
      <h1>Finanças</h1>
      <p class="subtitle">Seu sistema financeiro pessoal</p>
    </div>

    <form @submit.prevent="fazerLogin" class="login-form">
      <div class="campo">
        <label for="email">E-mail</label>
        <InputText
          id="email"
          v-model="email"
          type="email"
          placeholder="seu@email.com"
          autofocus
          class="input-full"
        />
      </div>

      <div class="campo">
        <label for="senha">Senha</label>
        <div class="input-senha-wrapper">
          <InputText
            id="senha"
            v-model="senha"
            :type="mostrarSenha ? 'text' : 'password'"
            placeholder="Sua senha"
            class="input-full"
          />
          <button
            type="button"
            class="btn-mostrar-senha"
            @click="mostrarSenha = !mostrarSenha"
            :title="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'"
          >
            <Eye v-if="!mostrarSenha" :size="18" />
            <EyeOff v-else :size="18" />
          </button>
        </div>
      </div>

      <Button
        type="submit"
        :loading="carregando"
        class="btn-entrar"
      >
        <LogIn :size="18" style="margin-right: 8px" />
        Entrar
        <ArrowRight :size="18" style="margin-left: 8px" />
      </Button>

      <div class="separador">
        <span>ou</span>
      </div>

      <RouterLink to="/registro" class="link-registro">
        Ainda não tenho conta — <strong>Criar agora</strong>
      </RouterLink>
    </form>

    <p class="footer-nota">
      Feito com 💜 por Rafael · 2026
    </p>
  </div>
</template>

<style scoped>
.login-card {
  background: var(--bg-glass-strong);
  backdrop-filter: blur(30px) saturate(180%);
  -webkit-backdrop-filter: blur(30px) saturate(180%);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: 48px 40px;
  box-shadow: var(--shadow-lg), var(--shadow-glow-primary);
  animation: entrar 500ms cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes entrar {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
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

.login-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}

.subtitle {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.login-form {
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
  height: 44px;
  padding: 0 16px;
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

.btn-entrar {
  width: 100%;
  height: 48px;
  font-size: var(--text-base) !important;
  font-weight: 600 !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  margin-top: var(--space-2);
}

.separador {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-3) 0;
}

.separador::before,
.separador::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}

.separador span {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-weight: 600;
}

.link-registro {
  text-align: center;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  text-decoration: none;
  transition: all 200ms ease;
  border: 1px solid var(--border-subtle);
  display: block;
}

.link-registro:hover {
  background: var(--bg-hover);
  color: var(--brand-primary);
  border-color: var(--brand-primary);
}

.link-registro strong {
  color: var(--brand-primary);
}

.footer-nota {
  text-align: center;
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 32px;
  opacity: 0.7;
}
</style>
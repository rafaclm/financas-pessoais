<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue"
import { RouterLink, RouterView, useRouter, useRoute } from "vue-router"
import { useTemaStore } from "@/stores/tema"
import { useAuthStore } from "@/stores/auth"
import {
  Sun, Moon, Home, Calendar, TrendingDown, TrendingUp, Building2, Wallet,
  CreditCard, PiggyBank, BarChart3, HeartHandshake, HeartCrack, Fuel, Receipt,
  ShoppingCart, Gem, Coins, LineChart, Sparkles, Bitcoin, Flag, Globe, Layers,
  Target, Settings, Activity, Database, Upload, LogOut, Menu as MenuIcon,
  ChevronDown, ChevronRight, PanelLeftClose, PanelLeft,
} from "lucide-vue-next"
import SeletorPeriodo from "@/components/SeletorPeriodo.vue"

const tema = useTemaStore()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// ===========================================
// ESTADO DO MENU (persistido no localStorage)
// ===========================================

// Menu inteiro colapsado ou expandido?
const menuColapsado = ref(false)

// Quais grupos estão abertos?
const gruposAbertos = ref<Record<string, boolean>>({
  patrimonio: true,
  balanceamento: true,
  posicoes: true,
  lancamentos: true,
  cadastros: true,
  configuracoes: true,
})

// Restaura preferências ao iniciar
onMounted(() => {
  const menuState = localStorage.getItem("menu_colapsado")
  if (menuState === "true") menuColapsado.value = true

  const gruposState = localStorage.getItem("menu_grupos")
  if (gruposState) {
    try {
      gruposAbertos.value = { ...gruposAbertos.value, ...JSON.parse(gruposState) }
    } catch { /* ignore */ }
  }
})

// Persiste mudanças
watch(menuColapsado, (v) => {
  localStorage.setItem("menu_colapsado", String(v))
})

watch(gruposAbertos, (v) => {
  localStorage.setItem("menu_grupos", JSON.stringify(v))
}, { deep: true })

// ===========================================
// AÇÕES
// ===========================================

function toggleMenu() {
  menuColapsado.value = !menuColapsado.value
}

function toggleGrupo(grupo: string) {
  gruposAbertos.value[grupo] = !gruposAbertos.value[grupo]
}

function sair() {
  if (!confirm("Tem certeza que deseja sair?")) return
  auth.logout()
  router.push("/login")
}

function irPerfil() {
  router.push("/perfil")
}

// ===========================================
// AUTO-EXPANSÃO INTELIGENTE
// ===========================================

// Se estiver dentro de um grupo, garante que ele está aberto
watch(() => route.path, (path) => {
  if (menuColapsado.value) return // se menu colapsado, não faz nada

  const mapeamento: Record<string, string> = {
    "/posicoes/consolidacao-patrimonial": "patrimonio",
    "/posicoes/posicao-atual": "patrimonio",
    "/posicoes/consolidacao-rv": "patrimonio",
    "/balanceamento/analise": "balanceamento",
    "/balanceamento/config": "balanceamento",
    "/posicoes/saldos-contas": "posicoes",
    "/posicoes/saldos-investimentos": "posicoes",
    "/posicoes/cripto": "posicoes",
    "/posicoes/ativos-br": "posicoes",
    "/posicoes/ativos-eua": "posicoes",
    "/lancamentos/receitas": "lancamentos",
    "/lancamentos/despesas": "lancamentos",
    "/lancamentos/combustivel": "lancamentos",
    "/lancamentos/pagamentos-cartao": "lancamentos",
    "/lancamentos/aportes": "lancamentos",
    "/lancamentos/proventos": "lancamentos",
    "/cadastros/anos": "cadastros",
    "/cadastros/categorias-despesas": "cadastros",
    "/cadastros/categorias-receitas": "cadastros",
    "/cadastros/instituicoes": "cadastros",
    "/cadastros/contas": "cadastros",
    "/cadastros/cartoes": "cadastros",
    "/cadastros/produtos": "cadastros",
    "/cadastros/ativos": "cadastros",
    "/configuracoes/backup": "configuracoes",
    "/configuracoes/importacao": "configuracoes",
  }

  const grupo = mapeamento[path]
  if (grupo) {
    gruposAbertos.value[grupo] = true
  }
}, { immediate: true })

// ===========================================
// GRUPOS DE NAVEGAÇÃO
// ===========================================

const grupos = computed(() => [
  {
    id: "patrimonio",
    label: "Patrimônio",
    icone: Sparkles,
    itens: [
      { to: "/posicoes/consolidacao-patrimonial", label: "Patrimônio Total", icone: Sparkles },
      { to: "/posicoes/posicao-atual", label: "Posição Atual", icone: Activity },
      { to: "/posicoes/consolidacao-rv", label: "Renda Variável", icone: Layers },
    ],
  },
  {
    id: "balanceamento",
    label: "Balanceamento",
    icone: Target,
    itens: [
      { to: "/balanceamento/analise", label: "Análise (Rebalancear)", icone: Target },
      { to: "/balanceamento/config", label: "Config. Metas", icone: Settings },
    ],
  },
  {
    id: "posicoes",
    label: "Posições mensais",
    icone: BarChart3,
    itens: [
      { to: "/posicoes/saldos-contas", label: "Saldos Contas", icone: Coins },
      { to: "/posicoes/saldos-investimentos", label: "Saldos Inv.", icone: LineChart },
      { to: "/posicoes/cripto", label: "Criptoativos", icone: Bitcoin },
      { to: "/posicoes/ativos-br", label: "Ativos BR", icone: Flag },
      { to: "/posicoes/ativos-eua", label: "Ativos EUA", icone: Globe },
    ],
  },
  {
    id: "lancamentos",
    label: "Lançamentos",
    icone: Receipt,
    itens: [
      { to: "/lancamentos/receitas", label: "Receitas", icone: HeartHandshake },
      { to: "/lancamentos/despesas", label: "Despesas", icone: HeartCrack },
      { to: "/lancamentos/combustivel", label: "Combustível", icone: Fuel },
      { to: "/lancamentos/pagamentos-cartao", label: "Pag. Cartão", icone: Receipt },
      { to: "/lancamentos/aportes", label: "Aportes", icone: ShoppingCart },
      { to: "/lancamentos/proventos", label: "Proventos", icone: Gem },
    ],
  },
  {
    id: "cadastros",
    label: "Cadastros",
    icone: Building2,
    itens: [
      { to: "/cadastros/anos", label: "Anos", icone: Calendar },
      { to: "/cadastros/categorias-despesas", label: "Cat. Despesas", icone: TrendingDown },
      { to: "/cadastros/categorias-receitas", label: "Cat. Receitas", icone: TrendingUp },
      { to: "/cadastros/instituicoes", label: "Instituições", icone: Building2 },
      { to: "/cadastros/contas", label: "Contas", icone: Wallet },
      { to: "/cadastros/cartoes", label: "Cartões", icone: CreditCard },
      { to: "/cadastros/produtos", label: "Produtos Inv.", icone: PiggyBank },
      { to: "/cadastros/ativos", label: "Ativos", icone: BarChart3 },
    ],
  },
  {
    id: "configuracoes",
    label: "Configurações",
    icone: Settings,
    itens: [
      { to: "/configuracoes/backup", label: "Backup e Restore", icone: Database },
      { to: "/configuracoes/importacao", label: "Importar Planilha", icone: Upload },
    ],
  },
])
</script>

<template>
  <div class="app-shell" :class="{ 'menu-colapsado': menuColapsado }">
    <aside class="sidebar">
      <!-- HEADER: Logo + Botão de ocultar -->
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon">
            <Sparkles :size="20" />
          </div>
          <span v-if="!menuColapsado" class="brand-nome">Finanças</span>
        </div>
        <button
          class="btn-toggle-menu"
          @click="toggleMenu"
          :title="menuColapsado ? 'Expandir menu' : 'Recolher menu'"
        >
          <PanelLeft v-if="menuColapsado" :size="16" />
          <PanelLeftClose v-else :size="16" />
        </button>
      </div>

      <nav class="menu-scroll">
        <!-- Início (sempre visível, sem grupo) -->
        <RouterLink to="/" class="nav-item" :title="menuColapsado ? 'Início' : ''">
          <Home :size="18" />
          <span v-if="!menuColapsado">Início</span>
        </RouterLink>

        <!-- Grupos colapsáveis -->
        <div v-for="grupo in grupos" :key="grupo.id" class="grupo">
          <!-- Título do grupo (clicável) -->
          <button
            v-if="!menuColapsado"
            class="grupo-header"
            @click="toggleGrupo(grupo.id)"
          >
            <MenuIcon :size="14" class="grupo-icone-menu" />
            <span class="grupo-label">{{ grupo.label }}</span>
            <ChevronDown v-if="gruposAbertos[grupo.id]" :size="14" class="grupo-chevron" />
            <ChevronRight v-else :size="14" class="grupo-chevron" />
          </button>

          <!-- Itens do grupo -->
          <transition name="collapse">
            <div v-if="menuColapsado || gruposAbertos[grupo.id]" class="grupo-itens">
              <RouterLink
                v-for="item in grupo.itens"
                :key="item.to"
                :to="item.to"
                class="nav-item"
                :title="menuColapsado ? item.label : ''"
              >
                <component :is="item.icone" :size="18" />
                <span v-if="!menuColapsado">{{ item.label }}</span>
              </RouterLink>
            </div>
          </transition>

          <!-- Separador visual entre grupos quando colapsado -->
          <div v-if="menuColapsado" class="separador-colapsado"></div>
        </div>
      </nav>

      <!-- USUARIO FOOTER -->
      <div class="usuario-footer">
        <button
          class="usuario-info"
          @click="irPerfil"
          :title="menuColapsado ? `${auth.nome} - Ver perfil` : 'Ver perfil'"
        >
          <div class="usuario-avatar">{{ auth.iniciais }}</div>
          <div v-if="!menuColapsado" class="usuario-dados">
            <span class="usuario-nome">{{ auth.nome }}</span>
            <span class="usuario-email">{{ auth.email }}</span>
          </div>
        </button>
        <button
          v-if="!menuColapsado"
          class="btn-sair"
          @click="sair"
          title="Sair do sistema"
        >
          <LogOut :size="16" />
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <SeletorPeriodo />
        <div class="topbar-actions">
          <button
            v-if="menuColapsado"
            class="theme-toggle"
            @click="sair"
            title="Sair"
          >
            <LogOut :size="18" />
          </button>
          <button
            class="theme-toggle"
            @click="tema.toggle()"
            :title="tema.tema === 'dark' ? 'Modo claro' : 'Modo escuro'"
          >
            <Sun v-if="tema.tema === 'dark'" :size="18" />
            <Moon v-else :size="18" />
          </button>
        </div>
      </header>
      <main class="content"><RouterView /></main>
    </div>
  </div>
</template>

<style scoped>
/* ===========================================
   LAYOUT PRINCIPAL
   =========================================== */
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100vh;
  transition: grid-template-columns 250ms cubic-bezier(0.16, 1, 0.3, 1);
}

.app-shell.menu-colapsado {
  grid-template-columns: 68px 1fr;
}

/* ===========================================
   SIDEBAR
   =========================================== */
.sidebar {
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  padding: var(--space-3) var(--space-2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.menu-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}

.menu-scroll::-webkit-scrollbar {
  width: 4px;
}

.menu-scroll::-webkit-scrollbar-thumb {
  background: var(--border-default);
  border-radius: 2px;
}

/* ===========================================
   HEADER DA SIDEBAR (Logo + Botão toggle)
   =========================================== */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-2);
  margin-bottom: var(--space-4);
  min-height: 48px;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  overflow: hidden;
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  color: white;
  box-shadow: var(--shadow-glow-primary);
  flex-shrink: 0;
}

.brand-nome {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.btn-toggle-menu {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease;
  flex-shrink: 0;
}

.btn-toggle-menu:hover {
  background: var(--bg-hover);
  color: var(--brand-primary);
  border-color: var(--brand-primary);
}

.menu-colapsado .sidebar-header {
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-1);
}

.menu-colapsado .brand {
  justify-content: center;
}

/* ===========================================
   GRUPOS COLAPSAVEIS
   =========================================== */
.grupo {
  margin-bottom: var(--space-2);
}

.grupo-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: var(--space-2) var(--space-3);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 700;
  cursor: pointer;
  transition: all 180ms ease;
  border-radius: var(--radius-sm);
  text-align: left;
}

.grupo-header:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.grupo-icone-menu {
  opacity: 0.5;
  flex-shrink: 0;
}

.grupo-label {
  flex: 1;
}

.grupo-chevron {
  transition: transform 200ms ease;
  opacity: 0.7;
}

.grupo-itens {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 4px;
  padding-left: var(--space-1);
}

/* ===========================================
   ITENS DE NAVEGACAO
   =========================================== */
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all 180ms ease;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.router-link-exact-active {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--shadow-glow-primary);
  font-weight: 600;
}

/* Modo colapsado: itens centralizados */
.menu-colapsado .nav-item {
  justify-content: center;
  padding: var(--space-3) var(--space-2);
}

.menu-colapsado .grupo-itens {
  padding-left: 0;
  padding-top: 0;
}

/* Separador quando colapsado */
.separador-colapsado {
  height: 1px;
  background: var(--border-subtle);
  margin: var(--space-2) var(--space-3);
}

/* ===========================================
   ANIMACAO DE COLAPSAR
   =========================================== */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* ===========================================
   USUARIO FOOTER
   =========================================== */
.usuario-footer {
  padding: var(--space-2);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-top: var(--space-3);
}

.usuario-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-md);
  text-align: left;
  color: inherit;
  transition: background 180ms ease;
}

.usuario-info:hover {
  background: var(--bg-surface);
}

.usuario-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: var(--text-xs);
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.usuario-dados {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.usuario-nome {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usuario-email {
  font-size: 10px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-sair {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease;
  flex-shrink: 0;
}

.btn-sair:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

.menu-colapsado .usuario-footer {
  justify-content: center;
  padding: var(--space-1);
}

.menu-colapsado .usuario-info {
  justify-content: center;
  padding: 4px;
}

/* ===========================================
   MAIN AREA
   =========================================== */
.main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-base);
}

.topbar {
  height: 68px;
  padding: 0 var(--space-6);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.theme-toggle {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  padding: 10px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 200ms ease;
}

.theme-toggle:hover {
  background: var(--bg-hover);
  color: var(--brand-primary);
  border-color: var(--brand-primary);
}

.content {
  padding: var(--space-6);
  overflow-y: auto;
  flex: 1;
}

/* ===========================================
   RESPONSIVO MOBILE
   =========================================== */
@media (max-width: 768px) {
  .app-shell {
    grid-template-columns: 68px 1fr;
  }

  .app-shell:not(.menu-colapsado) {
    grid-template-columns: 240px 1fr;
  }
}
</style>
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
  ChevronDown, ChevronRight, PanelLeftClose, PanelLeft, X,
} from "lucide-vue-next"
import SeletorPeriodo from "@/components/SeletorPeriodo.vue"

const tema = useTemaStore()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// Detecta se e mobile
const ehMobile = ref(window.innerWidth <= 768)
window.addEventListener("resize", () => {
  ehMobile.value = window.innerWidth <= 768
})

// Menu colapsado (desktop) / aberto (mobile)
const menuColapsado = ref(false)
// No mobile, controla se o menu-overlay esta aberto
const menuMobileAberto = ref(false)

const gruposAbertos = ref<Record<string, boolean>>({
  patrimonio: true, balanceamento: true, posicoes: true,
  lancamentos: true, cadastros: true, configuracoes: true,
})

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

watch(menuColapsado, (v) => localStorage.setItem("menu_colapsado", String(v)))
watch(gruposAbertos, (v) => localStorage.setItem("menu_grupos", JSON.stringify(v)), { deep: true })

// Fecha menu mobile ao trocar de rota
watch(() => route.path, () => {
  if (ehMobile.value) menuMobileAberto.value = false
})

function toggleMenu() {
  if (ehMobile.value) {
    menuMobileAberto.value = !menuMobileAberto.value
  } else {
    menuColapsado.value = !menuColapsado.value
  }
}

function fecharMenuMobile() {
  menuMobileAberto.value = false
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
  if (ehMobile.value) menuMobileAberto.value = false
}

watch(() => route.path, (path) => {
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
  if (grupo) gruposAbertos.value[grupo] = true
}, { immediate: true })

const grupos = computed(() => [
  {
    id: "patrimonio", label: "Patrimônio", itens: [
      { to: "/posicoes/consolidacao-patrimonial", label: "Patrimônio Total", icone: Sparkles },
      { to: "/posicoes/posicao-atual", label: "Posição Atual", icone: Activity },
      { to: "/posicoes/consolidacao-rv", label: "Renda Variável", icone: Layers },
    ],
  },
  {
    id: "balanceamento", label: "Balanceamento", itens: [
      { to: "/balanceamento/analise", label: "Análise (Rebalancear)", icone: Target },
      { to: "/balanceamento/config", label: "Config. Metas", icone: Settings },
    ],
  },
  {
    id: "posicoes", label: "Posições mensais", itens: [
      { to: "/posicoes/saldos-contas", label: "Saldos Contas", icone: Coins },
      { to: "/posicoes/saldos-investimentos", label: "Saldos Inv.", icone: LineChart },
      { to: "/posicoes/cripto", label: "Criptoativos", icone: Bitcoin },
      { to: "/posicoes/ativos-br", label: "Ativos BR", icone: Flag },
      { to: "/posicoes/ativos-eua", label: "Ativos EUA", icone: Globe },
    ],
  },
  {
    id: "lancamentos", label: "Lançamentos", itens: [
      { to: "/lancamentos/receitas", label: "Receitas", icone: HeartHandshake },
      { to: "/lancamentos/despesas", label: "Despesas", icone: HeartCrack },
      { to: "/lancamentos/combustivel", label: "Combustível", icone: Fuel },
      { to: "/lancamentos/pagamentos-cartao", label: "Pag. Cartão", icone: Receipt },
      { to: "/lancamentos/aportes", label: "Aportes", icone: ShoppingCart },
      { to: "/lancamentos/proventos", label: "Proventos", icone: Gem },
    ],
  },
  {
    id: "cadastros", label: "Cadastros", itens: [
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
    id: "configuracoes", label: "Configurações", itens: [
      { to: "/configuracoes/backup", label: "Backup e Restore", icone: Database },
      { to: "/configuracoes/importacao", label: "Importar Planilha", icone: Upload },
    ],
  },
])

// Estado visual: menu visivel?
const menuVisivel = computed(() => {
  if (ehMobile.value) return menuMobileAberto.value
  return !menuColapsado.value
})
</script>

<template>
  <div class="app-shell"
       :class="{ 'menu-colapsado': !ehMobile && menuColapsado, 'mobile': ehMobile }">

    <!-- Overlay escuro (mobile) -->
    <div v-if="ehMobile && menuMobileAberto" class="overlay-mobile" @click="fecharMenuMobile"></div>

    <aside class="sidebar" :class="{ 'sidebar-aberta': menuVisivel }">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon"><Sparkles :size="20" /></div>
          <span v-if="!menuColapsado || ehMobile" class="brand-nome">Finanças</span>
        </div>
        <!-- Botao fechar (dentro do menu) -->
        <button class="btn-toggle-menu" @click="toggleMenu"
                :title="ehMobile ? 'Fechar menu' : 'Recolher menu'">
          <X v-if="ehMobile" :size="18" />
          <PanelLeft v-else-if="menuColapsado" :size="16" />
          <PanelLeftClose v-else :size="16" />
        </button>
      </div>

      <nav class="menu-scroll">
        <RouterLink to="/" class="nav-item" :title="menuColapsado && !ehMobile ? 'Início' : ''">
          <Home :size="18" />
          <span v-if="!menuColapsado || ehMobile">Início</span>
        </RouterLink>

        <div v-for="grupo in grupos" :key="grupo.id" class="grupo">
          <button v-if="!menuColapsado || ehMobile" class="grupo-header" @click="toggleGrupo(grupo.id)">
            <MenuIcon :size="14" class="grupo-icone-menu" />
            <span class="grupo-label">{{ grupo.label }}</span>
            <ChevronDown v-if="gruposAbertos[grupo.id]" :size="14" class="grupo-chevron" />
            <ChevronRight v-else :size="14" class="grupo-chevron" />
          </button>

          <transition name="collapse">
            <div v-if="(menuColapsado && !ehMobile) || gruposAbertos[grupo.id]" class="grupo-itens">
              <RouterLink v-for="item in grupo.itens" :key="item.to" :to="item.to"
                          class="nav-item" :title="menuColapsado && !ehMobile ? item.label : ''">
                <component :is="item.icone" :size="18" />
                <span v-if="!menuColapsado || ehMobile">{{ item.label }}</span>
              </RouterLink>
            </div>
          </transition>

          <div v-if="menuColapsado && !ehMobile" class="separador-colapsado"></div>
        </div>
      </nav>

      <div class="usuario-footer">
        <button class="usuario-info" @click="irPerfil">
          <div class="usuario-avatar">{{ auth.iniciais }}</div>
          <div v-if="!menuColapsado || ehMobile" class="usuario-dados">
            <span class="usuario-nome">{{ auth.nome }}</span>
            <span class="usuario-email">{{ auth.email }}</span>
          </div>
        </button>
        <button v-if="!menuColapsado || ehMobile" class="btn-sair" @click="sair" title="Sair">
          <LogOut :size="16" />
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar-left">
          <!-- 🍔 Botao hamburguer SEMPRE visivel no mobile -->
          <button v-if="ehMobile" class="btn-hamburguer" @click="toggleMenu" title="Menu">
            <MenuIcon :size="22" />
          </button>
          <SeletorPeriodo />
        </div>
        <div class="topbar-actions">
          <button v-if="ehMobile" class="theme-toggle" @click="sair" title="Sair">
            <LogOut :size="18" />
          </button>
          <button class="theme-toggle" @click="tema.toggle()"
                  :title="tema.tema === 'dark' ? 'Modo claro' : 'Modo escuro'">
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
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100vh;
  transition: grid-template-columns 250ms cubic-bezier(0.16, 1, 0.3, 1);
}
.app-shell.menu-colapsado { grid-template-columns: 68px 1fr; }

/* No mobile, so 1 coluna (menu vira overlay) */
.app-shell.mobile { grid-template-columns: 1fr; }

.sidebar {
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  padding: var(--space-3) var(--space-2);
  padding-top: calc(var(--space-3) + env(safe-area-inset-top, 0px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* Sidebar como overlay no mobile */
.app-shell.mobile .sidebar {
  position: fixed;
  top: 0; left: 0;
  height: 100vh;
  width: 270px;
  z-index: 100;
  transform: translateX(-100%);
  transition: transform 280ms cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4);
}
.app-shell.mobile .sidebar.sidebar-aberta {
  transform: translateX(0);
}

.overlay-mobile {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 99;
  backdrop-filter: blur(2px);
}

.menu-scroll { flex: 1; overflow-y: auto; overflow-x: hidden; padding-right: 4px; }
.menu-scroll::-webkit-scrollbar { width: 4px; }
.menu-scroll::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 2px; }

.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--space-2); margin-bottom: var(--space-4); min-height: 48px;
}
.brand { display: flex; align-items: center; gap: var(--space-3); overflow: hidden; }
.brand-icon {
  width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
  background: var(--gradient-primary); border-radius: var(--radius-md);
  color: white; box-shadow: var(--shadow-glow-primary); flex-shrink: 0;
}
.brand-nome { font-size: var(--text-lg); font-weight: 700; color: var(--text-primary); white-space: nowrap; }

.btn-toggle-menu {
  background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  transition: all 200ms ease; flex-shrink: 0;
}
.btn-toggle-menu:hover { background: var(--bg-hover); color: var(--brand-primary); }

.menu-colapsado .sidebar-header { flex-direction: column; gap: var(--space-2); padding: var(--space-1); }
.menu-colapsado .brand { justify-content: center; }

.grupo { margin-bottom: var(--space-2); }
.grupo-header {
  display: flex; align-items: center; gap: var(--space-2); width: 100%;
  background: transparent; border: none; color: var(--text-muted);
  padding: var(--space-2) var(--space-3); font-size: 10px; text-transform: uppercase;
  letter-spacing: 0.12em; font-weight: 700; cursor: pointer;
  transition: all 180ms ease; border-radius: var(--radius-sm); text-align: left;
}
.grupo-header:hover { background: var(--bg-hover); color: var(--text-secondary); }
.grupo-icone-menu { opacity: 0.5; flex-shrink: 0; }
.grupo-label { flex: 1; }
.grupo-chevron { opacity: 0.7; }
.grupo-itens { display: flex; flex-direction: column; gap: 2px; padding-top: 4px; padding-left: var(--space-1); }

.nav-item {
  display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3);
  border-radius: var(--radius-md); text-decoration: none; color: var(--text-secondary);
  font-size: var(--text-sm); font-weight: 500; transition: all 180ms ease;
  white-space: nowrap; overflow: hidden;
}
.nav-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-item.router-link-exact-active {
  background: var(--gradient-primary); color: white;
  box-shadow: var(--shadow-glow-primary); font-weight: 600;
}
.menu-colapsado .nav-item { justify-content: center; padding: var(--space-3) var(--space-2); }
.menu-colapsado .grupo-itens { padding-left: 0; padding-top: 0; }
.separador-colapsado { height: 1px; background: var(--border-subtle); margin: var(--space-2) var(--space-3); }

.collapse-enter-active, .collapse-leave-active { transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1); overflow: hidden; }
.collapse-enter-from, .collapse-leave-to { opacity: 0; max-height: 0; }
.collapse-enter-to, .collapse-leave-from { opacity: 1; max-height: 500px; }

.usuario-footer {
  padding: var(--space-2); border-top: 1px solid var(--border-subtle);
  display: flex; align-items: center; gap: var(--space-2);
  background: var(--bg-elevated); border-radius: var(--radius-md); margin-top: var(--space-3);
  padding-bottom: calc(var(--space-2) + env(safe-area-inset-bottom, 0px));
}
.usuario-info {
  display: flex; align-items: center; gap: var(--space-2); flex: 1; min-width: 0;
  background: transparent; border: none; cursor: pointer; padding: 8px;
  border-radius: var(--radius-md); text-align: left; color: inherit; transition: background 180ms ease;
}
.usuario-info:hover { background: var(--bg-surface); }
.usuario-avatar {
  width: 36px; height: 36px; border-radius: var(--radius-full);
  background: var(--gradient-primary); display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: var(--text-xs); flex-shrink: 0;
}
.usuario-dados { display: flex; flex-direction: column; min-width: 0; }
.usuario-nome { font-size: var(--text-xs); font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.usuario-email { font-size: 10px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-sair {
  background: transparent; border: none; color: var(--text-muted); cursor: pointer;
  padding: 8px; border-radius: var(--radius-md); display: flex; align-items: center;
  justify-content: center; transition: all 200ms ease; flex-shrink: 0;
}
.btn-sair:hover { background: var(--danger-bg); color: var(--danger); }
.menu-colapsado .usuario-footer { justify-content: center; padding: var(--space-1); }
.menu-colapsado .usuario-info { justify-content: center; padding: 4px; }

.main { display: flex; flex-direction: column; overflow: hidden; background: var(--bg-base); }

/* 🍎 TOPBAR com safe area */
.topbar {
  padding: 0 var(--space-6);
  padding-top: env(safe-area-inset-top, 0px);
  height: calc(68px + env(safe-area-inset-top, 0px));
  display: flex; justify-content: space-between; align-items: center;
  background: var(--bg-surface); border-bottom: 1px solid var(--border-subtle);
}
.topbar-left { display: flex; align-items: center; gap: var(--space-3); }

.btn-hamburguer {
  background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  color: var(--text-primary); border-radius: var(--radius-md); padding: 8px;
  display: flex; align-items: center; cursor: pointer; transition: all 200ms ease;
}
.btn-hamburguer:hover { background: var(--brand-primary); color: white; }

.topbar-actions { display: flex; align-items: center; gap: var(--space-3); }
.theme-toggle {
  background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  color: var(--text-secondary); border-radius: var(--radius-md); padding: 10px;
  display: flex; align-items: center; cursor: pointer; transition: all 200ms ease;
}
.theme-toggle:hover { background: var(--bg-hover); color: var(--brand-primary); }

.content {
  padding: var(--space-6); overflow-y: auto; flex: 1;
  padding-bottom: calc(var(--space-6) + env(safe-area-inset-bottom, 0px));
}
</style>
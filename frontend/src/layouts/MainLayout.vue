<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from "vue-router"
import { useTemaStore } from "@/stores/tema"
import { useAuthStore } from "@/stores/auth"
import { Sun, Moon, Home, Calendar, TrendingDown, TrendingUp, Building2, Wallet, CreditCard, PiggyBank, BarChart3, HeartHandshake, HeartCrack, Fuel, Receipt, ShoppingCart, Gem, Coins, LineChart, Sparkles, Bitcoin, Flag, Globe, Layers, Target, Settings, Activity, Database, Upload, LogOut, User } from "lucide-vue-next"
import SeletorPeriodo from "@/components/SeletorPeriodo.vue"

const tema = useTemaStore()
const auth = useAuthStore()
const router = useRouter()

function sair() {
  if (!confirm("Tem certeza que deseja sair?")) return
  auth.logout()
  router.push("/login")
}

function irPerfil() {
  router.push("/perfil")
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">
          <Sparkles :size="20" />
        </div>
        <span class="brand-nome">Finanças</span>
      </div>

      <nav>
        <RouterLink to="/" class="nav-item">
          <Home :size="18" />
          <span>Início</span>
        </RouterLink>

        <div class="nav-group">Patrimônio</div>
        <RouterLink to="/posicoes/consolidacao-patrimonial" class="nav-item">
          <Sparkles :size="18" /> <span>Patrimônio Total</span>
        </RouterLink>
        <RouterLink to="/posicoes/posicao-atual" class="nav-item">
          <Activity :size="18" /> <span>Posição Atual</span>
        </RouterLink>
        <RouterLink to="/posicoes/consolidacao-rv" class="nav-item">
          <Layers :size="18" /> <span>Renda Variável</span>
        </RouterLink>

        <div class="nav-group">Balanceamento</div>
        <RouterLink to="/balanceamento/analise" class="nav-item">
          <Target :size="18" /> <span>Análise (Rebalancear)</span>
        </RouterLink>
        <RouterLink to="/balanceamento/config" class="nav-item">
          <Settings :size="18" /> <span>Config. Metas</span>
        </RouterLink>

        <div class="nav-group">Posições mensais</div>
        <RouterLink to="/posicoes/saldos-contas" class="nav-item">
          <Coins :size="18" /> <span>Saldos Contas</span>
        </RouterLink>
        <RouterLink to="/posicoes/saldos-investimentos" class="nav-item">
          <LineChart :size="18" /> <span>Saldos Inv.</span>
        </RouterLink>
        <RouterLink to="/posicoes/cripto" class="nav-item">
          <Bitcoin :size="18" /> <span>Criptoativos</span>
        </RouterLink>
        <RouterLink to="/posicoes/ativos-br" class="nav-item">
          <Flag :size="18" /> <span>Ativos BR</span>
        </RouterLink>
        <RouterLink to="/posicoes/ativos-eua" class="nav-item">
          <Globe :size="18" /> <span>Ativos EUA</span>
        </RouterLink>

        <div class="nav-group">Lançamentos</div>
        <RouterLink to="/lancamentos/receitas" class="nav-item"><HeartHandshake :size="18" /><span>Receitas</span></RouterLink>
        <RouterLink to="/lancamentos/despesas" class="nav-item"><HeartCrack :size="18" /><span>Despesas</span></RouterLink>
        <RouterLink to="/lancamentos/combustivel" class="nav-item"><Fuel :size="18" /><span>Combustível</span></RouterLink>
        <RouterLink to="/lancamentos/pagamentos-cartao" class="nav-item"><Receipt :size="18" /><span>Pag. Cartão</span></RouterLink>
        <RouterLink to="/lancamentos/aportes" class="nav-item"><ShoppingCart :size="18" /><span>Aportes</span></RouterLink>
        <RouterLink to="/lancamentos/proventos" class="nav-item"><Gem :size="18" /><span>Proventos</span></RouterLink>

        <div class="nav-group">Cadastros</div>
        <RouterLink to="/cadastros/anos" class="nav-item"><Calendar :size="18" /><span>Anos</span></RouterLink>
        <RouterLink to="/cadastros/categorias-despesas" class="nav-item"><TrendingDown :size="18" /><span>Cat. Despesas</span></RouterLink>
        <RouterLink to="/cadastros/categorias-receitas" class="nav-item"><TrendingUp :size="18" /><span>Cat. Receitas</span></RouterLink>
        <RouterLink to="/cadastros/instituicoes" class="nav-item"><Building2 :size="18" /><span>Instituições</span></RouterLink>
        <RouterLink to="/cadastros/contas" class="nav-item"><Wallet :size="18" /><span>Contas</span></RouterLink>
        <RouterLink to="/cadastros/cartoes" class="nav-item"><CreditCard :size="18" /><span>Cartões</span></RouterLink>
        <RouterLink to="/cadastros/produtos" class="nav-item"><PiggyBank :size="18" /><span>Produtos Inv.</span></RouterLink>
        <RouterLink to="/cadastros/ativos" class="nav-item"><BarChart3 :size="18" /><span>Ativos</span></RouterLink>

        <div class="nav-group">Configurações</div>
        <RouterLink to="/configuracoes/backup" class="nav-item">
          <Database :size="18" /> <span>Backup e Restore</span>
        </RouterLink>
        <RouterLink to="/configuracoes/importacao" class="nav-item">
          <Upload :size="18" /> <span>Importar Planilha</span>
        </RouterLink>
      </nav>

      <div class="usuario-footer">
        <button class="usuario-info" @click="irPerfil" title="Ver perfil">
          <div class="usuario-avatar">{{ auth.iniciais }}</div>
          <div class="usuario-dados">
            <span class="usuario-nome">{{ auth.nome }}</span>
            <span class="usuario-email">{{ auth.email }}</span>
          </div>
        </button>
        <button class="btn-sair" @click="sair" title="Sair do sistema">
          <LogOut :size="16" />
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <SeletorPeriodo />
        <div class="topbar-actions">
          <button class="theme-toggle" @click="tema.toggle()" :title="tema.tema === 'dark' ? 'Modo claro' : 'Modo escuro'">
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
}

.sidebar {
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  margin-bottom: var(--space-6);
}
.brand-icon {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  color: white;
  box-shadow: var(--shadow-glow-primary);
}
.brand-nome {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.nav-group {
  font-size: 10px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: var(--space-4) var(--space-3) var(--space-2);
  letter-spacing: 0.1em;
  font-weight: 600;
}

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

.usuario-footer {
  margin-top: auto;
  padding: var(--space-2);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-top: var(--space-4);
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
  width: 36px; height: 36px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  display: flex; align-items: center; justify-content: center;
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
}
.btn-sair:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

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
</style>
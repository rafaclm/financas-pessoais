import { createRouter, createWebHistory } from "vue-router"
import { requerAutenticacao, apenasNaoAutenticado } from "./guards"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      component: () => import("@/layouts/AuthLayout.vue"),
      beforeEnter: apenasNaoAutenticado,
      children: [
        {
          path: "",
          name: "login",
          component: () => import("@/views/auth/LoginView.vue"),
        },
      ],
    },
    {
      path: "/registro",
      component: () => import("@/layouts/AuthLayout.vue"),
      beforeEnter: apenasNaoAutenticado,
      children: [
        {
          path: "",
          name: "registro",
          component: () => import("@/views/auth/RegistroView.vue"),
        },
      ],
    },

    {
      path: "/",
      component: () => import("@/layouts/MainLayout.vue"),
      beforeEnter: requerAutenticacao,
      children: [
        { path: "", name: "home", component: () => import("@/views/HomeView.vue") },
        { path: "perfil", name: "perfil", component: () => import("@/views/auth/PerfilView.vue") },
        { path: "cadastros/anos", component: () => import("@/views/cadastros/AnosView.vue") },
        { path: "cadastros/categorias-despesas", component: () => import("@/views/cadastros/CategoriasDespesasView.vue") },
        { path: "cadastros/categorias-receitas", component: () => import("@/views/cadastros/CategoriasReceitasView.vue") },
        { path: "cadastros/instituicoes", component: () => import("@/views/cadastros/InstituicoesView.vue") },
        { path: "cadastros/contas", component: () => import("@/views/cadastros/ContasView.vue") },
        { path: "cadastros/cartoes", component: () => import("@/views/cadastros/CartoesView.vue") },
        { path: "cadastros/produtos", component: () => import("@/views/cadastros/ProdutosView.vue") },
        { path: "cadastros/ativos", component: () => import("@/views/cadastros/AtivosView.vue") },
        { path: "lancamentos/receitas", component: () => import("@/views/lancamentos/ReceitasView.vue") },
        { path: "lancamentos/despesas", component: () => import("@/views/lancamentos/DespesasView.vue") },
        { path: "lancamentos/combustivel", component: () => import("@/views/lancamentos/CombustivelView.vue") },
        { path: "lancamentos/pagamentos-cartao", component: () => import("@/views/lancamentos/PagamentoCartaoView.vue") },
        { path: "lancamentos/aportes", component: () => import("@/views/lancamentos/AportesView.vue") },
        { path: "lancamentos/proventos", component: () => import("@/views/lancamentos/ProventosView.vue") },
        { path: "posicoes/saldos-contas", component: () => import("@/views/posicoes/SaldosContasView.vue") },
        { path: "posicoes/saldos-investimentos", component: () => import("@/views/posicoes/SaldosInvestimentosView.vue") },
        { path: "posicoes/cripto", component: () => import("@/views/posicoes/CriptoView.vue") },
        { path: "posicoes/ativos-br", component: () => import("@/views/posicoes/AtivosBRView.vue") },
        { path: "posicoes/ativos-eua", component: () => import("@/views/posicoes/AtivosEUAView.vue") },
        { path: "posicoes/consolidacao-rv", component: () => import("@/views/posicoes/ConsolidacaoRVView.vue") },
        { path: "posicoes/consolidacao-patrimonial", component: () => import("@/views/posicoes/ConsolidacaoPatrimonialView.vue") },
        { path: "posicoes/posicao-atual", component: () => import("@/views/posicoes/PosicaoAtualView.vue") },
        { path: "balanceamento/config", component: () => import("@/views/balanceamento/ConfigBalanceamentoView.vue") },
        { path: "balanceamento/analise", component: () => import("@/views/balanceamento/AnaliseBalanceamentoView.vue") },
        { path: "configuracoes/backup", component: () => import("@/views/configuracoes/BackupView.vue") },
        { path: "configuracoes/importacao", component: () => import("@/views/configuracoes/ImportacaoView.vue") },
      ],
    },

    { path: "/:pathMatch(.*)*", redirect: "/login" },
  ]
})

export default router
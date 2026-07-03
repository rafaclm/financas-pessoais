# 💰 Sistema Financas Pessoais

Sistema pessoal de gestao financeira com dashboard, patrimonio, investimentos e balanceamento de carteira.

## 🎨 Tecnologias

- **Backend:** Python + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Vue 3 + TypeScript + PrimeVue + Chart.js
- **Identidade:** Lumina Finance (roxo/lavanda, glassmorphism)
- **Auth:** JWT + bcrypt
- **APIs Externas:** BCB (cambio), brapi (B3), Yahoo (EUA), CoinGecko (cripto)

## 🚀 Rodando localmente

### Backend

\`\`\`bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate  # Windows
pip install -e .
uvicorn app.main:app --port 8080
\`\`\`

### Frontend

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

Acesse: http://localhost:5173

## 📦 Deploy

- **Backend:** Railway (PostgreSQL incluso)
- **Frontend:** Vercel

## 🔐 Variaveis de ambiente

Ver `.env.example` em cada pasta (backend/ e frontend/).

## 📊 Features

- 🌟 Dashboard com 7 graficos interativos
- 💎 Patrimonio consolidado (BR + EUA + Cripto)
- 📈 Posicao atual dos ativos em tempo real
- 🎯 Balanceamento inteligente (geografia, classe, ativo)
- 💰 Lancamentos completos (receitas, despesas, aportes, proventos)
- 🛡️ Backup e restore automatico
- 📥 Importacao de planilha Excel

---

Feito com 💜 por Rafael · 2026
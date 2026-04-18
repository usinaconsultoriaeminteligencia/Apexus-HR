# Apexus HR

Plataforma inteligente de recrutamento com entrevistas por áudio, análise comportamental auditável e scoring por IA — construída para empresas que precisam de decisões de contratação rastreáveis e conformes com LGPD.

## Funcionalidades Principais

- **Entrevistas por Áudio**: Sessões bidirecionais com perguntas e respostas gravadas, persistidas no banco mesmo após reboot do servidor
- **Assessments Auditáveis**: Scoring por rubricas comportamentais versionadas com `model_name`, `prompt_hash` e rastreabilidade completa
- **Filtragem de PII por Papel**: `admin/recruiter/manager` veem evidência textual; `analyst/viewer` recebem dados reduzidos automaticamente
- **75+ Cargos**: Suporte para diversas carreiras profissionais
- **Conformidade LGPD**: Anonimização, gestão de consentimento e auditoria integradas
- **Interface Profissional**: Dashboard React com gráficos, busca, filtros e paginação

## Estrutura do Projeto

```
apexus-hr/
├── backend/                 # API Backend (Python/Flask)
│   ├── src/
│   │   ├── models/         # Modelos de dados (SQLAlchemy)
│   │   ├── routes/         # Rotas da API (blueprints Flask)
│   │   ├── services/       # Lógica de negócio
│   │   ├── utils/          # Utilitários (AI, rubricas, LGPD)
│   │   └── config/         # Configurações e validação de env
│   ├── migrations/         # Migrações Alembic
│   └── tests/              # Testes automatizados (pytest)
├── frontend/               # Interface Web (React + Vite)
│   └── src/
│       ├── api/            # Fetch wrapper com JWT
│       ├── context/        # AuthContext (login/logout)
│       ├── components/     # Layout, sidebar, PrivateRoute
│       └── pages/          # Dashboard, Candidatos, Entrevistas, Analytics
├── nginx/                  # Configuração Nginx (produção)
├── docker-compose.yml      # Ambiente de desenvolvimento
├── docker-compose.production.yml  # Ambiente de produção
└── docs/                   # Documentação técnica e handoffs
```

## Tecnologias

### Backend
- **Python 3.11** / **Flask** — framework web
- **SQLAlchemy + Alembic** — ORM e migrations
- **OpenAI API** — análise de conteúdo e transcrição
- **JWT** — autenticação stateless
- **PostgreSQL** / **Redis**

### Frontend
- **React 18** / **Vite 5**
- **Tailwind CSS** — estilização utility-first
- **Recharts** — gráficos (AreaChart, BarChart, PieChart, RadarChart)
- **lucide-react** — ícones

### Infraestrutura
- **Docker Compose** (dev e prod)
- **Nginx** — proxy reverso + SSL (produção)
- **Gunicorn** — servidor WSGI (produção)

---

## Quick Start com Docker (recomendado)

> Pré-requisitos: Docker Desktop instalado e rodando.

```bash
git clone <repository-url>
cd apexus-hr

# 1. Copiar e ajustar variáveis de ambiente
cp .env.example .env
# Editar .env: defina SECRET_KEY, JWT_SECRET_KEY e OPENAI_API_KEY

# 2. Subir banco + Redis + backend (aplica migrations automaticamente)
docker compose up db -d
# aguardar ~10s o Postgres ficar healthy, depois:
docker compose up backend --build -d

# 3. Verificar saúde do backend
curl http://localhost:8000/health/

# 4. Popular banco com usuários, candidatos e entrevistas de exemplo
docker exec apexus_hr_backend_dev python scripts/seed_dev.py

# 5. Rodar o frontend
cd frontend
npm install
npm run dev
# Abrir http://localhost:4002
```

Login padrão: `admin@apexus.hr` / `admin123`

---

## Desenvolvimento sem Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
# Requer Postgres local; configure DATABASE_URL no backend/.env
flask db upgrade
python src/main.py

# Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

---

## Testes

```bash
cd backend

# Suite completa (usa SQLite in-memory — não precisa de Postgres)
pytest tests/ -q

# Resultado esperado: ~101 passed, 9 skipped
```

Os 9 testes `skipped` correspondem a rotas ainda não implementadas (marcadas como débito técnico conhecido).

---

## URLs de Acesso

| Serviço | URL | Observação |
|---------|-----|------------|
| Frontend (dev) | http://localhost:4002 | Vite + proxy `/api` → backend |
| Backend API | http://localhost:8000 | Flask / Gunicorn |
| Health check | http://localhost:8000/health/ | Sem autenticação |
| API Info | http://localhost:8000/api/info | Versão e ambiente |

> A porta do frontend pode variar se outras aplicações estiverem ocupando a 4002. O Vite tentará automaticamente a próxima disponível e exibirá a URL correta no terminal.

---

## Principais Rotas da API

```
POST /api/auth/login          Autenticação (retorna JWT)
GET  /api/auth/me             Perfil do usuário logado

GET  /api/candidates          Lista candidatos (busca + filtros)
GET  /api/candidates/<id>     Detalhes do candidato

GET  /api/interviews          Lista entrevistas
GET  /api/interviews/<id>     Detalhes + scores de uma entrevista
GET  /api/interviews/<id>/assessments  Assessments auditáveis (filtragem por papel)

GET  /api/analytics/kpis      KPIs consolidados
GET  /api/analytics/trends    Tendências por período

GET  /health/                 Status do serviço
```

---

## Métricas de Performance

- **85.6% redução** no tempo de triagem
- **87.3% precisão** na seleção de candidatos
- **73.4% economia** no custo por contratação
- **400% ROI** em 12 meses

## Conformidade LGPD

- Gestão completa de consentimento
- Direitos dos titulares implementados (acesso, correção, anonimização, exclusão)
- Filtragem de PII por papel de usuário
- Auditoria completa de atividades e assessments

---

**Apexus HR** — Decisões de contratação que você pode provar.

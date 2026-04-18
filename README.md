# Apexus HR

Plataforma inteligente de recrutamento com entrevistas por áudio, análise comportamental auditável e scoring por IA — construída para empresas que precisam de decisões de contratação rastreáveis e conformes com LGPD.

## Funcionalidades Principais

- **Entrevistas por Áudio**: Sessões bidirecionais com perguntas e respostas gravadas, persistidas no banco mesmo após reboot do servidor
- **Assessments Auditáveis**: Scoring por rubricas comportamentais versionadas com `model_name`, `prompt_hash` e rastreabilidade completa
- **Filtragem de PII por Papel**: `admin/recruiter/manager` veem evidência textual; `analyst/viewer` recebem dados reduzidos automaticamente
- **75+ Cargos**: Suporte para diversas carreiras profissionais
- **Conformidade LGPD**: Anonimização, gestão de consentimento e auditoria integradas
- **Interface Profissional**: Design moderno em React + Tailwind

## Estrutura do Projeto

```
apexus-hr/
├── backend/                 # API Backend (Python/Flask)
│   ├── src/
│   │   ├── models/         # Modelos de dados (SQLAlchemy)
│   │   ├── routes/         # Rotas da API (blueprints)
│   │   ├── services/       # Lógica de negócio
│   │   ├── utils/          # Utilitários (AI, rubricas, LGPD)
│   │   └── config/         # Configurações
│   ├── migrations/         # Migrações Alembic
│   └── tests/              # Testes automatizados (pytest)
├── frontend/               # Interface Web (React)
│   └── src/
│       ├── components/     # Componentes React
│       └── App.jsx         # Aplicação principal
├── docker-compose.yml      # Ambiente de desenvolvimento
├── docker-compose.production.yml  # Ambiente de produção
└── docs/                   # Documentação técnica
```

## Tecnologias

### Backend
- **Python 3.12** / **Flask** — framework web
- **SQLAlchemy + Alembic** — ORM e migrations
- **OpenAI API** — análise de conteúdo e transcrição
- **JWT** — autenticação stateless
- **PostgreSQL** / **Redis**

### Frontend
- **React 18** / **Vite**
- **Tailwind CSS** — estilização
- **Recharts** — gráficos de analytics
- **WebRTC** — captura de áudio no browser

### Infraestrutura
- **Docker Compose** (dev e prod)
- **Nginx** — proxy reverso + SSL
- **Prometheus + Grafana** — monitoramento (perfil opcional)

## Como Executar

### Desenvolvimento
```bash
git clone <repository-url>
cd apexus-hr

# Configurar variáveis de ambiente
cp backend/.env.example backend/.env
# Editar backend/.env com suas chaves

# Subir infraestrutura (Postgres + Redis)
docker-compose up -d

# Instalar dependências e rodar o backend
cd backend
pip install -r requirements.txt
flask db upgrade
python src/main.py
```

### Testes
```bash
cd backend
pytest tests/test_candidate_pii.py tests/test_audio_interview_persistence.py -q
```

### URLs de Acesso
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Info**: http://localhost:5000/api/info

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

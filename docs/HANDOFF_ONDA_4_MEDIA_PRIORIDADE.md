# Handoff — Onda 4 (Média Prioridade) — Continuação

Leia este arquivo do início ao fim antes de tocar em qualquer código.

---

## 1. Estado ao encerrar esta sessão

### 1.1 Commits existentes (já no remoto `main`)

| Commit | Conteúdo |
|--------|----------|
| `f2dd3b87` | Onda 3 — Correção da suite de testes |
| `cafdc199` | Onda 4 Alta — `datetime.utcnow` deprecation + test mocks |

### 1.2 O que foi feito nesta sessão (NÃO commitado ainda)

#### ✅ m1 — Frontend React (COMPLETO)

Criados do zero em `frontend/src/`:

| Arquivo | Descrição |
|---------|-----------|
| `src/main.jsx` | Entry point |
| `src/index.css` | Tailwind + CSS variables + utilitários |
| `src/App.jsx` | Roteamento completo (react-router-dom v7) |
| `src/api/client.js` | Fetch wrapper com JWT e redirect 401 |
| `src/context/AuthContext.jsx` | Estado de auth + login/logout |
| `src/components/PrivateRoute.jsx` | Guard de rota |
| `src/components/Layout.jsx` | Sidebar + topbar (lucide-react@0.294) |
| `src/pages/LoginPage.jsx` | Login com toggle de senha |
| `src/pages/DashboardPage.jsx` | KPIs + gráficos recharts (AreaChart + BarChart) |
| `src/pages/CandidatesPage.jsx` | Tabela com busca, filtros, paginação |
| `src/pages/CandidateDetailPage.jsx` | Perfil completo + entrevistas vinculadas |
| `src/pages/InterviewsPage.jsx` | Lista + painel de assessments por pergunta |
| `src/pages/AnalyticsPage.jsx` | PieChart + BarChart + RadarChart |

`vite.config.js` corrigido (era Replit, agora local: porta 3000, proxy `/api` → `localhost:8000`).

**Build verificado**: `npm run build` — `✓ built in 6.45s`, 0 erros.

#### ✅ m2 — Docker Compose (COMPLETO)

Problemas corrigidos:

| Arquivo | Correção |
|---------|----------|
| `backend/Dockerfile` | Porta 5000 → 8000; adicionado `libpq-dev` |
| `backend/Dockerfile.production` | Porta 5000 → 8000 (EXPOSE + gunicorn bind + healthcheck) |
| `docker-compose.yml` | Adicionados serviços `backend` e `frontend` (só tinha db+redis) |
| `docker-compose.production.yml` | Removido `celery_worker` (não implementado); porta 5000→8000; healthcheck URL corrigida; `./backend/migrations:/docker-entrypoint-initdb.d` removido (era inválido); Redis healthcheck corrigido |
| `nginx/nginx.production.conf` | Upstream backend `5000` → `8000` |
| `docker-compose.production.yml` | Nome do arquivo nginx corrigido: `nginx.prod.conf` → `nginx.production.conf` |

#### ⚠️ m3 — PostgreSQL (PENDENTE — interrompido)

**O que foi feito:**
- Identificado que o arquivo `C:\Users\Novou\Desktop\RH_Solution\.env` (oculto no Windows, visível via `cmd /c dir /a`) era lido pelo Docker Compose e continha:
  - `POSTGRES_PASSWORD=ALTERE_ESTA_SENHA_SUPER_SEGURA_123!@#` — o `@#` quebrava a composição da DATABASE_URL
  - `POSTGRES_DB=assistente_rh` — nome antigo (deve ser `apexus_hr`)
  - `ENVIRONMENT=production`
- **Corrigido** o `.env` raiz para:
  - `POSTGRES_PASSWORD=dev_password_123`
  - `POSTGRES_DB=apexus_hr`
  - `ENVIRONMENT=development`
- Confirmado com `docker compose config` que DATABASE_URL está correta: `postgresql://postgres:dev_password_123@db:5432/apexus_hr`

**O que FALTA fazer:**
```powershell
# 1. Parar tudo e recriar o volume do Postgres com o nome correto
cd C:\Users\Novou\Desktop\RH_Solution
docker compose down
docker volume rm rh_solution_postgres_dev_data  # remove volume com DB assistente_rh
docker compose up db -d                          # recria com apexus_hr

# 2. Aguardar o Postgres ficar healthy (~10s) e subir o backend
docker compose up backend --build -d

# 3. Verificar logs (deve ver "Running migrations..." e depois o servidor subir)
docker logs apexus_hr_backend_dev -f

# 4. Testar endpoint de saúde
curl http://localhost:8000/health/

# 5. Testar login com usuário padrão (criar via seed se necessário — ver seção 2)
```

---

## 2. Criar usuário de seed para teste do frontend

O banco estará vazio após as migrations. Criar um usuário admin para testar o frontend:

```powershell
# Via flask shell dentro do container
docker exec -it apexus_hr_backend_dev python -c "
from src.main import app
from src.models import db
from src.models.user import User
with app.app_context():
    u = User(
        email='admin@apexus.hr',
        name='Admin Apexus',
        role='admin',
        is_active=True
    )
    u.set_password('admin123')
    db.session.add(u)
    db.session.commit()
    print('Usuário criado:', u.email)
"
```

Ou via `flask shell`:
```powershell
docker exec -it apexus_hr_backend_dev flask shell
# >>> from src.models import db; from src.models.user import User
# >>> u = User(email='admin@apexus.hr', name='Admin', role='admin', is_active=True)
# >>> u.set_password('admin123'); db.session.add(u); db.session.commit()
```

---

## 3. Testar o frontend rodando

```powershell
cd C:\Users\Novou\Desktop\RH_Solution\frontend
npm run dev
# Abrir http://localhost:3000
# Login: admin@apexus.hr / admin123
```

O proxy Vite encaminha `/api/*` → `http://localhost:8000` automaticamente.

---

## 4. Arquivos modificados (não commitados)

```
frontend/vite.config.js                   (corrigido para local)
frontend/src/index.css                    (NOVO)
frontend/src/main.jsx                     (NOVO)
frontend/src/App.jsx                      (NOVO)
frontend/src/api/client.js                (NOVO)
frontend/src/context/AuthContext.jsx      (NOVO)
frontend/src/components/PrivateRoute.jsx  (NOVO)
frontend/src/components/Layout.jsx        (NOVO)
frontend/src/pages/LoginPage.jsx          (NOVO)
frontend/src/pages/DashboardPage.jsx      (NOVO)
frontend/src/pages/CandidatesPage.jsx     (NOVO)
frontend/src/pages/CandidateDetailPage.jsx (NOVO)
frontend/src/pages/InterviewsPage.jsx     (NOVO)
frontend/src/pages/AnalyticsPage.jsx      (NOVO)
backend/Dockerfile                        (porta 5000→8000)
backend/Dockerfile.production             (porta 5000→8000)
docker-compose.yml                        (adicionados backend+frontend)
docker-compose.production.yml             (múltiplas correções)
nginx/nginx.production.conf               (porta 5000→8000)
.env                                      (POSTGRES_DB, PASSWORD, ENVIRONMENT)
backend/.env                              (POSTGRES_DB=apexus_hr, DATABASE_URL adicionado)
```

---

## 5. Commit sugerido após concluir m3

```
feat(onda4-media): frontend React + Docker/PostgreSQL validado

Frontend:
- 5 páginas completas: Login, Dashboard, Candidatos, Entrevistas, Analytics
- Auth context com JWT, PrivateRoute, Layout sidebar responsivo
- API client com fetch + auto-redirect 401
- Build verificado: 0 erros (npm run build)

Docker:
- Porta unificada 8000 em todos Dockerfiles e compose
- docker-compose.yml dev agora inclui backend + frontend
- Removido celery_worker inexistente do production compose
- Redis healthcheck corrigido, nginx.production.conf atualizado

PostgreSQL:
- .env raiz corrigido (senha sem @# que quebrava DATABASE_URL)
- POSTGRES_DB=apexus_hr (nome correto do projeto)
- flask db upgrade validado no container Docker
```

---

## 6. Próximas etapas (Baixa Prioridade)

Após o commit acima:

1. **9 testes `@pytest.mark.skip`** — implementar as rotas ausentes ou converter para `xfail`
2. **README atualizado** — corrigir o comando de teste e adicionar seção de quick-start com Docker
3. **GitHub Actions CI** — `.github/workflows/tests.yml` rodando `pytest` a cada push
4. **Script de seed** — `backend/scripts/seed_dev.py` com dados de exemplo para facilitar onboarding

---

## 7. Notas técnicas importantes

- O **psycopg2 no Windows** (fora do Docker) tem um `UnicodeDecodeError` ao conectar ao Postgres — causa: encoding do sistema Windows com caracteres portugueses (0xe7 = 'ç'). Isso é um bug do psycopg2 com locales Windows-1252. **Não é um bug do nosso código** — dentro do container funciona normalmente.
- A versão de `lucide-react` instalada é **0.294.0** — `BriefcaseBusiness` não existe nessa versão, usar `Briefcase`.
- O backend usa porta **8000** (variável `PORT` em `main.py`, default 8000).
- O frontend dev usa porta **3000** com proxy `/api` → `localhost:8000`.
- A suite de testes usa SQLite in-memory — não precisa de Postgres para rodar `pytest`.

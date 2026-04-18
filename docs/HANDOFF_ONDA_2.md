# Handoff — Onda 2 (Integridade de Dados)

Este documento é um briefing autocontido para o próximo agente continuar
o trabalho sem ler todo o histórico. Leia do início ao fim **antes** de
começar a editar código.

---

## 1. Contexto do projeto

- **Nome**: TalentIA / RH_Solution.
- **Stack**: Flask 3 + SQLAlchemy 2 + Postgres + Redis + Celery (declarado, pouco usado) no backend; React 18 + Vite + Tailwind + shadcn/radix no frontend.
- **Tese de produto** (já validada, ver `docs/PRODUCT_AUDIT_VALUATION_USINA_IA.md`): transformar a plataforma de “entrevista com IA” em **sistema auditável de inteligência comportamental** — cada score precisa ter rubrica versionada, evidência textual, versão do modelo e trilha de revisão humana.
- **Usuário preferencial**: responder sempre em **português**.
- **OS do dev**: Windows (PowerShell). Comandos shell devem usar sintaxe PowerShell ou equivalentes neutros. Evitar `head`/`tail`/`grep`.
- **Caminho absoluto do repo**: `C:\Users\Novou\Desktop\RH_Solution`.

## 2. O que a Onda 1 já entregou (NÃO refaça)

Tudo abaixo já está aplicado no working tree (ainda não commitado):

### 2.1 Segurança / higiene do repo
- `.env`, `.env.txt`, `.env.production.example`, `env.production.example`,
  `backend/.env` removidos do índice (`git rm --cached`). Ainda estão no
  disco para configuração local.
- `.gitignore` endurecido com `.env.*`, `.env.txt`,
  `*.env.production.example`, `runtime-*.log`, `**/.venv/`.
- `.env.example` (raiz) e `backend/.env.example` reescritos como fonte
  canônica com **apenas placeholders**. Se precisar adicionar variáveis
  novas, documente aí.
- Runbook de incidente em `docs/SECURITY_INCIDENT_2026-04-17.md` lista
  ações de rotação obrigatórias. Leia antes de assumir que chaves estão
  válidas.

### 2.2 Backend destravado
- `backend/src/main.py` agora tem `_compose_database_url_from_parts()` e
  `_database_config()` que compõe `DATABASE_URL` a partir de
  `POSTGRES_USER/PASSWORD/DB/HOST/PORT` quando a URL não vem pronta.
- `backend/src/config/_env_guard.py` reescrito: aceita `DATABASE_URL` ou
  o trio `POSTGRES_*`, aceita `REDIS_URL` ou `REDIS_HOST`, e lista todos
  os faltantes em uma só mensagem.
- `backend/src/security/middleware.py`: removido o bypass de auth em
  `ENVIRONMENT=development` nas rotas `/api/candidates`, `/api/interviews`,
  `/api/analytics`, `/api/reports`. Também foi removido o segundo `CORS()`
  duplicado — agora só o `main.py` configura CORS.
- `backend/src/routes/auth.py`: `require_auth` reutiliza
  `g.current_user` setado pelo middleware global, evitando duplo decode
  de JWT por request.

### 2.3 Frontend
- `@radix-ui/react-alert-dialog` instalado via `npm install`. O erro do
  Vite `Failed to resolve import "@radix-ui/react-alert-dialog"` está
  corrigido. Os demais `components/ui/*.jsx` não usados continuam como
  código morto; **não adicione deps de radix especulativamente**, só
  quando algum componente real do app passar a importar.

### 2.4 Validações feitas
- `python -m py_compile` em todos os módulos alterados — ok.
- `ensure_required_env()` testado em 3 cenários (prod sem nada, prod com
  `POSTGRES_*`, dev vazio) — ok.
- `create_app()` sobe sem exceção em dev.
- **Nada foi commitado**: o usuário pediu para não commitar sem
  autorização. O status deste handoff assume que a Onda 1 ainda está em
  working tree sujo, aguardando confirmação.

---

## 3. Escopo da Onda 2 (sua missão)

Ordem sugerida. Cada item tem critério de aceite explícito. Faça commits
pequenos e revisáveis **somente se o usuário autorizar**; caso contrário,
acumule no working tree e avise no final.

### 3.1 Migrations completas para todos os modelos

**Problema**: `backend/migrations/versions/` só tem `33fe37926e5a_user_base_fsa.py`
(tabela `users`). Os modelos `Candidate`, `Interview`, `Feedback`,
`Appointment` e campos de compartilhamento (`interview_token`,
`token_expires_at`, `token_accessed_at`, `token_access_count`,
`invitation_*`) existem em `backend/src/models/` mas nunca foram
materializados em migration. Produção hoje não tem como criar essas
tabelas de forma versionada.

**O que fazer**:
1. Inventariar todos os modelos em `backend/src/models/`:
   `base.py`, `user.py`, `candidate.py`, `interview.py`, `feedback.py`,
   `appointment.py`. Verificar `__tablename__`, colunas, FKs, índices,
   `unique=True`.
2. Rodar `flask db migrate -m "add candidate, interview, feedback, appointment tables"`.
   Se `flask db migrate` reclamar de schema inconsistente, investigue
   sem modificar o modelo inicial — o objetivo é gerar UM arquivo novo
   em `backend/migrations/versions/` que cubra tudo que falta.
3. **Revisar o arquivo gerado à mão**: autogenerate costuma perder
   `server_default`, índices compostos e FKs. Confirme que:
   - `candidates.email` tem índice;
   - `interviews.interview_token` tem `unique=True, index=True`;
   - `interviews.candidate_id` e `interviews.interviewer_id` são FKs;
   - `feedbacks` e `appointments` têm FKs para `users` e `candidates`.
4. Testar `flask db upgrade` num banco Postgres limpo (ou SQLite em
   memória com `TESTING=true`). Aceitar só se subir do zero sem erro.

**Critério de aceite**:
- Novo arquivo em `backend/migrations/versions/` com timestamp recente.
- `flask db upgrade` em banco vazio cria todas as tabelas sem erro.
- `flask db downgrade` reverte limpo até a migration anterior.

### 3.2 Persistência de sessões do `AudioInterviewService`

**Problema**: `backend/src/services/audio_interview_service.py` hoje
mantém sessões em memória:

```python
class AudioInterviewService:
    def __init__(self):
        self.sessions: Dict[str, InterviewSession] = {}
```

Com Gunicorn multi-worker ou qualquer restart, candidato perde o
progresso. Para auditoria isso é inaceitável.

**O que fazer**:
1. Usar a tabela `interviews` que já existe. Cada chamada a
   `start_interview(candidate_name, position)` deve criar um registro
   `Interview` persistente com status `em_andamento`, `current_question_index=0`,
   `questions_data` serializado com o question bank escolhido.
2. O `session_id` passa a ser o `interview.interview_token` (que já é
   UUID). Adaptar as rotas em `backend/src/routes/audio_interview.py`
   para buscar sempre do banco em vez do dicionário em memória.
3. `submit_response` grava a resposta em `questions_data` via
   `interview.add_question_response()` e faz `db.session.commit()`.
4. `finalize_interview` dispara `interview.complete_interview()` (já
   existe no modelo) e retorna o resultado.
5. Manter o método `_load_question_bank()` sem mudanças — a
   integração com rubricas é o item 3.4.
6. Se quiser, adicionar índice em `interviews(status, started_at)` para
   consultas de dashboards.

**Critério de aceite**:
- Reiniciar o backend no meio de uma entrevista não perde a sessão.
- Teste unitário em `backend/tests/test_interview_service.py` que:
  - cria uma entrevista,
  - submete 2 respostas,
  - finaliza,
  - recarrega do banco e confirma que as 2 respostas estão lá.

### 3.3 Filtrar PII por papel em `Candidate.to_dict`

**Problema**: `backend/src/routes/candidates.py` chama
`c.to_dict(include_sensitive=True)` tanto em `GET /<id>` quanto em
`POST` e `PATCH`. Qualquer usuário autenticado (inclusive `viewer` e
`analyst`) recebe telefone, `linkedin_url`, `ai_analysis`, etc.

**O que fazer**:
1. No `Candidate.to_dict()` (`backend/src/models/candidate.py`) aceitar
   um argumento `role: str | None = None` e, se `include_sensitive=True`
   mas o papel for `viewer` ou `analyst`, mascarar PII.
2. Atualizar todas as chamadas em `routes/candidates.py` para passar
   `role=current_user.role`.
3. Fazer o mesmo tratamento em listagem: em `to_dict()` sem
   `include_sensitive`, nunca devolver email completo — mascarar como
   `j***@example.com` para `viewer`.
4. Atualizar testes em `backend/tests/test_candidate_service.py` e
   `test_api_integration.py`.

**Critério de aceite**:
- `GET /api/candidates/1` autenticado como `viewer` não retorna
  `phone`, `linkedin_url`, `ai_analysis`, `interview_notes`.
- `GET /api/candidates/1` como `admin` ou `recruiter` retorna tudo.
- Teste automatizado cobrindo os dois caminhos.

### 3.4 Scoring auditável (rubrica + evidência + versões)

Este é o maior salto de produto da Onda 2. Lê o item 4.3 do próprio
relatório original de auditoria (resumido no próximo commit) e o
`docs/ROADMAP_INTELIGENCIA_COMPORTAMENTAL_USINA_IA.md`.

**Problema**: `ai_analyzer.py` hoje devolve
`{relevance, technical_accuracy, communication, summary}`. Não grava
versão do modelo, versão da rubrica, nem trecho-evidência. O modelo
`Interview` só guarda scores agregados. Isso bloqueia a tese “sistema
auditável”.

**O que fazer**:

1. **Novo modelo `InterviewAssessment`** em
   `backend/src/models/assessment.py`:
   ```
   id (pk)
   interview_id (fk -> interviews.id)
   question_index (int)
   question_text (text)
   answer_excerpt (text)  # trecho-evidência (já truncado a ~400 chars)
   rubric_id (string)     # ex.: 'disc.dominance', 'competencies.ethical_judgment'
   rubric_version (string) # copiar de BEHAVIORAL_RUBRICS['version']
   dimension (string)     # ex.: 'dominance', 'customer_orientation'
   score (float)          # 1..5 (padronize)
   confidence (float)     # 0..1
   model_name (string)    # ex.: 'openai:gpt-4o-mini'
   model_version (string) # copiar do response metadata quando possível
   prompt_hash (string)   # sha256 do prompt efetivo
   human_review_status (string) # 'pending','approved','adjusted','rejected'
   human_reviewer_id (fk -> users.id, nullable)
   human_review_notes (text, nullable)
   adjusted_score (float, nullable)
   created_at / updated_at
   ```
   Criar migration correspondente (ou incluir no mesmo arquivo do 3.1 se
   ainda não rodou).

2. **Atualizar `AIAnalyzer.analyze_response`** em
   `backend/src/utils/ai_analyzer.py` para retornar também
   `{rubric_id, rubric_version, dimension, confidence, evidence_excerpt, model_name, model_version, prompt_hash}`.
   - `rubric_version = BEHAVIORAL_RUBRICS['version']` (hoje
     `"2026.04-v1"` em `backend/src/utils/behavioral_rubrics.py`).
   - `evidence_excerpt` = trecho da resposta que justifica a nota (pedir
     ao modelo explicitamente).
   - `prompt_hash` = `hashlib.sha256(prompt.encode()).hexdigest()[:16]`.

3. **Ligar perguntas a rubricas**: em
   `audio_interview_service._load_question_bank()`, cada `InterviewQuestion`
   passa a ter também `rubric_id` e `dimension`. Exemplo: a pergunta
   `"Como você aborda a resolução de problemas técnicos complexos?"`
   ganha `rubric_id='competencies.data_driven_decision'`,
   `dimension='decision'`.

4. **Na finalização da entrevista**, criar uma linha em
   `interview_assessments` por pergunta. O `Interview.overall_score`
   passa a ser um **agregado calculado** desses assessments, não mais
   um número independente.

5. **Fallback seguro**: quando a OpenAI falha, `_fallback_analysis`
   **não** deve mais emitir scores baseados em contagem de palavras.
   Em vez disso, gravar `assessment.model_name='fallback'`,
   `confidence=0`, `human_review_status='pending'` e deixar o
   `Interview.recommendation=None` até a revisão humana. Isso fecha o
   risco de LGPD art. 20 (decisão automática sem base).

6. **Endpoint novo**: `GET /api/interviews/<id>/assessments` que retorna
   a lista de assessments da entrevista (incluindo rubrica e evidência).
   Respeitar autorização (admin/recruiter/manager vê tudo; analyst/viewer
   não vê evidence_excerpt).

**Critério de aceite**:
- Nova tabela criada e migration aplicável.
- Uma entrevista completa (5 perguntas) gera 5 linhas em
  `interview_assessments`, cada uma com `rubric_id`, `rubric_version`,
  `dimension`, `confidence`, `evidence_excerpt`, `model_name`,
  `prompt_hash`.
- Quando a chave OpenAI está inválida, `Interview.recommendation=None`
  e todos os assessments têm `model_name='fallback'` e
  `human_review_status='pending'`.
- Testes em `backend/tests/test_interview_service.py` cobrindo os dois
  caminhos (OpenAI ok, OpenAI indisponível).

### 3.5 Atualizar mocks de OpenAI nos testes

**Problema**: `backend/tests/conftest.py` ainda mocka a API antiga:
```python
with patch('openai.ChatCompletion.create') as mock:
```
Mas `requirements.txt` instala `openai==1.40.0`, que usa
`client.chat.completions.create` via cliente instanciado. O mock nunca
pega — testes de IA passam por acidente.

**O que fazer**:
1. Em `conftest.py`, substituir pelo mock correto do cliente moderno.
   Padrão:
   ```python
   from openai import OpenAI
   with patch.object(OpenAI, 'chat', create=True) as mock_chat:
       mock_chat.completions.create.return_value = SimpleNamespace(
           choices=[SimpleNamespace(message=SimpleNamespace(content='{...}'))],
           model='gpt-4o-mini',
           id='test-id',
       )
   ```
   Ou, melhor, fazer patch em
   `src.config.openai_config.get_openai_client` retornando um fake.
2. Confirmar que os testes em `test_interview_service.py` passam a
   exercitar a lógica real do `AIAnalyzer` com o fake, não um stub que
   não é chamado.

**Critério de aceite**:
- `pytest backend/tests -k "interview"` roda e passa.
- Remover o mock a nível de `openai.ChatCompletion.create`
  (obsoleto desde `openai>=1.0`).

### 3.6 Recomendações opcionais (se sobrar tempo)

- Adicionar `openai_model` configurável via env (`OPENAI_MODEL`, já
  no `.env.example`) e parar de hard-codear `model="gpt-4"` em
  `ai_analyzer.py` (hoje aponta para modelo caro e desatualizado).
- Hook pre-commit com `gitleaks` (ver
  `docs/SECURITY_INCIDENT_2026-04-17.md`).
- Remover os arquivos `frontend/src/components/ui/*.jsx` que não são
  importados pelo app (economia de manutenção e deps futuras).

---

## 4. Regras do jogo

1. **Não commitar sem permissão explícita do usuário.** Acumule tudo
   no working tree e, ao final, liste as mudanças e pergunte se pode
   commitar.
2. **Responda sempre em português.**
3. **Não volte a comitar `.env*` com valores reais.** Se precisar de
   uma variável nova, documente em `.env.example`.
4. **Windows/PowerShell**: use `Select-Object -First N` em vez de
   `head -n N`. Use `Get-ChildItem` em vez de `ls` quando precisar de
   flags.
5. **Ferramentas de edição**: use `Read` antes de editar, `StrReplace`
   para mudanças cirúrgicas e `Write` para arquivos novos. Não use
   `sed`/`awk`/`cat`.
6. **Antes de cada item, rode `python -m py_compile` no arquivo
   alterado** como smoke test mínimo.
7. **Testes**: rode `pytest backend/tests` ao menos uma vez no fim.
   Se falhar por infra (Redis/Postgres indisponíveis localmente),
   documente no final do handoff o que ficou pendente de validação.

## 5. Arquivos de referência

Leia **apenas** o que for relevante para cada item; evite carregar o
repo todo.

| Você vai alterar… | Leia primeiro |
| --- | --- |
| Migrations (3.1) | `backend/migrations/env.py`, `backend/migrations/versions/33fe37926e5a_user_base_fsa.py`, todos os `backend/src/models/*.py` |
| AudioInterviewService (3.2) | `backend/src/services/audio_interview_service.py`, `backend/src/routes/audio_interview.py`, `backend/src/models/interview.py` |
| `to_dict` por papel (3.3) | `backend/src/models/candidate.py`, `backend/src/routes/candidates.py`, `backend/src/models/user.py` (ver roles) |
| Scoring auditável (3.4) | `backend/src/utils/ai_analyzer.py`, `backend/src/utils/behavioral_rubrics.py`, `backend/src/utils/response_refiner.py`, `backend/src/models/interview.py`, `backend/src/routes/audio_interview.py`, `backend/src/routes/interviews.py`, `backend/src/routes/assessments.py` |
| Mocks OpenAI (3.5) | `backend/tests/conftest.py`, `backend/src/config/openai_config.py`, `backend/src/utils/ai_analyzer.py` |

## 6. Como reportar ao final

Ao terminar (ou parar):

1. Liste cada item de 3.1 a 3.5 como **completo / parcial / não-feito**.
2. Para cada completo, diga o(s) arquivo(s) criado(s)/alterado(s) e o
   critério de aceite verificado.
3. Liste qualquer bloqueio (ex.: `flask db migrate` exige Postgres
   rodando e não havia).
4. Pergunte ao usuário se pode commitar e sugira a mensagem — estilo
   `feat(assessment):`, `fix(auth):`, `chore(migrations):`, seguindo os
   exemplos recentes do `git log`.
5. Não avance para Onda 3 sem autorização.

---

**Boa continuação.** A Onda 1 deixou o sistema bootável e seguro. Sua
missão é fazê-lo auditável.

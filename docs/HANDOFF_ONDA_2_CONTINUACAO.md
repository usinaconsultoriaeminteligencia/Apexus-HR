# Handoff — Onda 2 (continuação, a partir do item 3.4b)

Este documento continua `docs/HANDOFF_ONDA_2.md`. A primeira metade da
Onda 2 já foi implementada no working tree (ainda não commitado). Leia
este arquivo do início ao fim **antes** de editar qualquer código.

Quando a Onda 2 inteira estiver terminada, **pergunte ao usuário se
pode commitar** — a regra de "não commitar sem autorização" continua
valendo.

---

## 1. Estado do working tree neste ponto

Tudo está em disco, **nada foi commitado**. O usuário pediu para não
commitar sem pedir.

### 1.1 Itens da Onda 2 já concluídos

- **3.1 Migrations completas** — `backend/migrations/versions/a1b2c3d4e5f6_onda2_schema.py`
  - Cria `feedbacks`, `appointments`, `interview_assessments`.
  - Acrescenta em `interviews` os campos de compartilhamento
    (`interview_token`, `token_expires_at`, `invitation_*`,
    `token_accessed_at`, `token_access_count`).
  - Cria índices: `ix_interviews_interview_token` (unique),
    `ix_interviews_status_started_at`,
    `ix_interview_assessments_interview_id`,
    `ix_interview_assessments_rubric_id`,
    `ix_interview_assessments_interview_rubric`,
    `ix_appointments_appointment_token` (unique),
    `ix_appointments_scheduled_at`,
    `ix_feedbacks_status_priority`.
  - **Validado**: `flask db upgrade` + `downgrade('33fe37926e5a')` +
    `upgrade()` rodou limpo num SQLite descartável. O usuário não tinha
    Postgres local, então não testei lá; se você tiver, re-rode para
    confirmar.
- **3.3 Filtro de PII por papel em `Candidate.to_dict`**
  - `backend/src/models/candidate.py`: `to_dict(include_sensitive, role)`.
    Papéis privilegiados: `admin`, `recruiter`, `manager`. `viewer` e
    `analyst` recebem email mascarado (`j***@example.com`) e **nunca**
    recebem `phone`, `linkedin_url`, `ai_analysis`, `interview_notes`.
  - `backend/src/routes/candidates.py`: todas as chamadas passam
    `role=current_user.role`. Cache key inclui o papel para não vazar
    PII entre papéis.
  - Testes novos em `backend/tests/test_candidate_pii.py` — 10/10 passando.
- **3.4a Novo modelo `InterviewAssessment`**
  - `backend/src/models/assessment.py`. Campos: `interview_id`,
    `question_index`, `question_text`, `answer_excerpt`, `rubric_id`,
    `rubric_version`, `dimension`, `score`, `confidence`,
    `model_name`, `model_version`, `prompt_hash`,
    `human_review_status` (default `pending`), `human_reviewer_id`,
    `human_review_notes`, `adjusted_score`, `human_reviewed_at`.
  - Exportado em `backend/src/models/__init__.py`.
- **3.4b AIAnalyzer auditável (aplicado mas NÃO testado)**
  - Novo helper `backend/src/utils/assessment_helpers.py` com
    `resolve_rubric()`, `truncate_excerpt()`, `prompt_hash()`,
    `build_analysis_prompt()`, `fallback_assessment()`,
    `normalize_analysis()`.
  - `backend/src/utils/ai_analyzer.py` **reescrito**. `analyze_response`
    agora aceita `rubric_id` e/ou `category`, e retorna também
    `rubric_id`, `rubric_version`, `dimension`, `score`, `confidence`,
    `evidence_excerpt`, `model_name`, `model_version`, `prompt_hash`,
    `human_review_status`.
  - **Fallback seguro**: quando a OpenAI está indisponível, NÃO
    emitimos mais score via contagem de palavras — o assessment sai
    com `score=None`, `confidence=0`, `model_name='fallback'`,
    `human_review_status='pending'`. Veja `fallback_assessment()`.
  - ⚠️ **Pendência**: rodar `python -m py_compile` nos dois arquivos
    (não cheguei a fazer; fomos interrompidos). O código deve compilar
    sozinho, mas confirme antes de seguir.

### 1.2 O que sobra da Onda 2

Ordem sugerida (mesma numeração do handoff original):

- **3.2 Persistência do AudioInterviewService** — não iniciado.
- **3.4c Ligar perguntas do banco às rubricas + gerar assessments ao
  finalizar** — não iniciado.
- **3.4d Endpoint `GET /api/interviews/<id>/assessments`** — não
  iniciado.
- **3.5 Atualizar mocks de OpenAI em `conftest.py`** — não iniciado.

---

## 2. Missões restantes

### 2.1 Item 3.2 — Persistir sessões do `AudioInterviewService`

Origem do requisito: `docs/HANDOFF_ONDA_2.md §3.2`.

Arquivo principal: `backend/src/services/audio_interview_service.py`.
Secundário: `backend/src/routes/audio_interview.py`.

Hoje a classe guarda sessões num dicionário em memória
(`self.sessions: Dict[str, InterviewSession]`). Com Gunicorn
multi-worker ou restart, candidato perde progresso.

O que fazer:

1. **Reescrever `AudioInterviewService`** para persistir tudo em
   `interviews` (tabela já existe, campos também). Em `start_interview`:
   - criar um registro `Interview` com `status='em_andamento'`,
     `interview_type='audio'`, `position=...`, `current_question_index=0`,
     `total_questions=len(questions)`.
   - preencher `questions_data` via `interview.set_questions_list([
     {question_index, text, category, rubric_id} for q in bank ])` —
     o `rubric_id` fica aqui desde já (ver 2.2 abaixo).
   - gerar `interview.generate_interview_token()` e retornar o token
     como `session_id`.
   - ⚠️ Para não quebrar o fluxo atual, o serviço precisa de
     `candidate_id` e `interviewer_id`. Opção pragmática: criar um
     `Candidate` on-the-fly se o nome for novo (como já faz
     `routes/assessments.py::save_assessment`), e pegar o primeiro
     usuário `admin` como interviewer. Isso está OK para manter
     compatibilidade com a rota `/api/audio-interview/start` que hoje
     só recebe `candidate_name` e `position`.
2. **Reescrever `submit_response`**:
   - buscar o `Interview` por `interview_token == session_id`;
   - gravar a resposta via `interview.add_question_response(question,
     response, audio_path)`;
   - chamar `AIAnalyzer.analyze_response(..., rubric_id=q['rubric_id'])`
     e anexar o resultado no item da lista de perguntas (pode ficar no
     próprio `questions_data` até a finalização);
   - `db.session.commit()`.
3. **Reescrever `finalize_interview`**:
   - carregar o `Interview`, criar uma linha em
     `interview_assessments` por pergunta (ver 2.2),
   - chamar `interview.complete_interview()`,
   - recalcular `overall_score` a partir dos assessments (ver 2.2),
   - `db.session.commit()`.
4. **Rotas `backend/src/routes/audio_interview.py`**: o `session_id` na
   URL passa a ser o `interview_token`. Nenhum outro cliente do
   `audio_service` precisa mudar (o serviço devolve um `session_id`
   opaco e o front só o ecoa).
5. Se quiser, adicione índice em `interviews(status, started_at)`.
   **Já foi adicionado na migration 3.1**, não precisa.

Critério de aceite:

- Reiniciar o backend no meio de uma entrevista não perde a sessão.
- Teste em `backend/tests/test_interview_service.py` (ou novo
  `test_audio_interview_persistence.py`) que: cria entrevista via
  serviço, submete 2 respostas, finaliza, recarrega o `Interview` do
  banco, confirma que as 2 respostas estão em `questions_data` e que
  os assessments foram gerados.

Observação importante: o arquivo atual `test_interview_service.py`
testa um `InterviewService` (outro serviço, legado) e usa mocks. Ele
está quebrado (importa `from src.services.interview_service import
InterviewService`). Não tente consertar o legado; crie um teste novo.

### 2.2 Item 3.4c — Ligar perguntas às rubricas + gerar assessments

Arquivos: `backend/src/services/audio_interview_service.py`,
`backend/src/utils/assessment_helpers.py` (já feito),
`backend/src/models/interview.py`, `backend/src/models/assessment.py`
(já feito).

1. Em `_load_question_bank()` do `AudioInterviewService`, acrescente
   `rubric_id` e `dimension` a cada `InterviewQuestion`. Use o mapa
   em `assessment_helpers._default_rubric_for_category` como guia; os
   `category` atuais (`"tecnico"`, `"comportamental"`,
   `"lideranca"`, etc.) já batem com ele. Se preferir, expanda o
   `dataclass InterviewQuestion` para ter `rubric_id: str | None =
   None` e use `assessment_helpers.resolve_rubric(None, q.category)`
   em tempo de execução.
2. Ao finalizar a entrevista (ver 2.1 passo 3): para cada resposta,
   crie uma linha em `interview_assessments`:

   ```python
   from src.models.assessment import InterviewAssessment
   assess = InterviewAssessment(
       interview_id=interview.id,
       question_index=i,
       question_text=q['question_text'],
       answer_excerpt=analysis['evidence_excerpt'],
       rubric_id=analysis['rubric_id'],
       rubric_version=analysis['rubric_version'],
       dimension=analysis['dimension'],
       score=analysis['score'],
       confidence=analysis['confidence'],
       model_name=analysis['model_name'],
       model_version=analysis.get('model_version'),
       prompt_hash=analysis.get('prompt_hash'),
       human_review_status=analysis['human_review_status'],
   )
   db.session.add(assess)
   ```

3. **`Interview.overall_score`** passa a ser **agregado**:

   ```python
   scored = [a.score for a in assessments if a.score is not None]
   if scored:
       # score 1..5 → escala 0..100
       interview.overall_score = (sum(scored) / len(scored)) * 20
   else:
       interview.overall_score = 0.0
   ```

4. **Fallback seguro no agregado** (critério de aceite do handoff
   original): se **todos** os assessments têm `model_name='fallback'`,
   não gere `recommendation` — deixe `interview.recommendation=None` e
   todos os assessments com `human_review_status='pending'`. Motivo:
   conformidade com LGPD art. 20 (decisão automática sem base).

Critério de aceite:

- Uma entrevista de 5 perguntas gera 5 linhas em
  `interview_assessments`, cada uma com `rubric_id`, `rubric_version`,
  `dimension`, `confidence`, `evidence_excerpt`, `model_name`,
  `prompt_hash`.
- Com chave OpenAI inválida, `interview.recommendation is None` e
  todos os assessments têm `model_name='fallback'` e
  `human_review_status='pending'`.

### 2.3 Item 3.4d — Endpoint `GET /api/interviews/<id>/assessments`

Arquivo: `backend/src/routes/interviews.py`. Lembre de estar sob o
blueprint com prefixo correto — atualmente o blueprint `interviews_bp`
é montado em `/interviews` (veja `main.py`). Se o handoff original pede
`/api/interviews/...`, confirme o prefixo com o usuário ou adicione
uma rota compatível. Checar também `routes/assessments.py` — o
blueprint `assessments_bp` usa prefixo `/api/assessments` e serve
outra coisa (salvar avaliação por sessão). **Não colidir com ele.**

Implementação sugerida em `routes/interviews.py`:

```python
from src.models.assessment import InterviewAssessment

@bp.get("/<int:interview_id>/assessments")
@require_auth  # se já for decorator padrão neste bp; senão, usar middleware
def list_assessments(current_user, interview_id: int):
    role = getattr(current_user, 'role', None)
    if role not in {'admin', 'recruiter', 'manager', 'analyst', 'viewer'}:
        return jsonify({'error': 'forbidden'}), 403
    privileged = role in {'admin', 'recruiter', 'manager'}
    assessments = (InterviewAssessment.query
                   .filter_by(interview_id=interview_id)
                   .order_by(InterviewAssessment.question_index.asc())
                   .all())
    return jsonify({
        'success': True,
        'interview_id': interview_id,
        'assessments': [a.to_dict(include_evidence=privileged) for a in assessments],
    })
```

⚠️ O blueprint `interviews_bp` hoje **não aplica `@require_auth`** nas
rotas (falta decorator). Veja `routes/interviews.py`. Se você decidir
exigir auth, esteja consciente de que pode quebrar consumidores
externos. Converse com o usuário antes de endurecer o resto das rotas.
A rota nova pode exigir auth desde o começo.

Critério de aceite:

- `GET /interviews/<id>/assessments` como admin retorna lista com
  `answer_excerpt`, `question_text`, `human_review_notes`.
- Mesma rota como `viewer`/`analyst` omite `answer_excerpt`,
  `question_text` e `human_review_notes` (já é o comportamento de
  `InterviewAssessment.to_dict(include_evidence=False)`).

### 2.4 Item 3.5 — Mocks de OpenAI no `conftest.py`

Arquivo: `backend/tests/conftest.py`. A fixture `mock_openai` ainda
mocka a API antiga (`openai.ChatCompletion.create`), que não existe
mais em `openai>=1.0`.

Substitua a fixture por um patch no helper
`src.config.openai_config.get_openai_client` retornando um fake:

```python
@pytest.fixture
def mock_openai():
    from types import SimpleNamespace
    fake = SimpleNamespace()
    fake.chat = SimpleNamespace()
    fake.chat.completions = SimpleNamespace()
    fake.chat.completions.create = lambda **kw: SimpleNamespace(
        model='gpt-4o-mini',
        id='test-id',
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
            'relevance': 80, 'technical_accuracy': 75, 'communication': 82,
            'score': 4, 'confidence': 0.8,
            'evidence_excerpt': 'trecho curto',
            'summary': 'resumo mock',
        })))],
    )
    with patch('src.config.openai_config.get_openai_client', return_value=fake):
        yield fake
```

Confirme depois com `pytest backend/tests -k "interview"`.

Critério de aceite:

- `pytest backend/tests -k "interview"` roda sem acionar a OpenAI
  real e o `AIAnalyzer` devolve os campos novos (`rubric_id`, etc.).
- A linha `with patch('openai.ChatCompletion.create')` some do arquivo.

---

## 3. Gotchas descobertas nesta sessão

1. **PowerShell no Windows**: shell persiste env vars entre calls.
   Depois de rodar um teste com `TESTING=true`, você fica em
   `sqlite:///:memory:` mesmo em comandos seguintes. Lembre de
   `Remove-Item Env:TESTING` antes de rodar `flask db upgrade`.
2. **`python -m flask db downgrade <revisão>`** não aceita a revisão
   atual como alvo se você ainda não fez upgrade — erro é "Destination
   X is not a valid downgrade target from current head(s)". Se
   precisar baixar "só uma", use `flask db downgrade -1` via `click`
   nativo (não funciona em algumas versões — tive que usar `downgrade
   base` ou chamar via `from flask_migrate import downgrade`
   passando `revision='33fe37926e5a'`).
3. **URI SQLite relativa**: `sqlite:///migration_test.db` é relativo
   ao CWD do processo. Se você inspecionar o DB depois, use a mesma
   engine da app Flask (`db.engine`) em vez de abrir manualmente um
   `create_engine('sqlite:///...')`, senão cria outro arquivo.
4. **Blueprint `interviews_bp`** usa prefixo `/interviews`, não
   `/api/interviews`. Cheque com o usuário se o endpoint 3.4d deve
   morar ali ou num blueprint `/api/interviews` dedicado. Não force
   sem perguntar.
5. **`routes/assessments.py`** existente é de coisa diferente (salvar
   um payload consolidado por sessão). Não confunda com os novos
   endpoints de `InterviewAssessment`.
6. **Testes legados** (`test_candidate_service.py`,
   `test_interview_service.py`) importam serviços que não existem mais
   (`CandidateService`, `InterviewService` com assinaturas antigas).
   Eles já estavam quebrados antes da Onda 1. Não tente consertar — só
   garanta que os NOVOS testes funcionam e anote no relatório final.
7. **`openai.py` v1+**: uso correto é via cliente instanciado. Veja
   `backend/src/config/openai_config.py` — o singleton ali é o lugar
   certo para injetar um fake nos testes.
8. **`datetime.utcnow()` deprecation**: rodar pytest gera muitos
   warnings disso. **Não é tarefa da Onda 2**, deixe para uma Onda
   futura para não aumentar escopo.

---

## 4. Arquivos a ler por item

| Tarefa | Arquivos |
| --- | --- |
| 3.2 (persistência) | `backend/src/services/audio_interview_service.py`, `backend/src/routes/audio_interview.py`, `backend/src/models/interview.py` |
| 3.4c (assessments) | `backend/src/utils/assessment_helpers.py`, `backend/src/utils/ai_analyzer.py`, `backend/src/models/assessment.py`, `backend/src/models/interview.py` |
| 3.4d (endpoint) | `backend/src/routes/interviews.py`, `backend/src/routes/auth.py` (decorator), `backend/src/models/assessment.py` |
| 3.5 (mocks) | `backend/tests/conftest.py`, `backend/src/config/openai_config.py`, `backend/src/utils/ai_analyzer.py` |

---

## 5. Como reportar ao final

Quando terminar (ou parar), siga o mesmo padrão do handoff original:

1. Liste cada item de 3.1 a 3.5 como **completo / parcial / não-feito**.
   Os itens 3.1, 3.3 e 3.4a já estão completos; 3.4b está parcial
   (código feito, sem smoke test).
2. Para cada item novo, diga o arquivo criado/alterado e o critério
   de aceite verificado.
3. Liste bloqueios (ex.: sem Postgres local, sem `OPENAI_API_KEY`).
4. **Pergunte ao usuário se pode commitar** e sugira mensagens no
   estilo `git log`:
   - `chore(migrations): add feedbacks, appointments, interview_assessments`
   - `feat(assessment): audit trail for interview scoring`
   - `fix(candidates): filter PII by role in to_dict`
   - `refactor(audio-interview): persist sessions in interviews table`
   - `test(openai): fix mocks for openai>=1.0`
5. **Não avance para Onda 3 sem autorização.**

---

**Boa continuação.** A infraestrutura (migrations + modelo
`InterviewAssessment` + `AIAnalyzer` auditável) já está pronta; a
segunda metade da Onda 2 é costurar isso na ponta (service, endpoint
e testes).

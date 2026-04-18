# API Documentation - Assistente RH

## Visão Geral

A API do Assistente RH fornece endpoints para gerenciar candidatos, entrevistas e análises de IA para processos seletivos.

**Base URL:** `http://localhost:5000/api`

## Autenticação

A API utiliza autenticação JWT (JSON Web Tokens). Inclua o token no header de todas as requisições:

```
Authorization: Bearer <seu_token_jwt>
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "usuario@email.com",
  "password": "senha123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "usuario@email.com",
    "full_name": "Nome do Usuário",
    "role": "recruiter"
  }
}
```

## Candidatos

### Listar Candidatos

```http
GET /api/candidates?page=1&per_page=20&search=nome&status=novo
```

**Parâmetros de Query:**
- `page` (int): Página (padrão: 1)
- `per_page` (int): Itens por página (padrão: 20)
- `search` (string): Busca por nome, email ou posição
- `status` (string): Filtrar por status
- `position` (string): Filtrar por posição
- `score_min` (int): Score mínimo
- `score_max` (int): Score máximo

**Resposta:**
```json
{
  "candidates": [
    {
      "id": 1,
      "full_name": "João Silva",
      "email": "joao@email.com",
      "position_applied": "Desenvolvedor Python",
      "status": "novo",
      "overall_score": 85.5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 156,
    "pages": 8
  }
}
```

### Criar Candidato

```http
POST /api/candidates
Content-Type: application/json

{
  "full_name": "Maria Santos",
  "email": "maria@email.com",
  "phone": "11999999999",
  "position_applied": "Analista de Dados",
  "experience_years": 3,
  "current_company": "Tech Corp",
  "current_position": "Analista Jr",
  "skills": ["Python", "SQL", "Power BI"],
  "consent_given": true
}
```

**Resposta:**
```json
{
  "id": 2,
  "full_name": "Maria Santos",
  "email": "maria@email.com",
  "status": "novo",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Buscar Candidato

```http
GET /api/candidates/{id}
```

**Resposta:**
```json
{
  "id": 1,
  "full_name": "João Silva",
  "email": "joao@email.com",
  "phone": "11999999999",
  "position_applied": "Desenvolvedor Python",
  "experience_years": 5,
  "skills": ["Python", "Django", "PostgreSQL"],
  "status": "entrevista_realizada",
  "overall_score": 85.5,
  "technical_score": 88.0,
  "behavioral_score": 83.0,
  "ai_recommendation": "CONTRATAR",
  "created_at": "2024-01-10T09:15:00Z",
  "interview_completed": "2024-01-12T14:30:00Z"
}
```

### Atualizar Candidato

```http
PUT /api/candidates/{id}
Content-Type: application/json

{
  "status": "aprovado",
  "interview_notes": "Candidato demonstrou excelente conhecimento técnico"
}
```

### Deletar Candidato

```http
DELETE /api/candidates/{id}
```

## Entrevistas

### Criar Entrevista

```http
POST /api/interviews
Content-Type: application/json

{
  "candidate_id": 1,
  "position": "Desenvolvedor Python",
  "interview_type": "audio"
}
```

**Resposta:**
```json
{
  "id": 1,
  "candidate_id": 1,
  "interviewer_id": 1,
  "position": "Desenvolvedor Python",
  "interview_type": "audio",
  "status": "agendada",
  "created_at": "2024-01-15T11:30:00Z"
}
```

### Iniciar Entrevista

```http
POST /api/interviews/{id}/start
```

**Resposta:**
```json
{
  "interview_id": 1,
  "question": {
    "id": 1,
    "question": "Conte-me sobre sua experiência com desenvolvimento de software.",
    "category": "technical",
    "audio_path": "/uploads/interviews/1/questions/question_0.wav"
  },
  "question_index": 0,
  "total_questions": 5,
  "status": "em_andamento"
}
```

### Obter Próxima Pergunta

```http
GET /api/interviews/{id}/question/next
```

**Resposta:**
```json
{
  "interview_id": 1,
  "question": {
    "id": 2,
    "question": "Como você aborda a resolução de problemas técnicos complexos?",
    "category": "problem_solving",
    "audio_path": "/uploads/interviews/1/questions/question_1.wav"
  },
  "question_index": 1,
  "total_questions": 5,
  "progress": 20.0
}
```

### Enviar Resposta

```http
POST /api/interviews/{id}/respond
Content-Type: multipart/form-data

response_text: "Minha experiência inclui 5 anos desenvolvendo..."
audio_file: [arquivo de áudio]
```

**Resposta:**
```json
{
  "success": true,
  "is_last_question": false,
  "next_question_index": 2,
  "progress": 40.0,
  "audio_analysis": {
    "confidence": 0.85,
    "clarity": 0.90,
    "energy": 0.75
  },
  "content_analysis": {
    "relevance": 88,
    "technical_accuracy": 85,
    "communication": 92
  }
}
```

### Finalizar Entrevista

```http
POST /api/interviews/{id}/finalize
```

**Resposta:**
```json
{
  "interview_id": 1,
  "overall_score": 85.5,
  "recommendation": "CONTRATAR",
  "confidence_level": 0.92,
  "behavioral_scores": {
    "confidence": 85.0,
    "enthusiasm": 80.0,
    "clarity": 90.0,
    "nervousness": 15.0
  },
  "content_scores": {
    "relevance": 88.0,
    "technical_accuracy": 85.0,
    "communication": 92.0
  },
  "insights": {
    "summary": "Candidato demonstrou excelente performance na entrevista.",
    "strengths": [
      "Demonstra alta confiança",
      "Excelentes habilidades de comunicação",
      "Conhecimento técnico sólido"
    ],
    "improvements": []
  },
  "next_steps": "Prosseguir com verificação de referências e proposta de contratação."
}
```

## Relatórios

### Estatísticas de Candidatos

```http
GET /api/reports/candidates/stats?recruiter_id=1
```

**Resposta:**
```json
{
  "total_candidates": 156,
  "status_distribution": {
    "novo": 45,
    "triagem": 23,
    "entrevista": 12,
    "entrevista_realizada": 38,
    "aprovado": 25,
    "rejeitado": 8,
    "contratado": 5
  },
  "position_distribution": {
    "Desenvolvedor Python": 45,
    "Analista de Dados": 32,
    "Gerente de Projetos": 28,
    "Designer UX": 25,
    "DevOps Engineer": 26
  },
  "average_scores": {
    "overall": 73.2,
    "technical": 75.8,
    "behavioral": 70.6
  },
  "monthly_trends": [
    {"month": "2024-01", "count": 28},
    {"month": "2024-02", "count": 35},
    {"month": "2024-03", "count": 42}
  ]
}
```

### Relatório de Entrevistas

```http
GET /api/reports/interviews?start_date=2024-01-01&end_date=2024-01-31
```

**Resposta:**
```json
{
  "total_interviews": 45,
  "completed_interviews": 38,
  "average_score": 73.5,
  "recommendations": {
    "CONTRATAR": 25,
    "CONSIDERAR": 8,
    "REJEITAR": 5
  },
  "position_performance": {
    "Desenvolvedor Python": {
      "interviews": 15,
      "average_score": 78.2,
      "hire_rate": 0.73
    }
  }
}
```

## LGPD - Conformidade

### Exportar Dados do Candidato

```http
GET /api/candidates/{id}/export
```

**Resposta:**
```json
{
  "candidate_data": {
    "id": 1,
    "full_name": "João Silva",
    "email": "joao@email.com",
    "created_at": "2024-01-10T09:15:00Z"
  },
  "interviews": [
    {
      "id": 1,
      "completed_at": "2024-01-12T14:30:00Z",
      "overall_score": 85.5
    }
  ],
  "export_date": "2024-01-15T12:00:00Z",
  "data_retention_info": {
    "retention_date": "2029-01-10T09:15:00Z",
    "can_request_deletion": true
  }
}
```

### Anonimizar Candidato

```http
POST /api/candidates/{id}/anonymize
```

**Resposta:**
```json
{
  "success": true,
  "message": "Dados do candidato foram anonimizados com sucesso"
}
```

## Códigos de Status

- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Requisição inválida
- `401` - Não autorizado
- `403` - Acesso negado
- `404` - Não encontrado
- `422` - Dados inválidos
- `500` - Erro interno do servidor

## Rate Limiting

A API possui limitação de taxa:
- **100 requisições por hora** por usuário
- **1000 requisições por hora** por IP

## Webhooks

O sistema pode enviar webhooks para eventos importantes:

### Entrevista Finalizada

```json
{
  "event": "interview.completed",
  "data": {
    "interview_id": 1,
    "candidate_id": 1,
    "overall_score": 85.5,
    "recommendation": "CONTRATAR"
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### Candidato Aprovado

```json
{
  "event": "candidate.approved",
  "data": {
    "candidate_id": 1,
    "position": "Desenvolvedor Python",
    "score": 85.5
  },
  "timestamp": "2024-01-15T15:00:00Z"
}
```


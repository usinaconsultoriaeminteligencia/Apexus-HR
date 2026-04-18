"""
seed_dev.py — Popula o banco de dados de desenvolvimento com dados de exemplo.

Uso (dentro do container):
    docker exec apexus_hr_backend_dev python scripts/seed_dev.py

Uso (local, com Postgres rodando):
    cd backend
    python scripts/seed_dev.py

O script é idempotente: verifica se os dados já existem antes de inserir.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Garante que src/ seja importável independente de onde o script for chamado
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.models import db
from src.models.user import User
from src.models.candidate import Candidate
from src.models.interview import Interview

# ---------------------------------------------------------------------------
# Dados de exemplo
# ---------------------------------------------------------------------------

USERS = [
    dict(
        email="admin@apexus.hr",
        full_name="Admin Apexus",
        role="admin",
        password="admin123",
    ),
    dict(
        email="recruiter@apexus.hr",
        full_name="Ana Recruiter",
        role="recruiter",
        password="recruiter123",
    ),
    dict(
        email="manager@apexus.hr",
        full_name="Carlos Manager",
        role="manager",
        password="manager123",
    ),
    dict(
        email="viewer@apexus.hr",
        full_name="Diana Viewer",
        role="viewer",
        password="viewer123",
    ),
]

CANDIDATES = [
    dict(
        full_name="Lucas Andrade",
        email="lucas.andrade@email.com",
        phone="+55 11 91234-5678",
        position_applied="Engenheiro de Software Sênior",
        experience_years=7,
        current_company="TechCorp Brasil",
        current_position="Desenvolvedor Pleno",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "React"],
        source="LinkedIn",
        status="entrevistado",
        overall_score=8.7,
        technical_score=9.1,
        behavioral_score=8.3,
        cultural_fit_score=8.6,
        ai_recommendation="contratar",
        ai_confidence=0.91,
        consent_given=True,
    ),
    dict(
        full_name="Mariana Costa",
        email="mariana.costa@email.com",
        phone="+55 21 92345-6789",
        position_applied="Product Manager",
        experience_years=5,
        current_company="Fintech SA",
        current_position="PM Pleno",
        skills=["Roadmapping", "OKRs", "SQL", "Figma", "Agile"],
        source="Indicação",
        status="aprovado",
        overall_score=9.2,
        technical_score=8.8,
        behavioral_score=9.5,
        cultural_fit_score=9.3,
        ai_recommendation="contratar",
        ai_confidence=0.95,
        consent_given=True,
    ),
    dict(
        full_name="Rafael Souza",
        email="rafael.souza@email.com",
        phone="+55 31 93456-7890",
        position_applied="Analista de Dados",
        experience_years=3,
        current_company="Consultoria XYZ",
        current_position="Analista Jr",
        skills=["Python", "Pandas", "SQL", "Power BI", "Spark"],
        source="Gupy",
        status="em_análise",
        overall_score=7.4,
        technical_score=7.8,
        behavioral_score=7.1,
        cultural_fit_score=7.2,
        ai_recommendation="aguardar",
        ai_confidence=0.72,
        consent_given=True,
    ),
    dict(
        full_name="Juliana Ferreira",
        email="juliana.ferreira@email.com",
        phone="+55 41 94567-8901",
        position_applied="Engenheira de DevOps",
        experience_years=6,
        current_company="Cloud Soluções",
        current_position="DevOps Engineer",
        skills=["Kubernetes", "Terraform", "AWS", "GitLab CI", "Prometheus"],
        source="LinkedIn",
        status="agendado",
        overall_score=None,
        technical_score=None,
        behavioral_score=None,
        cultural_fit_score=None,
        ai_recommendation=None,
        ai_confidence=None,
        consent_given=True,
    ),
    dict(
        full_name="Pedro Oliveira",
        email="pedro.oliveira@email.com",
        phone="+55 51 95678-9012",
        position_applied="Designer UX/UI",
        experience_years=4,
        current_company="Agência Criativa",
        current_position="Designer Sênior",
        skills=["Figma", "Adobe XD", "Prototipagem", "User Research", "CSS"],
        source="Behance",
        status="reprovado",
        overall_score=5.8,
        technical_score=6.2,
        behavioral_score=5.5,
        cultural_fit_score=5.7,
        ai_recommendation="não contratar",
        ai_confidence=0.83,
        consent_given=True,
    ),
    dict(
        full_name="Fernanda Lima",
        email="fernanda.lima@email.com",
        phone="+55 11 96789-0123",
        position_applied="Engenheira de Machine Learning",
        experience_years=5,
        current_company="AI Startup",
        current_position="ML Engineer",
        skills=["PyTorch", "TensorFlow", "MLOps", "Python", "Docker"],
        source="GitHub",
        status="entrevistado",
        overall_score=8.9,
        technical_score=9.4,
        behavioral_score=8.4,
        cultural_fit_score=8.9,
        ai_recommendation="contratar",
        ai_confidence=0.93,
        consent_given=True,
    ),
]

# Entrevistas a criar (referenciadas por índice de CANDIDATES + índice de USERS)
# (candidate_idx, interviewer_idx, status, dias_atrás, scores)
INTERVIEWS_SPEC = [
    (0, 1, "concluida", 5,
     dict(overall_score=8.7, confidence_score=8.5, enthusiasm_score=9.0,
          clarity_score=8.8, communication_skills=8.6, technical_accuracy=9.1,
          recommendation="contratar", confidence_level=0.91,
          ai_insights="Candidato demonstrou sólido conhecimento técnico em Python e sistemas distribuídos. "
                      "Respostas claras e estruturadas. Recomenda-se avançar para proposta.",
          interviewer_notes="Excelente candidato. Experiência relevante e boa fit cultural.")),
    (1, 1, "concluida", 3,
     dict(overall_score=9.2, confidence_score=9.0, enthusiasm_score=9.5,
          clarity_score=9.3, communication_skills=9.4, technical_accuracy=8.8,
          recommendation="contratar", confidence_level=0.95,
          ai_insights="Candidata com perfil estratégico excepcional. Histórico comprovado de liderança "
                      "de produto e entrega de OKRs. Alta aderência cultural.",
          interviewer_notes="Uma das melhores entrevistas do trimestre. Aprovada com destaque.")),
    (2, 2, "em_andamento", 1,
     dict(overall_score=None, confidence_score=7.2, enthusiasm_score=7.5,
          clarity_score=7.0, communication_skills=7.1, technical_accuracy=7.8,
          recommendation=None, confidence_level=None,
          ai_insights=None,
          interviewer_notes=None)),
    (5, 1, "concluida", 7,
     dict(overall_score=8.9, confidence_score=8.7, enthusiasm_score=9.1,
          clarity_score=9.0, communication_skills=8.8, technical_accuracy=9.4,
          recommendation="contratar", confidence_level=0.93,
          ai_insights="Candidata com domínio técnico avançado em ML e MLOps. "
                      "Demonstrou capacidade de resolver problemas complexos com clareza.",
          interviewer_notes="Perfil técnico muito acima da média. Aprovada.")),
    (3, 2, "agendada", -2,  # agendada no futuro
     dict(overall_score=None, confidence_score=None, enthusiasm_score=None,
          clarity_score=None, communication_skills=None, technical_accuracy=None,
          recommendation=None, confidence_level=None,
          ai_insights=None,
          interviewer_notes=None)),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upsert_user(u_data: dict) -> User:
    user = User.query.filter_by(email=u_data["email"]).first()
    if user:
        print(f"  [skip] usuário já existe: {u_data['email']}")
        return user
    user = User(
        email=u_data["email"],
        full_name=u_data["full_name"],
        role=u_data["role"],
        is_active=True,
        is_verified=True,
        consent_given=True,
    )
    user.set_password(u_data["password"])
    db.session.add(user)
    db.session.flush()
    print(f"  [ok] usuário criado: {u_data['email']} ({u_data['role']})")
    return user


def upsert_candidate(c_data: dict, recruiter: User) -> Candidate:
    candidate = Candidate.query.filter_by(email=c_data["email"]).first()
    if candidate:
        print(f"  [skip] candidato já existe: {c_data['email']}")
        return candidate

    import json
    candidate = Candidate(
        full_name=c_data["full_name"],
        email=c_data["email"],
        phone=c_data.get("phone"),
        position_applied=c_data["position_applied"],
        experience_years=c_data.get("experience_years"),
        current_company=c_data.get("current_company"),
        current_position=c_data.get("current_position"),
        skills=json.dumps(c_data.get("skills", []), ensure_ascii=False),
        source=c_data.get("source"),
        recruiter_id=recruiter.id,
        status=c_data.get("status", "novo"),
        overall_score=c_data.get("overall_score"),
        technical_score=c_data.get("technical_score"),
        behavioral_score=c_data.get("behavioral_score"),
        cultural_fit_score=c_data.get("cultural_fit_score"),
        ai_recommendation=c_data.get("ai_recommendation"),
        ai_confidence=c_data.get("ai_confidence"),
        consent_given=c_data.get("consent_given", True),
        consent_date=_now(),
        is_active=True,
    )
    db.session.add(candidate)
    db.session.flush()
    print(f"  [ok] candidato criado: {c_data['full_name']} — {c_data['position_applied']}")
    return candidate


def create_interview(candidate: Candidate, interviewer: User, spec: dict, days_ago: int) -> Interview:
    base_time = _now() - timedelta(days=days_ago)
    scheduled_at = base_time.replace(hour=10, minute=0, second=0)
    started_at = scheduled_at if spec["status"] in ("concluida", "em_andamento") else None
    completed_at = scheduled_at + timedelta(minutes=45) if spec["status"] == "concluida" else None

    interview = Interview(
        candidate_id=candidate.id,
        interviewer_id=interviewer.id,
        interview_type="audio",
        position=candidate.position_applied,
        scheduled_at=scheduled_at,
        started_at=started_at,
        completed_at=completed_at,
        duration_minutes=45 if completed_at else None,
        status=spec["status"],
        overall_score=spec.get("overall_score"),
        confidence_score=spec.get("confidence_score"),
        enthusiasm_score=spec.get("enthusiasm_score"),
        clarity_score=spec.get("clarity_score"),
        communication_skills=spec.get("communication_skills"),
        technical_accuracy=spec.get("technical_accuracy"),
        recommendation=spec.get("recommendation"),
        confidence_level=spec.get("confidence_level"),
        ai_insights=spec.get("ai_insights"),
        interviewer_notes=spec.get("interviewer_notes"),
        is_active=True,
        consent_given=True,
        consent_date=_now(),
    )
    db.session.add(interview)
    db.session.flush()
    print(f"  [ok] entrevista criada: {candidate.full_name} ({spec['status']})")
    return interview


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def seed():
    print("\n=== Apexus HR — Seed de Desenvolvimento ===\n")

    with app.app_context():
        print("→ Criando usuários...")
        users = [upsert_user(u) for u in USERS]
        db.session.flush()

        recruiter = users[1]  # Ana Recruiter

        print("\n→ Criando candidatos...")
        candidates = [upsert_candidate(c, recruiter) for c in CANDIDATES]
        db.session.flush()

        print("\n→ Criando entrevistas...")
        for (cand_idx, interviewer_idx, status, days_ago, scores) in INTERVIEWS_SPEC:
            spec = {"status": status, **scores}
            create_interview(candidates[cand_idx], users[interviewer_idx], spec, days_ago)

        db.session.commit()

    print("\n✓ Seed concluído com sucesso!")
    print("\nCredenciais de acesso:")
    for u in USERS:
        print(f"  {u['role']:12s}  {u['email']:35s}  senha: {u['password']}")
    print()


if __name__ == "__main__":
    seed()

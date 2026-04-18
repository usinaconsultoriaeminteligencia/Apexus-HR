# backend/src/models/candidate.py
"""
Modelo de candidato com conformidade LGPD (Flask-SQLAlchemy)
"""
from datetime import datetime, timedelta, timezone
import json

from src.models import db
from src.models import BaseModel

class Candidate(BaseModel):
    """Modelo de candidato"""
    __tablename__ = 'candidates'

    # Dados pessoais
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(20))

    # Dados profissionais
    position_applied = db.Column(db.String(255), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    current_company = db.Column(db.String(255))
    current_position = db.Column(db.String(255))
    skills = db.Column(db.Text)  # JSON string com habilidades

    # Dados de recrutamento
    source = db.Column(db.String(100))  # LinkedIn, site, indicação, etc.
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='novo')  # novo, triagem, entrevista, aprovado, rejeitado

    # Scoring e avaliação
    overall_score = db.Column(db.Float, default=0.0)
    technical_score = db.Column(db.Float, default=0.0)
    behavioral_score = db.Column(db.Float, default=0.0)
    cultural_fit_score = db.Column(db.Float, default=0.0)

    # Dados da entrevista
    interview_scheduled = db.Column(db.DateTime)
    interview_completed = db.Column(db.DateTime)
    interview_notes = db.Column(db.Text)
    interview_recording_path = db.Column(db.String(500))

    # Análise de IA
    ai_analysis = db.Column(db.Text)  # JSON com análise detalhada
    ai_recommendation = db.Column(db.String(50))  # CONTRATAR, CONSIDERAR, REJEITAR
    ai_confidence = db.Column(db.Float, default=0.0)

    # Dados LGPD específicos
    cv_file_path = db.Column(db.String(500))
    portfolio_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))

    # Relacionamentos
    recruiter = db.relationship("User", foreign_keys=[recruiter_id])
    # interviews = db.relationship("Interview", back_populates="candidate")

    def calculate_overall_score(self):
        weights = {'technical': 0.4, 'behavioral': 0.3, 'cultural_fit': 0.3}
        self.overall_score = (
            (self.technical_score or 0) * weights['technical'] +
            (self.behavioral_score or 0) * weights['behavioral'] +
            (self.cultural_fit_score or 0) * weights['cultural_fit']
        )
        return self.overall_score

    def get_skills_list(self):
        if not self.skills:
            return []
        try:
            return json.loads(self.skills)
        except json.JSONDecodeError:
            # Se não for JSON válido, tratar como string separada por vírgulas
            return self.skills.split(',') if self.skills else []
        except Exception as e:
            # Log do erro para debugging
            import logging
            logging.warning(f"Erro inesperado ao processar skills: {e}")
            return []

    def set_skills_list(self, skills_list):
        self.skills = json.dumps(skills_list) if isinstance(skills_list, list) else str(skills_list)

    def get_ai_analysis_dict(self):
        if not self.ai_analysis:
            return {}
        try:
            return json.loads(self.ai_analysis)
        except Exception:
            return {}

    def set_ai_analysis_dict(self, analysis_dict):
        self.ai_analysis = json.dumps(analysis_dict, ensure_ascii=False)

    def anonymize(self):
        super().anonymize()
        self.full_name = f"Candidato_{self.id}"
        self.email = f"anonimo_{self.id}@example.com"
        self.phone = None
        self.current_company = "Empresa Anônima"
        self.linkedin_url = None

    def get_retention_date(self):
        return self.created_at + timedelta(days=5*365)

    def should_be_anonymized(self):
        if self.anonymized:
            return False
        if self.status in ['rejeitado', 'desistiu']:
            return datetime.now(timezone.utc).replace(tzinfo=None) > (self.created_at + timedelta(days=2*365))
        return False

    def get_status_display(self):
        status_map = {
            'novo': 'Novo',
            'triagem': 'Em Triagem',
            'entrevista': 'Entrevista Agendada',
            'entrevista_realizada': 'Entrevista Realizada',
            'aprovado': 'Aprovado',
            'rejeitado': 'Rejeitado',
            'contratado': 'Contratado',
            'desistiu': 'Desistiu'
        }
        return status_map.get(self.status, self.status)

    # Papéis que têm permissão para visualizar PII completo/sensível.
    # Onda 2 — item 3.3: 'viewer' e 'analyst' NÃO recebem telefone,
    # linkedin_url, ai_analysis, interview_notes nem email completo,
    # mesmo quando include_sensitive=True.
    PII_PRIVILEGED_ROLES = frozenset({'admin', 'recruiter', 'manager'})

    @staticmethod
    def _mask_email(email):
        """Mascara o email para 'j***@example.com'."""
        if not email or '@' not in email:
            return email
        local, _, domain = email.partition('@')
        if not local:
            return email
        visible = local[0]
        return f"{visible}***@{domain}"

    def to_dict(self, include_sensitive=False, role=None):
        """Serializa candidato para dicionário respeitando papel (role).

        Args:
            include_sensitive: se True, tenta incluir PII sensível.
            role: papel do usuário solicitante. Papéis fora de
                PII_PRIVILEGED_ROLES (ex.: 'viewer', 'analyst') recebem
                versão reduzida: email mascarado, sem telefone/linkedin
                /ai_analysis/interview_notes.
        """
        privileged = role is None or role in self.PII_PRIVILEGED_ROLES

        if self.anonymized:
            email_value = None
        elif privileged:
            email_value = self.email
        else:
            email_value = self._mask_email(self.email)

        data = {
            'id': self.id,
            'full_name': self.full_name,
            'email': email_value,
            'position_applied': self.position_applied,
            'experience_years': self.experience_years,
            'skills': self.get_skills_list(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'overall_score': round(self.overall_score or 0, 1),
            'technical_score': round(self.technical_score or 0, 1),
            'behavioral_score': round(self.behavioral_score or 0, 1),
            'cultural_fit_score': round(self.cultural_fit_score or 0, 1),
            'ai_recommendation': self.ai_recommendation,
            'ai_confidence': round(self.ai_confidence or 0, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'interview_scheduled': self.interview_scheduled.isoformat() if self.interview_scheduled else None,
            'interview_completed': self.interview_completed.isoformat() if self.interview_completed else None,
            'anonymized': self.anonymized
        }
        if include_sensitive and not self.anonymized and privileged:
            data.update({
                'phone': self.phone,
                'current_company': self.current_company,
                'current_position': self.current_position,
                'linkedin_url': self.linkedin_url,
                'interview_notes': self.interview_notes,
                'ai_analysis': self.get_ai_analysis_dict()
            })
        return data


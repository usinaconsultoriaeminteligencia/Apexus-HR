# backend/src/models/assessment.py
"""
Modelo de avaliação auditável por pergunta/rubrica de entrevista.

Cada linha representa a nota atribuída a UMA dimensão (rubrica) para UMA
resposta de UMA entrevista, com evidência textual, versão do modelo e
status de revisão humana. É a base da trilha de auditoria exigida pela
tese de "sistema auditável de inteligência comportamental" (Onda 2).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from . import BaseModel


class InterviewAssessment(BaseModel):
    """Avaliação auditável por pergunta, com rubrica versionada."""

    __tablename__ = 'interview_assessments'

    # Relação com a entrevista
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False, index=True)

    # Posição/origem da pergunta
    question_index = Column(Integer, nullable=False, default=0)
    question_text = Column(Text, nullable=False)

    # Evidência textual (trecho da resposta que sustenta a nota)
    answer_excerpt = Column(Text)

    # Rubrica aplicada (id canônico + versão da rubrica)
    # Ex.: rubric_id='competencies.data_driven_decision', dimension='decision'
    rubric_id = Column(String(100), nullable=False, index=True)
    rubric_version = Column(String(40), nullable=False)
    dimension = Column(String(100), nullable=False)

    # Nota (escala 1..5) e confiança (0..1)
    score = Column(Float)
    confidence = Column(Float, default=0.0)

    # Rastreamento do modelo que gerou o score
    model_name = Column(String(100))       # ex.: 'openai:gpt-4o-mini' ou 'fallback'
    model_version = Column(String(100))    # id/metadata do response quando disponível
    prompt_hash = Column(String(64))       # sha256(prompt_efetivo)[:16]

    # Trilha de revisão humana
    human_review_status = Column(
        String(20), nullable=False, default='pending'
    )  # pending | approved | adjusted | rejected
    human_reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    human_review_notes = Column(Text)
    adjusted_score = Column(Float)
    human_reviewed_at = Column(DateTime)

    # Relacionamentos
    interview = relationship("Interview", foreign_keys=[interview_id])
    human_reviewer = relationship("User", foreign_keys=[human_reviewer_id])

    VALID_REVIEW_STATUSES = ('pending', 'approved', 'adjusted', 'rejected')

    def effective_score(self):
        """Retorna o score adotado: adjusted_score se revisado, senão score."""
        if self.human_review_status == 'adjusted' and self.adjusted_score is not None:
            return float(self.adjusted_score)
        if self.score is None:
            return None
        return float(self.score)

    def mark_reviewed(self, reviewer_id: int, status: str, notes: str = None,
                      adjusted_score: float = None):
        """Registra revisão humana do assessment."""
        if status not in self.VALID_REVIEW_STATUSES:
            raise ValueError(f"status inválido: {status}")
        self.human_review_status = status
        self.human_reviewer_id = reviewer_id
        self.human_review_notes = notes
        self.human_reviewed_at = datetime.utcnow()
        if adjusted_score is not None:
            self.adjusted_score = float(adjusted_score)

    def to_dict(self, include_evidence: bool = True) -> dict:
        """Serializa para dicionário.

        include_evidence: se False, omite answer_excerpt e question_text
        completos (para papéis viewer/analyst que não devem ver PII da
        resposta completa).
        """
        data = {
            'id': self.id,
            'interview_id': self.interview_id,
            'question_index': self.question_index,
            'rubric_id': self.rubric_id,
            'rubric_version': self.rubric_version,
            'dimension': self.dimension,
            'score': round(float(self.score), 2) if self.score is not None else None,
            'effective_score': (
                round(self.effective_score(), 2)
                if self.effective_score() is not None else None
            ),
            'confidence': round(float(self.confidence or 0.0), 2),
            'model_name': self.model_name,
            'model_version': self.model_version,
            'prompt_hash': self.prompt_hash,
            'human_review_status': self.human_review_status,
            'human_reviewer_id': self.human_reviewer_id,
            'human_reviewed_at': (
                self.human_reviewed_at.isoformat() if self.human_reviewed_at else None
            ),
            'adjusted_score': (
                round(float(self.adjusted_score), 2)
                if self.adjusted_score is not None else None
            ),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_evidence:
            data['question_text'] = self.question_text
            data['answer_excerpt'] = self.answer_excerpt
            data['human_review_notes'] = self.human_review_notes
        return data

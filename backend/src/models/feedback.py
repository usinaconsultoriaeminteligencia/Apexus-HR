"""
Modelo de feedback/avaliação do sistema
"""
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import json
from src.models import db
from src.models import BaseModel
from ..utils.type_helpers import as_str, dt_iso, as_int, as_float


class Feedback(BaseModel):
    """Modelo de feedback do sistema"""
    __tablename__ = 'feedbacks'
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=True)
    
    # Tipo de feedback
    feedback_type = Column(String(50), nullable=False)  # system, interview, candidate, feature
    category = Column(String(50))  # bug, suggestion, complaint, praise
    
    # Conteúdo
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 estrelas
    
    # Status
    status = Column(String(50), default='pending')  # pending, reviewed, resolved, dismissed
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    
    # Resposta/Resolução
    admin_response = Column(Text)
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime)
    
    # Metadados
    user_agent = Column(String(500))
    page_url = Column(String(500))
    metadata_json = Column('metadata', Text)  # JSON com dados adicionais (coluna chamada 'metadata' no banco)
    
    # Relacionamentos
    user = relationship("User", foreign_keys=[user_id])
    interview = relationship("Interview", foreign_keys=[interview_id])
    candidate = relationship("Candidate", foreign_keys=[candidate_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    def set_metadata(self, data: dict):
        """Define metadados como JSON"""
        self.metadata_json = json.dumps(data, ensure_ascii=False)
    
    def get_metadata(self) -> dict:
        """Retorna metadados como dicionário"""
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except:
            return {}
    
    def resolve(self, admin_id: int, response: str = None):
        """Marca feedback como resolvido"""
        self.status = 'resolved'
        self.resolved_by = admin_id
        self.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if response:
            self.admin_response = response
    
    def to_dict(self, include_sensitive: bool = False):
        """Converte para dicionário"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'rating': self.rating,
            'status': self.status,
            'priority': self.priority,
            'created_at': dt_iso(self.created_at),
            'interview_id': self.interview_id,
            'candidate_id': self.candidate_id
        }
        
        if include_sensitive:
            data.update({
                'admin_response': self.admin_response,
                'resolved_by': self.resolved_by,
                'resolved_at': dt_iso(self.resolved_at),
                'metadata': self.get_metadata(),  # Retorna como 'metadata' no dict
                'user_agent': self.user_agent,
                'page_url': self.page_url
            })
        
        return data


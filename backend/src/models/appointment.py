"""
Modelo de agendamento de entrevistas
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import json
import uuid
from . import BaseModel
from ..utils.type_helpers import as_str, dt_iso, as_int, safe_bool


class Appointment(BaseModel):
    """Modelo de agendamento"""
    __tablename__ = 'appointments'
    
    # Relacionamentos
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    interviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=True)
    
    # Dados do agendamento
    appointment_token = Column(String(36), unique=True, index=True)  # UUID para acesso público
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Datas e horários
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    timezone = Column(String(50), default='America/Sao_Paulo')
    
    # Status
    status = Column(String(50), default='pending')  # pending, confirmed, cancelled, completed, no_show
    confirmation_status = Column(String(50), default='pending')  # pending, confirmed, declined
    
    # Notificações
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime)
    
    # Localização/Meio
    location = Column(String(500))  # Endereço físico ou link para video
    meeting_type = Column(String(50), default='audio')  # audio, video, presencial
    meeting_link = Column(String(500))  # Link para video conferência
    
    # Metadados
    notes = Column(Text)
    cancellation_reason = Column(Text)
    cancelled_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    cancelled_at = Column(DateTime)
    
    # Relacionamentos
    candidate = relationship("Candidate", foreign_keys=[candidate_id])
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    interview = relationship("Interview", foreign_keys=[interview_id])
    canceller = relationship("User", foreign_keys=[cancelled_by])
    
    def generate_token(self):
        """Gera token único para o agendamento"""
        self.appointment_token = str(uuid.uuid4())
        return self.appointment_token
    
    def confirm(self):
        """Confirma o agendamento"""
        self.status = 'confirmed'
        self.confirmation_status = 'confirmed'
        self.confirmation_sent = True
        self.confirmation_sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    def decline(self, reason: str = None):
        """Recusa o agendamento"""
        self.status = 'cancelled'
        self.confirmation_status = 'declined'
        if reason:
            self.cancellation_reason = reason
    
    def cancel(self, user_id: int, reason: str = None):
        """Cancela o agendamento"""
        self.status = 'cancelled'
        self.cancelled_by = user_id
        self.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if reason:
            self.cancellation_reason = reason
    
    def is_upcoming(self) -> bool:
        """Verifica se o agendamento está no futuro"""
        if not self.scheduled_at:
            return False
        return datetime.now(timezone.utc).replace(tzinfo=None) < self.scheduled_at
    
    def is_past(self) -> bool:
        """Verifica se o agendamento já passou"""
        if not self.scheduled_at:
            return False
        return datetime.now(timezone.utc).replace(tzinfo=None) > (self.scheduled_at + timedelta(minutes=self.duration_minutes))
    
    def get_reminder_time(self, hours_before: int = 24) -> datetime:
        """Retorna horário para enviar lembrete"""
        if not self.scheduled_at:
            return None
        return self.scheduled_at - timedelta(hours=hours_before)
    
    def should_send_reminder(self, hours_before: int = 24) -> bool:
        """Verifica se deve enviar lembrete"""
        if self.reminder_sent or self.status != 'confirmed':
            return False
        
        reminder_time = self.get_reminder_time(hours_before)
        if not reminder_time:
            return False
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Enviar lembrete se estiver dentro de 1 hora do horário ideal
        return reminder_time <= now <= reminder_time + timedelta(hours=1)
    
    def to_dict(self, include_sensitive: bool = False):
        """Converte para dicionário"""
        data = {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'interviewer_id': self.interviewer_id,
            'interview_id': self.interview_id,
            'appointment_token': self.appointment_token,
            'title': self.title,
            'description': self.description,
            'scheduled_at': dt_iso(self.scheduled_at),
            'duration_minutes': self.duration_minutes,
            'timezone': self.timezone,
            'status': self.status,
            'confirmation_status': self.confirmation_status,
            'meeting_type': self.meeting_type,
            'location': self.location,
            'meeting_link': self.meeting_link,
            'is_upcoming': self.is_upcoming(),
            'is_past': self.is_past(),
            'created_at': dt_iso(self.created_at)
        }
        
        if include_sensitive:
            data.update({
                'notes': self.notes,
                'cancellation_reason': self.cancellation_reason,
                'cancelled_by': self.cancelled_by,
                'cancelled_at': dt_iso(self.cancelled_at),
                'reminder_sent': safe_bool(self.reminder_sent),
                'reminder_sent_at': dt_iso(self.reminder_sent_at),
                'confirmation_sent': safe_bool(self.confirmation_sent),
                'confirmation_sent_at': dt_iso(self.confirmation_sent_at)
            })
        
        return data


"""
Serviço de gerenciamento de agendamentos
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models import Appointment, Candidate, User, Interview
from ..services.websocket_service import emit_to_user, emit_to_room

logger = logging.getLogger(__name__)


class AppointmentService:
    """Serviço para gerenciar agendamentos"""
    
    def create_appointment(self, db: Session, interviewer_id: int, appointment_data: Dict) -> Appointment:
        """Cria novo agendamento"""
        try:
            appointment = Appointment(
                candidate_id=appointment_data['candidate_id'],
                interviewer_id=interviewer_id,
                interview_id=appointment_data.get('interview_id'),
                title=appointment_data.get('title', 'Entrevista'),
                description=appointment_data.get('description'),
                scheduled_at=appointment_data['scheduled_at'],
                duration_minutes=appointment_data.get('duration_minutes', 30),
                timezone=appointment_data.get('timezone', 'America/Sao_Paulo'),
                meeting_type=appointment_data.get('meeting_type', 'audio'),
                location=appointment_data.get('location'),
                meeting_link=appointment_data.get('meeting_link'),
                notes=appointment_data.get('notes'),
                status='pending',
                confirmation_status='pending'
            )
            
            # Gerar token único
            appointment.generate_token()
            
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            # Notificar candidato via WebSocket
            self._notify_candidate_new_appointment(appointment)
            
            logger.info(f"Agendamento criado: {appointment.id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {e}")
            db.rollback()
            raise
    
    def get_appointment(self, db: Session, appointment_id: int) -> Optional[Appointment]:
        """Busca agendamento por ID"""
        return db.query(Appointment).filter_by(id=appointment_id, is_active=True).first()
    
    def get_appointment_by_token(self, db: Session, token: str) -> Optional[Appointment]:
        """Busca agendamento por token"""
        return db.query(Appointment).filter_by(
            appointment_token=token,
            is_active=True
        ).first()
    
    def list_appointments(self, db: Session, filters: Dict = None, page: int = 1,
                         per_page: int = 20) -> Dict:
        """Lista agendamentos com filtros e paginação"""
        try:
            query = db.query(Appointment).filter(Appointment.is_active == True)
            
            if filters:
                if filters.get('candidate_id'):
                    query = query.filter(Appointment.candidate_id == filters['candidate_id'])
                
                if filters.get('interviewer_id'):
                    query = query.filter(Appointment.interviewer_id == filters['interviewer_id'])
                
                if filters.get('status'):
                    query = query.filter(Appointment.status == filters['status'])
                
                if filters.get('date_from'):
                    query = query.filter(Appointment.scheduled_at >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(Appointment.scheduled_at <= filters['date_to'])
                
                if filters.get('upcoming_only'):
                    query = query.filter(Appointment.scheduled_at > datetime.now(timezone.utc).replace(tzinfo=None))
            
            # Ordenação
            order_by = filters.get('order_by', 'scheduled_at') if filters else 'scheduled_at'
            order_dir = filters.get('order_dir', 'asc') if filters else 'asc'
            
            if hasattr(Appointment, order_by):
                if order_dir == 'asc':
                    query = query.order_by(getattr(Appointment, order_by).asc())
                else:
                    query = query.order_by(getattr(Appointment, order_by).desc())
            
            # Paginação
            total = query.count()
            appointments = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'appointments': [a.to_dict() for a in appointments],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar agendamentos: {e}")
            raise
    
    def confirm_appointment(self, db: Session, appointment_id: int) -> Appointment:
        """Confirma agendamento"""
        try:
            appointment = self.get_appointment(db, appointment_id)
            if not appointment:
                raise ValueError("Agendamento não encontrado")
            
            appointment.confirm()
            db.commit()
            db.refresh(appointment)
            
            # Notificar entrevistador
            emit_to_user(
                appointment.interviewer_id,
                'appointment_confirmed',
                {
                    'appointment_id': appointment.id,
                    'candidate_name': appointment.candidate.full_name if appointment.candidate else 'Candidato',
                    'scheduled_at': appointment.scheduled_at.isoformat(),
                    'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                }
            )
            
            logger.info(f"Agendamento {appointment_id} confirmado")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao confirmar agendamento: {e}")
            db.rollback()
            raise
    
    def decline_appointment(self, db: Session, appointment_id: int, reason: str = None) -> Appointment:
        """Recusa agendamento"""
        try:
            appointment = self.get_appointment(db, appointment_id)
            if not appointment:
                raise ValueError("Agendamento não encontrado")
            
            appointment.decline(reason)
            db.commit()
            db.refresh(appointment)
            
            # Notificar entrevistador
            emit_to_user(
                appointment.interviewer_id,
                'appointment_declined',
                {
                    'appointment_id': appointment.id,
                    'reason': reason,
                    'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                }
            )
            
            logger.info(f"Agendamento {appointment_id} recusado")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao recusar agendamento: {e}")
            db.rollback()
            raise
    
    def cancel_appointment(self, db: Session, appointment_id: int, user_id: int,
                          reason: str = None) -> Appointment:
        """Cancela agendamento"""
        try:
            appointment = self.get_appointment(db, appointment_id)
            if not appointment:
                raise ValueError("Agendamento não encontrado")
            
            appointment.cancel(user_id, reason)
            db.commit()
            db.refresh(appointment)
            
            # Notificar ambas as partes
            emit_to_user(
                appointment.candidate_id,
                'appointment_cancelled',
                {
                    'appointment_id': appointment.id,
                    'reason': reason,
                    'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                }
            )
            
            emit_to_user(
                appointment.interviewer_id,
                'appointment_cancelled',
                {
                    'appointment_id': appointment.id,
                    'reason': reason,
                    'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                }
            )
            
            logger.info(f"Agendamento {appointment_id} cancelado")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao cancelar agendamento: {e}")
            db.rollback()
            raise
    
    def get_upcoming_appointments(self, db: Session, user_id: int = None,
                                  days_ahead: int = 7) -> List[Appointment]:
        """Retorna agendamentos próximos"""
        try:
            query = db.query(Appointment).filter(
                and_(
                    Appointment.is_active == True,
                    Appointment.status == 'confirmed',
                    Appointment.scheduled_at >= datetime.now(timezone.utc).replace(tzinfo=None),
                    Appointment.scheduled_at <= datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days_ahead)
                )
            )
            
            if user_id:
                query = query.filter(
                    or_(
                        Appointment.candidate_id == user_id,
                        Appointment.interviewer_id == user_id
                    )
                )
            
            return query.order_by(Appointment.scheduled_at.asc()).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar agendamentos próximos: {e}")
            raise
    
    def check_reminders(self, db: Session) -> List[Appointment]:
        """Verifica agendamentos que precisam de lembrete"""
        try:
            appointments = db.query(Appointment).filter(
                and_(
                    Appointment.is_active == True,
                    Appointment.status == 'confirmed',
                    Appointment.reminder_sent == False
                )
            ).all()
            
            reminders_to_send = []
            for appointment in appointments:
                if appointment.should_send_reminder():
                    reminders_to_send.append(appointment)
            
            return reminders_to_send
            
        except Exception as e:
            logger.error(f"Erro ao verificar lembretes: {e}")
            raise
    
    def _notify_candidate_new_appointment(self, appointment: Appointment):
        """Notifica candidato sobre novo agendamento"""
        try:
            emit_to_user(
                appointment.candidate_id,
                'new_appointment',
                {
                    'appointment_id': appointment.id,
                    'title': appointment.title,
                    'scheduled_at': appointment.scheduled_at.isoformat(),
                    'appointment_token': appointment.appointment_token,
                    'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Erro ao notificar candidato: {e}")


# Instância global
appointment_service = AppointmentService()


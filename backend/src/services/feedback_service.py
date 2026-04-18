"""
Serviço de gerenciamento de feedback/avaliações
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models import Feedback, User
from ..services.websocket_service import emit_to_user, broadcast

logger = logging.getLogger(__name__)


class FeedbackService:
    """Serviço para gerenciar feedbacks"""
    
    def create_feedback(self, db: Session, user_id: int, feedback_data: Dict) -> Feedback:
        """Cria novo feedback"""
        try:
            feedback = Feedback(
                user_id=user_id,
                interview_id=feedback_data.get('interview_id'),
                candidate_id=feedback_data.get('candidate_id'),
                feedback_type=feedback_data.get('feedback_type', 'system'),
                category=feedback_data.get('category', 'suggestion'),
                title=feedback_data.get('title', '').strip(),
                description=feedback_data.get('description', '').strip(),
                rating=feedback_data.get('rating'),
                priority=feedback_data.get('priority', 'medium'),
                user_agent=feedback_data.get('user_agent'),
                page_url=feedback_data.get('page_url'),
                status='pending'
            )
            
            # Metadados adicionais
            if feedback_data.get('metadata'):
                feedback.set_metadata(feedback_data['metadata'])
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            # Notificar admins via WebSocket
            self._notify_admins_new_feedback(feedback)
            
            logger.info(f"Feedback criado: {feedback.id} por usuário {user_id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Erro ao criar feedback: {e}")
            db.rollback()
            raise
    
    def get_feedback(self, db: Session, feedback_id: int) -> Optional[Feedback]:
        """Busca feedback por ID"""
        return db.query(Feedback).filter_by(id=feedback_id, is_active=True).first()
    
    def list_feedbacks(self, db: Session, filters: Dict = None, page: int = 1, 
                      per_page: int = 20) -> Dict:
        """Lista feedbacks com filtros e paginação"""
        try:
            query = db.query(Feedback).filter(Feedback.is_active == True)
            
            if filters:
                if filters.get('user_id'):
                    query = query.filter(Feedback.user_id == filters['user_id'])
                
                if filters.get('feedback_type'):
                    query = query.filter(Feedback.feedback_type == filters['feedback_type'])
                
                if filters.get('status'):
                    query = query.filter(Feedback.status == filters['status'])
                
                if filters.get('category'):
                    query = query.filter(Feedback.category == filters['category'])
                
                if filters.get('priority'):
                    query = query.filter(Feedback.priority == filters['priority'])
                
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            Feedback.title.ilike(search_term),
                            Feedback.description.ilike(search_term)
                        )
                    )
            
            # Ordenação
            order_by = filters.get('order_by', 'created_at') if filters else 'created_at'
            order_dir = filters.get('order_dir', 'desc') if filters else 'desc'
            
            if hasattr(Feedback, order_by):
                if order_dir == 'asc':
                    query = query.order_by(getattr(Feedback, order_by).asc())
                else:
                    query = query.order_by(getattr(Feedback, order_by).desc())
            
            # Paginação
            total = query.count()
            feedbacks = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'feedbacks': [f.to_dict() for f in feedbacks],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar feedbacks: {e}")
            raise
    
    def update_feedback_status(self, db: Session, feedback_id: int, admin_id: int,
                              status: str, response: str = None) -> Feedback:
        """Atualiza status do feedback"""
        try:
            feedback = self.get_feedback(db, feedback_id)
            if not feedback:
                raise ValueError("Feedback não encontrado")
            
            old_status = feedback.status
            feedback.status = status
            
            if status == 'resolved':
                feedback.resolve(admin_id, response)
            elif response:
                feedback.admin_response = response
            
            db.commit()
            db.refresh(feedback)
            
            # Notificar usuário via WebSocket
            emit_to_user(
                feedback.user_id,
                'feedback_updated',
                {
                    'feedback_id': feedback.id,
                    'status': status,
                    'response': response,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Feedback {feedback_id} atualizado: {old_status} -> {status}")
            return feedback
            
        except Exception as e:
            logger.error(f"Erro ao atualizar feedback: {e}")
            db.rollback()
            raise
    
    def get_feedback_statistics(self, db: Session) -> Dict:
        """Retorna estatísticas de feedbacks"""
        try:
            total = db.query(Feedback).filter(Feedback.is_active == True).count()
            
            by_status = {}
            for status in ['pending', 'reviewed', 'resolved', 'dismissed']:
                count = db.query(Feedback).filter(
                    and_(
                        Feedback.is_active == True,
                        Feedback.status == status
                    )
                ).count()
                by_status[status] = count
            
            by_type = {}
            types = db.query(Feedback.feedback_type).distinct().all()
            for (f_type,) in types:
                count = db.query(Feedback).filter(
                    and_(
                        Feedback.is_active == True,
                        Feedback.feedback_type == f_type
                    )
                ).count()
                by_type[f_type] = count
            
            # Rating médio
            avg_rating = db.query(func.avg(Feedback.rating)).filter(
                and_(
                    Feedback.is_active == True,
                    Feedback.rating.isnot(None)
                )
            ).scalar() or 0
            
            return {
                'total': total,
                'by_status': by_status,
                'by_type': by_type,
                'average_rating': round(float(avg_rating), 2)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            raise
    
    def _notify_admins_new_feedback(self, feedback: Feedback):
        """Notifica administradores sobre novo feedback"""
        try:
            from ..models import db
            # Buscar todos os admins
            admins = db.session.query(User).filter(
                and_(
                    User.role == 'admin',
                    User.is_active == True
                )
            ).all()
            
            notification_data = {
                'type': 'new_feedback',
                'feedback': feedback.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Enviar para cada admin
            for admin in admins:
                emit_to_user(admin.id, 'notification', notification_data)
                
        except Exception as e:
            logger.error(f"Erro ao notificar admins: {e}")


# Instância global
feedback_service = FeedbackService()


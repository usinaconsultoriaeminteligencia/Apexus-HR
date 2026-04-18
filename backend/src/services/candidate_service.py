"""
Serviço de gerenciamento de candidatos
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from ..models import Candidate, User, Interview
from ..utils.lgpd_compliance import LGPDCompliance

logger = logging.getLogger(__name__)

class CandidateService:
    """Serviço para gerenciar candidatos"""
    
    def __init__(self):
        self.lgpd = LGPDCompliance()
    
    def create_candidate(self, db: Session, candidate_data: Dict, recruiter_id: int) -> Candidate:
        """Cria um novo candidato"""
        try:
            # Verificar se email já existe
            existing = db.query(Candidate).filter(
                Candidate.email == candidate_data['email'],
                Candidate.is_active == True
            ).first()
            
            if existing:
                raise ValueError("Candidato com este email já existe")
            
            # Criar candidato
            candidate = Candidate(
                full_name=candidate_data['full_name'],
                email=candidate_data['email'],
                phone=candidate_data.get('phone'),
                position_applied=candidate_data['position_applied'],
                experience_years=candidate_data.get('experience_years', 0),
                current_company=candidate_data.get('current_company'),
                current_position=candidate_data.get('current_position'),
                source=candidate_data.get('source', 'manual'),
                recruiter_id=recruiter_id,
                status='novo',
                consent_given=candidate_data.get('consent_given', False),
                consent_date=datetime.now(timezone.utc).replace(tzinfo=None) if candidate_data.get('consent_given') else None
            )
            
            # Definir habilidades
            if candidate_data.get('skills'):
                candidate.set_skills_list(candidate_data['skills'])
            
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            logger.info(f"Candidato criado: {candidate.id} - {candidate.full_name}")
            return candidate
            
        except Exception as e:
            logger.error(f"Erro ao criar candidato: {str(e)}")
            db.rollback()
            raise
    
    def get_candidate(self, db: Session, candidate_id: int, include_sensitive: bool = False) -> Optional[Candidate]:
        """Busca candidato por ID"""
        try:
            candidate = db.query(Candidate).filter(
                Candidate.id == candidate_id,
                Candidate.is_active == True
            ).first()
            
            if candidate and candidate.anonymized and not include_sensitive:
                # Retornar dados anonimizados
                return candidate
            
            return candidate
            
        except Exception as e:
            logger.error(f"Erro ao buscar candidato {candidate_id}: {str(e)}")
            raise
    
    def list_candidates(self, db: Session, filters: Dict = None, page: int = 1, 
                       per_page: int = 20) -> Dict:
        """Lista candidatos com filtros e paginação"""
        try:
            query = db.query(Candidate).filter(Candidate.is_active == True)
            
            # Aplicar filtros
            if filters:
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            Candidate.full_name.ilike(search_term),
                            Candidate.email.ilike(search_term),
                            Candidate.position_applied.ilike(search_term)
                        )
                    )
                
                if filters.get('status'):
                    query = query.filter(Candidate.status == filters['status'])
                
                if filters.get('position'):
                    query = query.filter(Candidate.position_applied == filters['position'])
                
                if filters.get('recruiter_id'):
                    query = query.filter(Candidate.recruiter_id == filters['recruiter_id'])
                
                if filters.get('score_min'):
                    query = query.filter(Candidate.overall_score >= filters['score_min'])
                
                if filters.get('score_max'):
                    query = query.filter(Candidate.overall_score <= filters['score_max'])
                
                if filters.get('date_from'):
                    query = query.filter(Candidate.created_at >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(Candidate.created_at <= filters['date_to'])
            
            # Ordenação
            order_by = filters.get('order_by', 'created_at') if filters else 'created_at'
            order_dir = filters.get('order_dir', 'desc') if filters else 'desc'
            
            if hasattr(Candidate, order_by):
                if order_dir == 'asc':
                    query = query.order_by(getattr(Candidate, order_by).asc())
                else:
                    query = query.order_by(getattr(Candidate, order_by).desc())
            
            # Paginação
            total = query.count()
            candidates = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'candidates': [c.to_dict() for c in candidates],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar candidatos: {str(e)}")
            raise
    
    def update_candidate(self, db: Session, candidate_id: int, update_data: Dict) -> Candidate:
        """Atualiza dados do candidato"""
        try:
            candidate = db.query(Candidate).filter(
                Candidate.id == candidate_id,
                Candidate.is_active == True
            ).first()
            
            if not candidate:
                raise ValueError("Candidato não encontrado")
            
            if candidate.anonymized:
                raise ValueError("Não é possível atualizar candidato anonimizado")
            
            # Campos permitidos para atualização
            allowed_fields = [
                'full_name', 'email', 'phone', 'position_applied', 
                'experience_years', 'current_company', 'current_position',
                'status', 'interview_notes'
            ]
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(candidate, field):
                    setattr(candidate, field, value)
            
            # Atualizar habilidades se fornecidas
            if 'skills' in update_data:
                candidate.set_skills_list(update_data['skills'])
            
            candidate.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            db.commit()
            db.refresh(candidate)
            
            logger.info(f"Candidato atualizado: {candidate.id}")
            return candidate
            
        except Exception as e:
            logger.error(f"Erro ao atualizar candidato {candidate_id}: {str(e)}")
            db.rollback()
            raise
    
    def delete_candidate(self, db: Session, candidate_id: int, soft_delete: bool = True) -> bool:
        """Remove candidato (exclusão lógica ou física)"""
        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            
            if not candidate:
                raise ValueError("Candidato não encontrado")
            
            if soft_delete:
                # Exclusão lógica
                candidate.soft_delete()
                logger.info(f"Candidato removido (soft delete): {candidate.id}")
            else:
                # Exclusão física (apenas para conformidade LGPD)
                db.delete(candidate)
                logger.info(f"Candidato removido (hard delete): {candidate.id}")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover candidato {candidate_id}: {str(e)}")
            db.rollback()
            raise
    
    def anonymize_candidate(self, db: Session, candidate_id: int) -> bool:
        """Anonimiza dados do candidato (LGPD)"""
        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            
            if not candidate:
                raise ValueError("Candidato não encontrado")
            
            if candidate.anonymized:
                return True  # Já anonimizado
            
            # Anonimizar dados
            candidate.anonymize()
            
            db.commit()
            
            logger.info(f"Candidato anonimizado: {candidate.id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao anonimizar candidato {candidate_id}: {str(e)}")
            db.rollback()
            raise
    
    def export_candidate_data(self, db: Session, candidate_id: int) -> Dict:
        """Exporta dados do candidato (direito à portabilidade - LGPD)"""
        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            
            if not candidate:
                raise ValueError("Candidato não encontrado")
            
            if candidate.anonymized:
                raise ValueError("Dados do candidato foram anonimizados")
            
            # Buscar entrevistas relacionadas
            interviews = db.query(Interview).filter(Interview.candidate_id == candidate_id).all()
            
            export_data = {
                'candidate_data': candidate.to_dict(include_sensitive=True),
                'interviews': [interview.to_dict(include_detailed=True) for interview in interviews],
                'export_date': datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                'data_retention_info': {
                    'retention_date': candidate.get_retention_date().isoformat(),
                    'can_request_deletion': True
                }
            }
            
            logger.info(f"Dados exportados para candidato: {candidate.id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados do candidato {candidate_id}: {str(e)}")
            raise
    
    def get_candidate_statistics(self, db: Session, recruiter_id: Optional[int] = None) -> Dict:
        """Retorna estatísticas de candidatos"""
        try:
            base_query = db.query(Candidate).filter(Candidate.is_active == True)
            
            if recruiter_id:
                base_query = base_query.filter(Candidate.recruiter_id == recruiter_id)
            
            # Estatísticas básicas
            total_candidates = base_query.count()
            
            # Por status
            status_stats = {}
            statuses = ['novo', 'triagem', 'entrevista', 'entrevista_realizada', 'aprovado', 'rejeitado', 'contratado']
            for status in statuses:
                count = base_query.filter(Candidate.status == status).count()
                status_stats[status] = count
            
            # Por posição
            position_stats = {}
            positions = db.query(Candidate.position_applied).filter(
                Candidate.is_active == True
            ).distinct().all()
            
            for (position,) in positions:
                count = base_query.filter(Candidate.position_applied == position).count()
                position_stats[position] = count
            
            # Scores médios
            avg_scores = db.query(
                db.func.avg(Candidate.overall_score).label('overall'),
                db.func.avg(Candidate.technical_score).label('technical'),
                db.func.avg(Candidate.behavioral_score).label('behavioral')
            ).filter(
                Candidate.is_active == True,
                Candidate.overall_score > 0
            )
            
            if recruiter_id:
                avg_scores = avg_scores.filter(Candidate.recruiter_id == recruiter_id)
            
            scores = avg_scores.first()
            
            # Candidatos por mês (últimos 6 meses)
            monthly_stats = []
            for i in range(6):
                start_date = datetime.now(timezone.utc).replace(tzinfo=None).replace(day=1) - timedelta(days=30*i)
                end_date = start_date + timedelta(days=31)
                
                count = base_query.filter(
                    and_(
                        Candidate.created_at >= start_date,
                        Candidate.created_at < end_date
                    )
                ).count()
                
                monthly_stats.append({
                    'month': start_date.strftime('%Y-%m'),
                    'count': count
                })
            
            return {
                'total_candidates': total_candidates,
                'status_distribution': status_stats,
                'position_distribution': position_stats,
                'average_scores': {
                    'overall': round(scores.overall or 0, 1),
                    'technical': round(scores.technical or 0, 1),
                    'behavioral': round(scores.behavioral or 0, 1)
                },
                'monthly_trends': list(reversed(monthly_stats))
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {str(e)}")
            raise
    
    def schedule_anonymization_check(self, db: Session) -> int:
        """Verifica candidatos que devem ser anonimizados"""
        try:
            candidates = db.query(Candidate).filter(
                Candidate.is_active == True,
                Candidate.anonymized == False
            ).all()
            
            anonymized_count = 0
            
            for candidate in candidates:
                if candidate.should_be_anonymized():
                    candidate.anonymize()
                    anonymized_count += 1
            
            if anonymized_count > 0:
                db.commit()
                logger.info(f"Anonimizados {anonymized_count} candidatos automaticamente")
            
            return anonymized_count
            
        except Exception as e:
            logger.error(f"Erro na verificação de anonimização: {str(e)}")
            db.rollback()
            raise


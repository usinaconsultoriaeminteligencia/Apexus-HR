"""
Rotas de relatórios do sistema
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import func, distinct, and_, or_
from datetime import datetime, timedelta
from src.models import db
from src.models.candidate import Candidate
from src.models.interview import Interview
from src.models.user import User
from src.utils.type_helpers import as_float, safe_bool, as_int, dt_iso
from functools import wraps
from flask import jsonify, request
import jwt
import os
from datetime import datetime
from src.models.user import User
from src.models import db

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
JWT_ALG = "HS256"

# Remover o decorador duplicado - usar apenas o middleware principal

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/candidates', methods=['GET'])
# JWT handled by middleware
def get_candidate_reports():
    """
    Retorna relatórios detalhados sobre candidatos
    """
    try:
        # Parâmetros de filtro
        period = request.args.get('period', 'all')  # today, week, month, year, all
        status = request.args.get('status', 'all')
        
        # Base query
        query = db.session.query(Candidate)
        
        # Aplicar filtro de período
        if period != 'all':
            now = datetime.utcnow()
            if period == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'week':
                start_date = now - timedelta(days=7)
            elif period == 'month':
                start_date = now - timedelta(days=30)
            elif period == 'year':
                start_date = now - timedelta(days=365)
            else:
                start_date = None
                
            if start_date:
                query = query.filter(Candidate.created_at >= start_date)
        
        # Aplicar filtro de status
        if status != 'all':
            query = query.filter(Candidate.status == status)
        
        candidates = query.all()
        
        # Estatísticas por status
        status_stats = db.session.query(
            Candidate.status,
            func.count(Candidate.id).label('count')
        ).group_by(Candidate.status).all()
        
        # Taxa de aprovação
        total_candidates = len(candidates)
        approved = len([c for c in candidates if c.status == 'aprovado'])
        rejected = len([c for c in candidates if c.status == 'rejeitado'])
        approval_rate = (approved / total_candidates * 100) if total_candidates > 0 else 0
        rejection_rate = (rejected / total_candidates * 100) if total_candidates > 0 else 0
        
        # Tempo médio do processo
        completed_candidates = [c for c in candidates if c.interview_completed]
        if completed_candidates:
            avg_process_time = sum([
                (c.interview_completed - c.created_at).days 
                for c in completed_candidates
            ]) / len(completed_candidates)
        else:
            avg_process_time = 0
        
        # Candidatos por posição
        position_stats = db.session.query(
            Candidate.position_applied,
            func.count(Candidate.id).label('count')
        ).group_by(Candidate.position_applied).all()
        
        # Score médio por status
        score_by_status = []
        for status_name, _ in status_stats:
            status_candidates = [c for c in candidates if c.status == status_name]
            if status_candidates:
                avg_score = sum([c.overall_score or 0 for c in status_candidates]) / len(status_candidates)
                score_by_status.append({
                    'status': status_name,
                    'avg_score': round(avg_score, 2),
                    'count': len(status_candidates)
                })
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_candidates': total_candidates,
                    'approved': approved,
                    'rejected': rejected,
                    'in_process': total_candidates - approved - rejected,
                    'approval_rate': round(approval_rate, 1),
                    'rejection_rate': round(rejection_rate, 1),
                    'avg_process_days': round(avg_process_time, 1)
                },
                'status_distribution': [
                    {'status': s[0], 'count': s[1]} for s in status_stats
                ],
                'position_distribution': [
                    {'position': p[0], 'count': p[1]} for p in position_stats
                ],
                'score_by_status': score_by_status,
                'candidates': [c.to_dict() for c in candidates[:100]],  # Limitar a 100 para performance
                'period': period,
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/api/reports/interviews', methods=['GET'])
# JWT handled by middleware
def get_interview_reports():
    """
    Retorna relatórios detalhados sobre entrevistas
    """
    try:
        # Parâmetros de filtro
        period = request.args.get('period', 'all')
        status = request.args.get('status', 'all')
        
        # Base query
        query = db.session.query(Interview).join(Candidate).join(User, Interview.interviewer_id == User.id)
        
        # Aplicar filtro de período
        if period != 'all':
            now = datetime.utcnow()
            if period == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'week':
                start_date = now - timedelta(days=7)
            elif period == 'month':
                start_date = now - timedelta(days=30)
            elif period == 'year':
                start_date = now - timedelta(days=365)
            else:
                start_date = None
                
            if start_date:
                query = query.filter(Interview.created_at >= start_date)
        
        # Aplicar filtro de status
        if status != 'all':
            query = query.filter(Interview.status == status)  # type: ignore
        
        interviews = query.all()
        
        # Estatísticas gerais
        total_interviews = len(interviews)
        completed = len([i for i in interviews if i.status == 'concluida'])  # type: ignore
        scheduled = len([i for i in interviews if i.status == 'agendada'])  # type: ignore
        cancelled = len([i for i in interviews if i.status == 'cancelada'])  # type: ignore
        
        # Taxa de conclusão
        completion_rate = (completed / total_interviews * 100) if total_interviews > 0 else 0
        
        # Duração média
        completed_interviews = [i for i in interviews if safe_bool(i.duration_minutes) and as_int(i.duration_minutes) > 0]
        avg_duration = sum([as_int(i.duration_minutes) for i in completed_interviews]) / len(completed_interviews) if completed_interviews else 0
        
        # Entrevistas por dia da semana
        weekday_stats = {}
        for interview in interviews:
            if safe_bool(interview.scheduled_at):
                weekday = interview.scheduled_at.strftime('%A')
                weekday_stats[weekday] = weekday_stats.get(weekday, 0) + 1
        
        # Entrevistas por hora do dia
        hour_stats = {}
        for interview in interviews:
            if safe_bool(interview.scheduled_at):
                hour = interview.scheduled_at.hour
                hour_stats[hour] = hour_stats.get(hour, 0) + 1
        
        # Performance por entrevistador
        interviewer_stats = db.session.query(
            User.full_name,
            func.count(Interview.id).label('total'),
            func.avg(Interview.overall_score).label('avg_score')
        ).join(Interview, User.id == Interview.interviewer_id)\
         .group_by(User.id, User.full_name).all()
        
        # Scores médios
        scores = {
            'overall': sum([as_float(i.overall_score) for i in interviews]) / len(interviews) if interviews else 0,
            'confidence': sum([as_float(i.confidence_score) for i in interviews]) / len(interviews) if interviews else 0,
            'enthusiasm': sum([as_float(i.enthusiasm_score) for i in interviews]) / len(interviews) if interviews else 0,
            'clarity': sum([as_float(i.clarity_score) for i in interviews]) / len(interviews) if interviews else 0,
            'technical': sum([as_float(i.technical_accuracy) for i in interviews]) / len(interviews) if interviews else 0,
            'communication': sum([as_float(i.communication_skills) for i in interviews]) / len(interviews) if interviews else 0
        }
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_interviews': total_interviews,
                    'completed': completed,
                    'scheduled': scheduled,
                    'cancelled': cancelled,
                    'completion_rate': round(completion_rate, 1),
                    'avg_duration_minutes': round(avg_duration, 1)
                },
                'weekday_distribution': [
                    {'day': day, 'count': count} 
                    for day, count in weekday_stats.items()
                ],
                'hourly_distribution': [
                    {'hour': hour, 'count': count} 
                    for hour, count in sorted(hour_stats.items())
                ],
                'interviewer_performance': [
                    {
                        'name': stat[0],
                        'total_interviews': stat[1],
                        'avg_score': round(as_float(stat[2]), 2)
                    }
                    for stat in interviewer_stats
                ],
                'average_scores': {k: round(v, 2) for k, v in scores.items()},
                'interviews': [
                    {
                        'id': i.id,
                        'candidate_name': i.candidate.full_name if i.candidate else 'N/A',
                        'position': i.position,
                        'status': i.status,
                        'scheduled_at': dt_iso(i.scheduled_at),
                        'duration': as_int(i.duration_minutes),
                        'overall_score': round(as_float(i.overall_score), 2),
                        'recommendation': i.recommendation
                    }
                    for i in interviews[:100]  # Limitar a 100 para performance
                ],
                'period': period,
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/api/reports/export/<report_type>', methods=['GET'])
# JWT handled by middleware
def export_report(report_type):
    """
    Exporta relatório em formato JSON (pode ser estendido para CSV/PDF)
    """
    try:
        if report_type == 'candidates':
            response = get_candidate_reports()
            return response
        elif report_type == 'interviews':
            response = get_interview_reports()
            return response
        else:
            return jsonify({'success': False, 'error': 'Invalid report type'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
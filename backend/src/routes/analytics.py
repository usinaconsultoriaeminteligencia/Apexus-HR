"""
Rotas de analytics do sistema
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract, and_, or_, case, text, literal
from datetime import datetime, timedelta
from src.models import db
from src.models.candidate import Candidate
from src.models.interview import Interview
from src.models.user import User
from src.utils.type_helpers import as_float, safe_bool, as_int
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

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/kpis', methods=['GET'])
# JWT handled by middleware
def get_kpis():
    """
    Retorna KPIs principais do sistema
    """
    try:
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # KPI 1: Total de candidatos
        total_candidates = db.session.query(func.count(Candidate.id)).scalar()
        new_candidates_month = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.created_at >= thirty_days_ago).scalar()
        new_candidates_week = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.created_at >= seven_days_ago).scalar()
        
        # KPI 2: Taxa de conclusão de entrevistas
        total_interviews = db.session.query(func.count(Interview.id)).scalar()
        # Criar query e aplicar filtros separadamente para evitar problemas de tipo
        completed_interviews = db.session.query(func.count(Interview.id))\
            .filter(text("status = 'concluida'")).scalar() or 0
        # Converter para int para evitar problemas de tipo
        total_interviews = as_int(total_interviews)
        completed_interviews = as_int(completed_interviews)
        completion_rate = (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0
        
        # KPI 3: Tempo médio até contratação
        hired_candidates = db.session.query(Candidate)\
            .filter(Candidate.status == 'contratado').all()
        
        if hired_candidates:
            hiring_times = []
            for candidate in hired_candidates:
                if candidate.interview_completed and candidate.created_at:
                    days = (candidate.interview_completed - candidate.created_at).days
                    hiring_times.append(days)
            avg_hiring_time = sum(hiring_times) / len(hiring_times) if hiring_times else 0
        else:
            avg_hiring_time = 0
        
        # KPI 4: Taxa de aprovação
        total_evaluated = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status.in_(['aprovado', 'rejeitado', 'contratado'])).scalar()
        approved = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status.in_(['aprovado', 'contratado'])).scalar()
        approval_rate = (approved / total_evaluated * 100) if total_evaluated > 0 else 0
        
        # KPI 5: Score médio dos candidatos
        # Criar query e aplicar filtros separadamente 
        avg_score = db.session.query(func.avg(Candidate.overall_score))\
            .filter(text("overall_score > 0")).scalar() or 0.0
        
        # KPI 6: Candidatos em pipeline
        in_pipeline = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status.in_(['novo', 'triagem', 'entrevista', 'entrevista_realizada'])).scalar()
        
        # KPI 7: Entrevistas agendadas
        # Criar query e aplicar filtros com text para evitar problemas de tipo
        scheduled_interviews = db.session.query(func.count(Interview.id))\
            .filter(text(f"status = 'agendada' AND scheduled_at >= '{now.isoformat()}'")).scalar() or 0
        scheduled_interviews = as_int(scheduled_interviews)
        
        # KPI 8: Taxa de desistência
        total_started = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status != 'novo').scalar()
        dropouts = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status == 'desistiu').scalar()
        dropout_rate = (dropouts / total_started * 100) if total_started > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'candidates': {
                    'total': total_candidates,
                    'new_this_month': new_candidates_month,
                    'new_this_week': new_candidates_week,
                    'in_pipeline': in_pipeline,
                    'growth_rate': round((new_candidates_week / 7) if new_candidates_week else 0, 1)
                },
                'interviews': {
                    'total': total_interviews,
                    'completed': completed_interviews,
                    'scheduled': scheduled_interviews,
                    'completion_rate': round(completion_rate, 1)
                },
                'performance': {
                    'approval_rate': round(approval_rate, 1),
                    'avg_score': round(as_float(avg_score), 2),
                    'avg_hiring_days': round(avg_hiring_time, 1),
                    'dropout_rate': round(dropout_rate, 1)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/analytics/trends', methods=['GET'])
# JWT handled by middleware
def get_trends():
    """
    Retorna dados de tendências para gráficos
    """
    try:
        period = request.args.get('period', '30')  # dias
        period_days = int(period)
        
        now = datetime.utcnow()
        start_date = now - timedelta(days=period_days)
        
        # Tendência de candidatos por dia
        candidates_trend = db.session.query(
            func.date(Candidate.created_at).label('date'),
            func.count(Candidate.id).label('count')
        ).filter(Candidate.created_at >= start_date)\
         .group_by(func.date(Candidate.created_at))\
         .order_by(func.date(Candidate.created_at)).all()
        
        # Tendência de entrevistas por dia
        interviews_trend = db.session.query(
            func.date(Interview.created_at).label('date'),
            func.count(Interview.id).label('count')
        ).filter(Interview.created_at >= start_date)\
         .group_by(func.date(Interview.created_at))\
         .order_by(func.date(Interview.created_at)).all()
        
        # Funil de conversão
        total_candidates = db.session.query(func.count(Candidate.id)).scalar()
        in_screening = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status == 'triagem').scalar()
        interviewed = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status.in_(['entrevista', 'entrevista_realizada'])).scalar()
        approved = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status == 'aprovado').scalar()
        hired = db.session.query(func.count(Candidate.id))\
            .filter(Candidate.status == 'contratado').scalar()
        
        conversion_funnel = [
            {'stage': 'Aplicaram', 'count': total_candidates, 'percentage': 100},
            {'stage': 'Triagem', 'count': in_screening, 'percentage': (in_screening/total_candidates*100) if total_candidates > 0 else 0},
            {'stage': 'Entrevistados', 'count': interviewed, 'percentage': (interviewed/total_candidates*100) if total_candidates > 0 else 0},
            {'stage': 'Aprovados', 'count': approved, 'percentage': (approved/total_candidates*100) if total_candidates > 0 else 0},
            {'stage': 'Contratados', 'count': hired, 'percentage': (hired/total_candidates*100) if total_candidates > 0 else 0}
        ]
        
        # Distribuição de scores
        # Usar CASE SQL diretamente para evitar problemas de tipo
        score_distribution = db.session.query(
            text("""
                CASE 
                    WHEN overall_score < 3 THEN '0-3'
                    WHEN overall_score < 5 THEN '3-5'
                    WHEN overall_score < 7 THEN '5-7'
                    WHEN overall_score < 9 THEN '7-9'
                    ELSE '9-10'
                END AS range
            """),
            func.count(Candidate.id).label('count')
        ).select_from(Candidate)\
         .filter(text("overall_score > 0"))\
         .group_by(text('range')).all()
        
        # Heatmap de horários de entrevista
        interview_heatmap = db.session.query(
            extract('dow', Interview.scheduled_at).label('weekday'),
            extract('hour', Interview.scheduled_at).label('hour'),
            func.count(Interview.id).label('count')
        ).filter(Interview.scheduled_at.isnot(None))\
         .group_by('weekday', 'hour').all()
        
        # Performance dos recrutadores
        # Usar dict para case quando
        recruiter_performance = db.session.query(
            User.full_name,
            func.count(Candidate.id).label('total_candidates'),
            func.avg(Candidate.overall_score).label('avg_score'),
            func.sum(case(
                {(Candidate.status == 'contratado'): 1},
                else_=0
            )).label('hired')
        ).join(Candidate, User.id == Candidate.recruiter_id)\
         .group_by(User.id, User.full_name).all()
        
        # Candidatos por fonte
        source_distribution = db.session.query(
            Candidate.source,
            func.count(Candidate.id).label('count')
        ).filter(Candidate.source.isnot(None))\
         .group_by(Candidate.source).all()
        
        # Candidatos por posição
        position_distribution = db.session.query(
            Candidate.position_applied,
            func.count(Candidate.id).label('count')
        ).group_by(Candidate.position_applied)\
         .order_by(func.count(Candidate.id).desc())\
         .limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'candidates_trend': [
                    {'date': str(item[0]), 'count': item[1]} 
                    for item in candidates_trend
                ],
                'interviews_trend': [
                    {'date': str(item[0]), 'count': item[1]} 
                    for item in interviews_trend
                ],
                'conversion_funnel': conversion_funnel,
                'score_distribution': [
                    {'range': item[0], 'count': item[1]} 
                    for item in score_distribution
                ],
                'interview_heatmap': [
                    {
                        'weekday': int(item[0]) if item[0] is not None else 0,
                        'hour': int(item[1]) if item[1] is not None else 0,
                        'count': item[2]
                    }
                    for item in interview_heatmap
                ],
                'recruiter_performance': [
                    {
                        'name': item[0],
                        'total_candidates': item[1],
                        'avg_score': round(as_float(item[2]), 2),
                        'hired': item[3] or 0
                    }
                    for item in recruiter_performance
                ],
                'source_distribution': [
                    {'source': item[0] or 'Não especificado', 'count': item[1]}
                    for item in source_distribution
                ],
                'position_distribution': [
                    {'position': item[0], 'count': item[1]}
                    for item in position_distribution
                ],
                'period_days': period_days,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/api/analytics/compare', methods=['GET'])
# JWT handled by middleware
def compare_periods():
    """
    Compara métricas entre dois períodos
    """
    try:
        period1_start = request.args.get('period1_start')
        period1_end = request.args.get('period1_end')
        period2_start = request.args.get('period2_start')
        period2_end = request.args.get('period2_end')
        
        if not all([period1_start, period1_end, period2_start, period2_end]):
            return jsonify({'success': False, 'error': 'Missing period parameters'}), 400
        
        # Converter strings para datas
        p1_start = datetime.fromisoformat(period1_start) if period1_start else None
        p1_end = datetime.fromisoformat(period1_end) if period1_end else None
        p2_start = datetime.fromisoformat(period2_start) if period2_start else None
        p2_end = datetime.fromisoformat(period2_end) if period2_end else None
        
        # Métricas do período 1
        p1_candidates = db.session.query(func.count(Candidate.id))\
            .filter(and_(Candidate.created_at >= p1_start, Candidate.created_at <= p1_end)).scalar()
        p1_interviews = db.session.query(func.count(Interview.id))\
            .filter(and_(Interview.created_at >= p1_start, Interview.created_at <= p1_end)).scalar()
        p1_hired = db.session.query(func.count(Candidate.id))\
            .filter(and_(Candidate.created_at >= p1_start, Candidate.created_at <= p1_end, 
                        Candidate.status == 'contratado')).scalar()
        
        # Métricas do período 2
        p2_candidates = db.session.query(func.count(Candidate.id))\
            .filter(and_(Candidate.created_at >= p2_start, Candidate.created_at <= p2_end)).scalar()
        p2_interviews = db.session.query(func.count(Interview.id))\
            .filter(and_(Interview.created_at >= p2_start, Interview.created_at <= p2_end)).scalar()
        p2_hired = db.session.query(func.count(Candidate.id))\
            .filter(and_(Candidate.created_at >= p2_start, Candidate.created_at <= p2_end, 
                        Candidate.status == 'contratado')).scalar()
        
        # Calcular variações
        candidates_change = ((p2_candidates - p1_candidates) / p1_candidates * 100) if p1_candidates > 0 else 0
        interviews_change = ((p2_interviews - p1_interviews) / p1_interviews * 100) if p1_interviews > 0 else 0
        hired_change = ((p2_hired - p1_hired) / p1_hired * 100) if p1_hired > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'period1': {
                    'start': period1_start,
                    'end': period1_end,
                    'candidates': p1_candidates,
                    'interviews': p1_interviews,
                    'hired': p1_hired
                },
                'period2': {
                    'start': period2_start,
                    'end': period2_end,
                    'candidates': p2_candidates,
                    'interviews': p2_interviews,
                    'hired': p2_hired
                },
                'changes': {
                    'candidates': round(candidates_change, 1),
                    'interviews': round(interviews_change, 1),
                    'hired': round(hired_change, 1)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
"""
Rotas de agendamento de entrevistas
"""
from flask import Blueprint, request, jsonify
from src.models import db
from src.services.appointment_service import appointment_service
from src.routes.auth import require_auth
from src.utils.error_handler import NotFoundError, ValidationError as AppValidationError
from src.utils.retry import retry_db_operation_improved
from src.utils.cache import cache_manager, invalidate_cache
from datetime import datetime

bp = Blueprint("appointments", __name__, url_prefix="/api/appointments")


@bp.post("")
@require_auth
@retry_db_operation_improved()
@invalidate_cache("cache:appointments:*")
def create_appointment(current_user):
    """Cria novo agendamento"""
    try:
        data = request.get_json() or {}
        
        # Validação básica
        if not data.get('candidate_id'):
            raise AppValidationError("ID do candidato é obrigatório")
        
        if not data.get('scheduled_at'):
            raise AppValidationError("Data e horário são obrigatórios")
        
        # Converter string de data para datetime
        try:
            scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
        except:
            raise AppValidationError("Formato de data inválido (use ISO 8601)")
        
        appointment = appointment_service.create_appointment(
            db.session,
            current_user.id,
            {
                **data,
                'scheduled_at': scheduled_at
            }
        )
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict(include_sensitive=True)
        }), 201
        
    except AppValidationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


@bp.get("")
@require_auth
@retry_db_operation_improved()
def list_appointments(current_user):
    """Lista agendamentos"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        filters = {}
        
        # Filtros baseados no role
        if current_user.role == 'candidate':
            filters['candidate_id'] = current_user.id
        elif current_user.role not in ['admin', 'recruiter', 'manager']:
            filters['interviewer_id'] = current_user.id
        
        # Filtros adicionais
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('upcoming_only') == 'true':
            filters['upcoming_only'] = True
        
        result = appointment_service.list_appointments(
            db.session,
            filters=filters,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        raise


@bp.get("/<int:appointment_id>")
@require_auth
@retry_db_operation_improved()
def get_appointment(current_user, appointment_id):
    """Obtém agendamento por ID"""
    try:
        appointment = appointment_service.get_appointment(db.session, appointment_id)
        
        if not appointment:
            raise NotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar permissão
        has_access = (
            current_user.role == 'admin' or
            appointment.candidate_id == current_user.id or
            appointment.interviewer_id == current_user.id
        )
        
        if not has_access:
            raise NotFoundError("Agendamento não encontrado")
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict(include_sensitive=True)
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        raise


@bp.get("/token/<token>")
def get_appointment_by_token(token):
    """Obtém agendamento por token público (sem autenticação)"""
    try:
        appointment = appointment_service.get_appointment_by_token(db.session, token)
        
        if not appointment:
            raise NotFoundError("Agendamento não encontrado")
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict()
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        raise


@bp.post("/<int:appointment_id>/confirm")
@require_auth
@retry_db_operation_improved()
@invalidate_cache("cache:appointments:*")
def confirm_appointment(current_user, appointment_id):
    """Confirma agendamento"""
    try:
        appointment = appointment_service.get_appointment(db.session, appointment_id)
        
        if not appointment:
            raise NotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar permissão (candidato ou entrevistador)
        if appointment.candidate_id != current_user.id and appointment.interviewer_id != current_user.id:
            if current_user.role != 'admin':
                return jsonify({'error': 'Acesso negado'}), 403
        
        appointment = appointment_service.confirm_appointment(db.session, appointment_id)
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict(include_sensitive=True)
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


@bp.post("/<int:appointment_id>/decline")
@require_auth
@retry_db_operation_improved()
@invalidate_cache("cache:appointments:*")
def decline_appointment(current_user, appointment_id):
    """Recusa agendamento"""
    try:
        appointment = appointment_service.get_appointment(db.session, appointment_id)
        
        if not appointment:
            raise NotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar permissão (candidato pode recusar)
        if appointment.candidate_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason')
        
        appointment = appointment_service.decline_appointment(
            db.session,
            appointment_id,
            reason
        )
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict(include_sensitive=True)
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


@bp.post("/<int:appointment_id>/cancel")
@require_auth
@retry_db_operation_improved()
@invalidate_cache("cache:appointments:*")
def cancel_appointment(current_user, appointment_id):
    """Cancela agendamento"""
    try:
        appointment = appointment_service.get_appointment(db.session, appointment_id)
        
        if not appointment:
            raise NotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar permissão (entrevistador ou admin)
        if appointment.interviewer_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason')
        
        appointment = appointment_service.cancel_appointment(
            db.session,
            appointment_id,
            current_user.id,
            reason
        )
        
        return jsonify({
            'success': True,
            'appointment': appointment.to_dict(include_sensitive=True)
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


@bp.get("/upcoming")
@require_auth
@retry_db_operation_improved()
def get_upcoming_appointments(current_user):
    """Retorna agendamentos próximos"""
    try:
        days_ahead = int(request.args.get('days', 7))
        
        appointments = appointment_service.get_upcoming_appointments(
            db.session,
            user_id=current_user.id,
            days_ahead=days_ahead
        )
        
        return jsonify({
            'success': True,
            'appointments': [a.to_dict() for a in appointments]
        })
        
    except Exception as e:
        raise


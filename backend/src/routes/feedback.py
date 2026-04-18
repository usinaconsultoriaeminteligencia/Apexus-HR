"""
Rotas de feedback/avaliação do sistema
"""
from flask import Blueprint, request, jsonify
from src.models import db
from src.services.feedback_service import feedback_service
from src.routes.auth import require_auth
from src.utils.error_handler import NotFoundError, ValidationError as AppValidationError
from src.utils.validators import ValidationError
from src.utils.retry import retry_db_operation_improved
from src.utils.cache import cache_manager, invalidate_cache

bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@bp.post("")
@require_auth
@retry_db_operation_improved()
def create_feedback(current_user):
    """Cria novo feedback"""
    try:
        data = request.get_json() or {}
        
        # Validação básica
        if not data.get('title') or not data.get('description'):
            raise AppValidationError("Título e descrição são obrigatórios")
        
        feedback = feedback_service.create_feedback(
            db.session,
            current_user.id,
            {
                **data,
                'user_agent': request.headers.get('User-Agent'),
                'page_url': data.get('page_url', request.referrer)
            }
        )
        
        return jsonify({
            'success': True,
            'feedback': feedback.to_dict()
        }), 201
        
    except AppValidationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


@bp.get("")
@require_auth
@retry_db_operation_improved()
def list_feedbacks(current_user):
    """Lista feedbacks"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        filters = {
            'user_id': current_user.id if current_user.role != 'admin' else None,
            'feedback_type': request.args.get('type'),
            'status': request.args.get('status'),
            'category': request.args.get('category'),
            'search': request.args.get('search')
        }
        
        # Remover filtros None
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = feedback_service.list_feedbacks(
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


@bp.get("/<int:feedback_id>")
@require_auth
@retry_db_operation_improved()
def get_feedback(current_user, feedback_id):
    """Obtém feedback por ID"""
    try:
        feedback = feedback_service.get_feedback(db.session, feedback_id)
        
        if not feedback:
            raise NotFoundError(f"Feedback {feedback_id} não encontrado")
        
        # Verificar permissão (usuário só vê seus próprios feedbacks, exceto admin)
        if current_user.role != 'admin' and feedback.user_id != current_user.id:
            raise NotFoundError("Feedback não encontrado")
        
        return jsonify({
            'success': True,
            'feedback': feedback.to_dict(include_sensitive=current_user.role == 'admin')
        })
        
    except NotFoundError:
        raise
    except Exception as e:
        raise


@bp.patch("/<int:feedback_id>/status")
@require_auth
@retry_db_operation_improved()
def update_feedback_status(current_user, feedback_id):
    """Atualiza status do feedback (apenas admin)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        data = request.get_json() or {}
        status = data.get('status')
        response = data.get('response')
        
        if not status:
            raise AppValidationError("Status é obrigatório")
        
        feedback = feedback_service.update_feedback_status(
            db.session,
            feedback_id,
            current_user.id,
            status,
            response
        )
        
        return jsonify({
            'success': True,
            'feedback': feedback.to_dict(include_sensitive=True)
        })
        
    except AppValidationError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


@bp.get("/statistics")
@require_auth
@retry_db_operation_improved()
def get_feedback_statistics(current_user):
    """Retorna estatísticas de feedbacks (apenas admin)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        stats = feedback_service.get_feedback_statistics(db.session)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        raise


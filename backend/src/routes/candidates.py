from flask import Blueprint, request, jsonify
from src.models import db
from src.models.candidate import Candidate
from src.utils.retry import retry_db_operation_improved
from src.utils.validators import CandidateValidator, ValidationError as ValidatorError
from src.utils.error_handler import NotFoundError, ConflictError, ValidationError as AppValidationError
from src.utils.cache import cache_manager, invalidate_cache
from src.routes.auth import require_auth

bp = Blueprint("candidates", __name__, url_prefix="/api/candidates")

@bp.get("/ping")
def ping_candidates():
    return jsonify({"message": "candidates blueprint ativo"})


def _candidate_from_json(data):
    c = Candidate(
        full_name=data["full_name"],
        email=data["email"],
        position_applied=data.get("position_applied", ""),
        experience_years=data.get("experience_years", 0),
        current_company=data.get("current_company"),
        current_position=data.get("current_position"),
        source=data.get("source"),
        technical_score=data.get("technical_score", 0.0),
        behavioral_score=data.get("behavioral_score", 0.0),
        cultural_fit_score=data.get("cultural_fit_score", 0.0),
        ai_recommendation=data.get("ai_recommendation"),
        ai_confidence=data.get("ai_confidence", 0.0),
        linkedin_url=data.get("linkedin_url"),
        portfolio_url=data.get("portfolio_url"),
        phone=data.get("phone"),
        status=data.get("status", "novo"),
    )
    # skills: aceita lista ou string
    skills = data.get("skills")
    if isinstance(skills, list):
        c.set_skills_list(skills)
    elif isinstance(skills, str):
        c.skills = skills
    c.calculate_overall_score()
    return c

@bp.post("")
@require_auth
@retry_db_operation_improved(max_retries=3, initial_delay=1.0)
@invalidate_cache("cache:candidates:*")
def create_candidate(current_user):
    """Cria novo candidato com validação robusta"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        # Validar dados de entrada
        try:
            validated_data = CandidateValidator.validate_candidate_data(data, is_update=False)
        except ValidatorError as e:
            raise AppValidationError(str(e))
        
        # Verificar se email já existe
        existing = Candidate.query.filter_by(
            email=validated_data['email'],
            is_active=True
        ).first()
        
        if existing:
            raise ConflictError("Candidato com este email já existe", details={'email': validated_data['email']})
        
        # Criar candidato
        c = _candidate_from_json(validated_data)
        c.recruiter_id = current_user.id
        c.consent_given = data.get('consent_given', False)
        
        db.session.add(c)
        db.session.commit()
        
        # Invalidar cache de estatísticas
        cache_manager.delete_pattern("cache:candidates:*")
        
        return jsonify({
            'success': True,
            'candidate': c.to_dict(include_sensitive=True, role=getattr(current_user, 'role', None))
        }), 201
    
    except (AppValidationError, ConflictError):
        raise  # Re-raise exceções customizadas
    except Exception as e:
        db.session.rollback()
        raise

@bp.get("")
@require_auth
@retry_db_operation_improved(max_retries=3, initial_delay=1.0)
def list_candidates(current_user):
    """Lista candidatos com cache e paginação"""
    try:
        # Parâmetros de paginação e filtros
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 por página
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        
        # Chave de cache (inclui role para evitar vazar PII entre papéis)
        role = getattr(current_user, 'role', 'anon') or 'anon'
        cache_key = f"cache:candidates:list:{role}:{page}:{per_page}:{search}:{status}"
        
        # Tentar obter do cache
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            return jsonify(cached_result)
        
        # Query base
        q = Candidate.query.filter_by(is_active=True)
        
        # Filtros
        if search:
            q = q.filter(
                db.or_(
                    Candidate.full_name.ilike(f'%{search}%'),
                    Candidate.email.ilike(f'%{search}%'),
                    Candidate.position_applied.ilike(f'%{search}%')
                )
            )
        
        if status:
            q = q.filter(Candidate.status == status)
        
        # Contar total
        total = q.count()
        
        # Paginação
        candidates = q.order_by(Candidate.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        result = {
            'success': True,
            'candidates': [c.to_dict(role=role) for c in candidates],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
        
        # Armazenar no cache (TTL de 5 minutos)
        cache_manager.set(cache_key, result, ttl=300)
        
        return jsonify(result)
    
    except Exception as e:
        raise

@bp.get("/<int:candidate_id>")
@require_auth
@retry_db_operation_improved(max_retries=3, initial_delay=1.0)
def get_candidate(current_user, candidate_id):
    """Obtém candidato por ID com cache"""
    try:
        # Cache key inclui role para não vazar PII entre papéis
        role = getattr(current_user, 'role', 'anon') or 'anon'
        cache_key = f"cache:candidates:{role}:{candidate_id}"
        
        # Tentar obter do cache
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            return jsonify(cached_result)
        
        # Buscar do banco
        c = Candidate.query.filter_by(id=candidate_id, is_active=True).first()
        
        if not c:
            raise NotFoundError(f"Candidato com ID {candidate_id} não encontrado")
        
        result = {
            'success': True,
            'candidate': c.to_dict(include_sensitive=True, role=role)
        }
        
        # Cachear por 10 minutos (chave já inclui role)
        cache_manager.set(cache_key, result, ttl=600)
        
        return jsonify(result)
    
    except NotFoundError:
        raise
    except Exception as e:
        raise

@bp.patch("/<int:candidate_id>")
@require_auth
@retry_db_operation_improved(max_retries=3, initial_delay=1.0)
@invalidate_cache("cache:candidates:*")
def update_candidate(current_user, candidate_id):
    """Atualiza candidato com validação"""
    try:
        c = Candidate.query.filter_by(id=candidate_id, is_active=True).first()
        
        if not c:
            raise NotFoundError(f"Candidato com ID {candidate_id} não encontrado")
        
        if c.anonymized:
            raise AppValidationError("Não é possível atualizar candidato anonimizado")
        
        data = request.get_json(force=True, silent=True) or {}
        
        # Validar dados
        try:
            validated_data = CandidateValidator.validate_candidate_data(data, is_update=True)
        except ValidationError as e:
            raise AppValidationError(str(e))
        
        # Atualizar campos
        for field, value in validated_data.items():
            if hasattr(c, field):
                setattr(c, field, value)
        
        # Recalcular score
        c.calculate_overall_score()
        
        db.session.commit()
        
        # Invalidar cache
        cache_manager.delete(f"cache:candidates:{candidate_id}")
        cache_manager.delete_pattern("cache:candidates:list:*")
        
        return jsonify({
            'success': True,
            'candidate': c.to_dict(include_sensitive=True, role=getattr(current_user, 'role', None))
        })
    
    except (NotFoundError, AppValidationError):
        raise
    except Exception as e:
        db.session.rollback()
        raise

@bp.delete("/<int:candidate_id>")
@require_auth
@retry_db_operation_improved(max_retries=3, initial_delay=1.0)
@invalidate_cache("cache:candidates:*")
def delete_candidate(current_user, candidate_id):
    """Remove candidato (soft delete)"""
    try:
        c = Candidate.query.filter_by(id=candidate_id).first()
        
        if not c:
            raise NotFoundError(f"Candidato com ID {candidate_id} não encontrado")
        
        c.soft_delete()
        db.session.commit()
        
        # Invalidar cache
        cache_manager.delete(f"cache:candidates:{candidate_id}")
        cache_manager.delete_pattern("cache:candidates:list:*")
        
        return jsonify({
            'success': True,
            'status': 'deleted',
            'id': c.id
        })
    
    except NotFoundError:
        raise
    except Exception as e:
        db.session.rollback()
        raise


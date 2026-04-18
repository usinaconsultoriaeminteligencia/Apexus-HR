"""
Sistema robusto de tratamento de erros e exceções customizadas
"""
import logging
from typing import Optional, Dict, Any
from flask import jsonify, request, g
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Exceção base da aplicação"""
    status_code = 500
    message = "Erro interno do servidor"
    
    def __init__(self, message: Optional[str] = None, status_code: Optional[int] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error': self.message,
            'status_code': self.status_code,
            'details': self.details,
            'request_id': getattr(g, 'request_id', None)
        }


class ValidationError(AppError):
    """Erro de validação de dados"""
    status_code = 400
    message = "Dados inválidos"


class NotFoundError(AppError):
    """Recurso não encontrado"""
    status_code = 404
    message = "Recurso não encontrado"


class UnauthorizedError(AppError):
    """Não autorizado"""
    status_code = 401
    message = "Não autorizado"


class ForbiddenError(AppError):
    """Acesso negado"""
    status_code = 403
    message = "Acesso negado"


class ConflictError(AppError):
    """Conflito (ex: recurso já existe)"""
    status_code = 409
    message = "Conflito de recursos"


class DatabaseError(AppError):
    """Erro de banco de dados"""
    status_code = 500
    message = "Erro no banco de dados"


def handle_app_error(error: AppError):
    """Handler para exceções customizadas da aplicação"""
    logger.warning(f"AppError: {error.message} - {error.details}")
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_sqlalchemy_error(error: SQLAlchemyError):
    """Handler para erros do SQLAlchemy"""
    logger.error(f"Database error: {error}", exc_info=True)
    
    if isinstance(error, IntegrityError):
        # Violação de constraint (ex: email duplicado)
        message = "Violação de integridade de dados"
        if "unique" in str(error.orig).lower() or "duplicate" in str(error.orig).lower():
            message = "Registro já existe no sistema"
        elif "foreign key" in str(error.orig).lower():
            message = "Referência inválida"
        
        return jsonify({
            'error': message,
            'status_code': 409,
            'request_id': getattr(g, 'request_id', None)
        }), 409
    
    elif isinstance(error, OperationalError):
        # Erro de conexão/operação
        return jsonify({
            'error': 'Erro de conexão com o banco de dados',
            'status_code': 503,
            'request_id': getattr(g, 'request_id', None)
        }), 503
    
    else:
        # Outros erros do SQLAlchemy
        return jsonify({
            'error': 'Erro no banco de dados',
            'status_code': 500,
            'request_id': getattr(g, 'request_id', None)
        }), 500


def handle_http_exception(error: HTTPException):
    """Handler para exceções HTTP do Werkzeug"""
    logger.warning(f"HTTP {error.code}: {error.description}")
    return jsonify({
        'error': error.description,
        'status_code': error.code,
        'request_id': getattr(g, 'request_id', None)
    }), error.code


def handle_generic_exception(error: Exception):
    """Handler genérico para exceções não tratadas"""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    
    # Em produção, não expor detalhes do erro
    from flask import current_app
    is_production = current_app.config.get('ENVIRONMENT') == 'production'
    
    return jsonify({
        'error': 'Erro interno do servidor' if is_production else str(error),
        'status_code': 500,
        'request_id': getattr(g, 'request_id', None),
        'details': {} if is_production else {'type': type(error).__name__}
    }), 500


def register_error_handlers(app):
    """Registra todos os handlers de erro na aplicação Flask"""
    app.register_error_handler(AppError, handle_app_error)
    app.register_error_handler(SQLAlchemyError, handle_sqlalchemy_error)
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(Exception, handle_generic_exception)


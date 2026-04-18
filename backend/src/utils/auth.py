"""
Utilitários de autenticação e autorização
"""
from functools import wraps
from flask import request, jsonify
from sqlalchemy.orm import Session
from ..models import db, User
import logging

def require_auth(f):
    """Decorator para exigir autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Obter token do header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    'success': False,
                    'message': 'Token de acesso requerido'
                }), 401
            
            # Extrair token (formato: "Bearer <token>")
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({
                    'success': False,
                    'message': 'Formato de token inválido'
                }), 401
            
            # Verificar token
            payload = User.verify_token(token)
            
            if not payload:
                return jsonify({
                    'success': False,
                    'message': 'Token inválido ou expirado'
                }), 401
            
            # Buscar usuário
            user = User.query.filter(
                User.id == payload['user_id'],
                User.is_active == True
            ).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Usuário não encontrado'
                }), 401
            
            # Verificar se conta está bloqueada
            if user.is_account_locked():
                return jsonify({
                    'success': False,
                    'message': 'Conta bloqueada'
                }), 423
            
            # Adicionar usuário aos argumentos da função
            return f(user, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"Erro na autenticação: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Erro de autenticação'
            }), 401
    
    return decorated_function

def require_permission(permission):
    """Decorator para exigir permissão específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if not current_user.has_permission(permission):
                return jsonify({
                    'success': False,
                    'message': 'Permissão insuficiente'
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated_function
    return decorator

def require_role(required_roles):
    """Decorator para exigir papel específico"""
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in required_roles:
                return jsonify({
                    'success': False,
                    'message': 'Acesso negado'
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated_function
    return decorator

def hash_password(password):
    """Hash de senha (wrapper para compatibilidade)"""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)

def check_password(password_hash, password):
    """Verificação de senha (wrapper para compatibilidade)"""
    from werkzeug.security import check_password_hash
    return check_password_hash(password_hash, password)


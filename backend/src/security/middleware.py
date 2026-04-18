# backend/src/security/middleware.py
"""
Middleware de segurança para produção
Implementa autenticação, rate limiting, CORS, CSP e proteções
"""
import os
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, g, current_app
from werkzeug.exceptions import TooManyRequests
import redis
import jwt
import logging

from src.models.user import User
from src.models import db
from src.monitoring.logging_config import audit_logger, performance_logger
from src.utils.type_helpers import as_int

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter para proteção contra ataques de força bruta"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        )
        self.default_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 tentativas por 5 minutos
            'api': {'requests': 100, 'window': 60},   # 100 requests por minuto
            'upload': {'requests': 10, 'window': 60}, # 10 uploads por minuto
            'ai_analysis': {'requests': 20, 'window': 300}  # 20 análises por 5 minutos
        }
    
    def is_allowed(self, key, limit_type='api'):
        """Verifica se a requisição está dentro do limite"""
        try:
            limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            max_requests = limit_config['requests']
            window_seconds = limit_config['window']
            
            # Chave única para o rate limit
            rate_limit_key = f"rate_limit:{limit_type}:{key}"
            
            # Usar sliding window com Redis
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Remover entradas antigas
            self.redis_client.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Contar requisições na janela atual
            current_requests = self.redis_client.zcard(rate_limit_key)
            
            # Converter current_requests para int de forma segura
            # Redis pode retornar ResponseT, converter para str primeiro
            current_requests_int = as_int(str(current_requests) if current_requests is not None else "0")
            
            if current_requests_int >= int(max_requests):
                # Log da tentativa de rate limit
                audit_logger.log_security_event(
                    'rate_limit_exceeded',
                    'warning',
                    {
                        'key': key,
                        'limit_type': limit_type,
                        'current_requests': current_requests,
                        'max_requests': max_requests
                    }
                )
                return False
            
            # Adicionar requisição atual
            self.redis_client.zadd(rate_limit_key, {str(current_time): current_time})
            self.redis_client.expire(rate_limit_key, window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Em caso de erro, permitir a requisição (fail-open)
            return True
    
    def get_remaining_requests(self, key, limit_type='api'):
        """Retorna número de requisições restantes"""
        try:
            limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            max_requests = limit_config['requests']
            window_seconds = limit_config['window']
            
            rate_limit_key = f"rate_limit:{limit_type}:{key}"
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Limpar entradas antigas
            self.redis_client.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Contar requisições atuais
            current_requests = self.redis_client.zcard(rate_limit_key)
            
            # Converter current_requests para int de forma segura
            # Redis pode retornar ResponseT, converter para str primeiro
            current_requests_int = as_int(str(current_requests) if current_requests is not None else "0")
            
            return max(0, int(max_requests) - current_requests_int)
            
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return 0

class SecurityHeaders:
    """Classe para gerenciar headers de segurança"""
    
    @staticmethod
    def add_security_headers(response):
        """Adiciona headers de segurança à resposta"""
        # Headers de segurança básicos sem CSP problemático
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy simplificado
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(self), camera=(), '
            'payment=(), usb=()'
        )
        
        # HSTS apenas em produção com HTTPS
        if os.getenv('ENVIRONMENT') == 'production':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        
        return response

class AuthenticationMiddleware:
    """Middleware de autenticação JWT"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa middleware na aplicação Flask"""
        app.before_request(self.authenticate_request)
        app.after_request(SecurityHeaders.add_security_headers)
    
    def authenticate_request(self):
        """Autentica requisição usando JWT"""
        # Endpoints que não requerem autenticação
        public_endpoints = [
            'health.health_simple',
            'health.health_detailed',
            'health_advanced.health_simple',
            'health_advanced.health_detailed',
            'auth.login',
            'auth.register',
            'static',
            'app_info',
            # Removidas as rotas de audio_interview - agora requerem autenticação
            'product_intelligence.get_product_intelligence',
            'product_intelligence.get_product_rubrics',
            'interviews.list_interviews',  # Lista de entrevistas para relatórios
            'interviews.get_interview',    # Detalhes de entrevista específica
        ]
        
        # Pular autenticação para endpoints públicos
        if request.endpoint in public_endpoints:
            return
        
        # Pular autenticação para arquivos estáticos
        if request.path.startswith('/static/'):
            return

        # Extrair token do header Authorization
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de acesso requerido'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verificar e decodificar token
            payload = User.verify_token(token)
            
            if not payload:
                audit_logger.log_security_event(
                    'invalid_token_used',
                    'warning',
                    {'token_prefix': token[:10] + '...'}
                )
                return jsonify({'error': 'Token inválido ou expirado'}), 401
            
            # Buscar usuário
            user = db.session.get(User, payload['user_id'])
            
            if not user or not user.is_active:
                audit_logger.log_security_event(
                    'inactive_user_access_attempt',
                    'warning',
                    {'user_id': payload.get('user_id')}
                )
                return jsonify({'error': 'Usuário inativo'}), 401
            
            if user.is_account_locked():
                audit_logger.log_security_event(
                    'locked_user_access_attempt',
                    'warning',
                    {'user_id': user.id}
                )
                return jsonify({'error': 'Conta bloqueada'}), 423
            
            # Armazenar informações do usuário no contexto da requisição
            g.current_user = user
            g.user_id = user.id
            g.user_role = user.role
            g.request_id = self._generate_request_id()
            
            # Log da autenticação bem-sucedida
            audit_logger.log_user_action(
                'authenticated_request',
                user.id,
                {
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'request_id': g.request_id
                }
            )
            
        except jwt.ExpiredSignatureError:
            audit_logger.log_security_event(
                'expired_token_used',
                'info',
                {'endpoint': request.endpoint}
            )
            return jsonify({'error': 'Token expirado'}), 401
        
        except jwt.InvalidTokenError:
            audit_logger.log_security_event(
                'malformed_token_used',
                'warning',
                {'endpoint': request.endpoint}
            )
            return jsonify({'error': 'Token malformado'}), 401
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({'error': 'Erro de autenticação'}), 500
    
    def _generate_request_id(self):
        """Gera ID único para rastreamento de requisição"""
        import uuid
        return str(uuid.uuid4())

class AuthorizationMiddleware:
    """Middleware de autorização baseado em roles"""
    
    @staticmethod
    def require_role(required_role):
        """Decorator para exigir role específica"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user'):
                    return jsonify({'error': 'Autenticação requerida'}), 401
                
                user = g.current_user
                
                # Definir hierarquia de roles
                role_hierarchy = {
                    'viewer': 1,
                    'analyst': 2,
                    'recruiter': 3,
                    'manager': 4,
                    'admin': 5
                }
                
                user_level = role_hierarchy.get(user.role, 0)
                required_level = role_hierarchy.get(required_role, 999)
                
                if user_level < required_level:
                    audit_logger.log_security_event(
                        'insufficient_permissions',
                        'warning',
                        {
                            'user_id': user.id,
                            'user_role': user.role,
                            'required_role': required_role,
                            'endpoint': request.endpoint
                        }
                    )
                    return jsonify({'error': 'Permissões insuficientes'}), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    @staticmethod
    def require_permission(permission):
        """Decorator para exigir permissão específica"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user'):
                    return jsonify({'error': 'Autenticação requerida'}), 401
                
                user = g.current_user
                
                if not user.has_permission(permission):
                    audit_logger.log_security_event(
                        'permission_denied',
                        'warning',
                        {
                            'user_id': user.id,
                            'permission': permission,
                            'endpoint': request.endpoint
                        }
                    )
                    return jsonify({'error': f'Permissão {permission} requerida'}), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

class InputValidationMiddleware:
    """Middleware para validação e sanitização de entrada"""
    
    @staticmethod
    def validate_json_input(f):
        """Decorator para validar entrada JSON"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json:
                try:
                    data = request.get_json()
                    
                    # Verificar se há tentativas de injeção
                    if InputValidationMiddleware._detect_injection_attempts(data):
                        audit_logger.log_security_event(
                            'injection_attempt_detected',
                            'critical',
                            {
                                'data': str(data)[:500],  # Primeiros 500 chars
                                'user_id': getattr(g, 'user_id', None)
                            }
                        )
                        return jsonify({'error': 'Entrada inválida detectada'}), 400
                    
                    # Sanitizar dados
                    sanitized_data = InputValidationMiddleware._sanitize_data(data)
                    request._cached_json = (sanitized_data, None)
                    
                except Exception as e:
                    logger.error(f"JSON validation error: {e}")
                    return jsonify({'error': 'JSON inválido'}), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    @staticmethod
    def _detect_injection_attempts(data):
        """Detecta tentativas de injeção SQL, XSS, etc."""
        if not isinstance(data, (dict, list, str)):
            return False
        
        # Padrões suspeitos
        suspicious_patterns = [
            # SQL Injection
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC)\b)",
            r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|#|/\*|\*/)",
            
            # XSS
            r"(<script[^>]*>.*?</script>)",
            r"(javascript:)",
            r"(on\w+\s*=)",
            
            # Command Injection
            r"(;|\||\&\&|\|\|)",
            r"(\$\(|\`)",
            
            # Path Traversal
            r"(\.\./|\.\.\\)",
            r"(/etc/passwd|/windows/system32)"
        ]
        
        import re
        
        def check_string(s):
            if not isinstance(s, str):
                return False
            
            s_lower = s.lower()
            for pattern in suspicious_patterns:
                if re.search(pattern, s_lower, re.IGNORECASE):
                    return True
            return False
        
        def check_recursive(obj):
            if isinstance(obj, str):
                return check_string(obj)
            elif isinstance(obj, dict):
                return any(check_recursive(v) or check_string(str(k)) for k, v in obj.items())
            elif isinstance(obj, list):
                return any(check_recursive(item) for item in obj)
            return False
        
        return check_recursive(data)
    
    @staticmethod
    def _sanitize_data(data):
        """Sanitiza dados de entrada"""
        import html
        
        def sanitize_string(s):
            if not isinstance(s, str):
                return s
            
            # Escapar HTML
            s = html.escape(s)
            
            # Remover caracteres de controle
            s = ''.join(char for char in s if ord(char) >= 32 or char in '\t\n\r')
            
            # Limitar tamanho
            if len(s) > 10000:  # 10KB limit
                s = s[:10000]
            
            return s
        
        def sanitize_recursive(obj):
            if isinstance(obj, str):
                return sanitize_string(obj)
            elif isinstance(obj, dict):
                return {k: sanitize_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            return obj
        
        return sanitize_recursive(data)

# Instâncias globais
rate_limiter = RateLimiter()

def rate_limit(limit_type='api'):
    """Decorator para aplicar rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Identificar cliente (IP + user_id se autenticado)
            client_id = request.remote_addr
            if hasattr(g, 'user_id'):
                client_id = f"{client_id}:{g.user_id}"
            
            if not rate_limiter.is_allowed(client_id, limit_type):
                remaining = rate_limiter.get_remaining_requests(client_id, limit_type)
                
                response = jsonify({
                    'error': 'Rate limit excedido',
                    'retry_after': 60,
                    'remaining_requests': remaining
                })
                response.status_code = 429
                response.headers['Retry-After'] = '60'
                
                return response
            
            # Adicionar headers de rate limit à resposta
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                remaining = rate_limiter.get_remaining_requests(client_id, limit_type)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
            
            return response
        
        return decorated_function
    return decorator

def setup_security_middleware(app):
    """Configura middlewares de segurança.

    Observação: o CORS é configurado uma única vez em ``src/main.py`` usando
    a variável ``CORS_ORIGINS``. Configurar CORS de novo aqui provocava
    conflito de origens e comportamento imprevisível em produção.
    """
    # Autenticação JWT + headers de segurança em todas as respostas
    AuthenticationMiddleware(app)

    # Middleware de request ID para rastreamento
    @app.before_request
    def add_request_id():
        if not hasattr(g, 'request_id'):
            import uuid
            g.request_id = str(uuid.uuid4())

    # Middleware de timing para performance
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def end_timer(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            g.request_duration = duration

            # Log de requests lentos
            if duration > 2.0:  # Mais de 2 segundos
                performance_logger.log_slow_query(
                    f"{request.method} {request.path}",
                    duration,
                    {'endpoint': request.endpoint}
                )

        return response

    logger.info("Security middleware configured successfully")


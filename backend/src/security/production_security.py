"""
Configurações de segurança para produção
"""
import os
from flask import Flask
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def configure_production_security(app: Flask):
    """Configura todas as medidas de segurança para produção"""
    
    # 1. HTTPS e HSTS
    configure_https_security(app)
    
    # 2. Rate Limiting
    configure_rate_limiting(app)
    
    # 3. Content Security Policy
    configure_csp(app)
    
    # 4. Headers de segurança
    configure_security_headers(app)

def configure_https_security(app: Flask):
    """Configura HTTPS e HSTS"""
    
    # Forçar HTTPS em produção
    if app.config.get('ENVIRONMENT') == 'production':
        from flask_talisman import Talisman
        
        csp = {
            'default-src': "'self'",
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Necessário para alguns componentes
                "https://cdn.jsdelivr.net",
                "https://unpkg.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Necessário para Tailwind CSS
                "https://fonts.googleapis.com"
            ],
            'font-src': [
                "'self'",
                "https://fonts.gstatic.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:"
            ],
            'connect-src': [
                "'self'",
                "https://api.openai.com"
            ],
            'frame-ancestors': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'"
        }
        
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 ano
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src', 'style-src']
        )

def configure_rate_limiting(app: Flask):
    """Configura rate limiting"""
    
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["1000 per hour", "100 per minute"]
    )
    
    # Rate limits específicos por endpoint
    @app.before_request
    def set_rate_limits():
        from flask import request
        
        # Endpoints de autenticação - mais restritivos
        if request.endpoint in ['auth.login', 'auth.register']:
            limiter.limit("10 per minute")(lambda: None)
        
        # Endpoints de upload - moderados
        elif 'upload' in request.endpoint or 'audio' in request.endpoint:
            limiter.limit("20 per minute")(lambda: None)
        
        # Endpoints de API - normais
        elif request.endpoint and request.endpoint.startswith('api'):
            limiter.limit("200 per hour")(lambda: None)

def configure_csp(app: Flask):
    """Configura Content Security Policy"""
    
    @app.after_request
    def add_csp_header(response):
        if app.config.get('ENVIRONMENT') == 'production':
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response

def configure_security_headers(app: Flask):
    """Configura headers de segurança adicionais"""
    
    @app.before_request
    def security_headers():
        from flask import request, g
        
        # Log de tentativas suspeitas
        if request.remote_addr:
            # Implementar detecção de IPs suspeitos
            # (pode integrar com serviços como AbuseIPDB)
            pass
        
        # Validação de User-Agent suspeito
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or len(user_agent) < 10:
            app.logger.warning(f"User-Agent suspeito: {user_agent} de {request.remote_addr}")

def generate_secure_headers():
    """Gera headers de segurança recomendados"""
    return {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin'
    }

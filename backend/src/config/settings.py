"""
Configurações do sistema Apexus HR
"""
import os
from datetime import timedelta

class Config:
    """Configuração base"""
    
    # Configurações básicas
    SECRET_KEY = os.getenv('SECRET_KEY', 'apexus-hr-secret-key-2024')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Banco de dados
    DATABASE_URL = os.getenv(
        'DATABASE_URL', 
        'postgresql://apexus_hr_user:secure_password@localhost:5432/apexus_hr'
    )
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-apexus-hr-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    
    # Redis (para cache e sessões)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Upload de arquivos
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'wav', 'mp3', 'mp4'}
    
    # Email (para notificações)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@apexushr.com')
    
    # Celery (para processamento assíncrono)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/apexus_hr.log')
    
    # LGPD
    DATA_RETENTION_YEARS = int(os.getenv('DATA_RETENTION_YEARS', '5'))
    ANONYMIZATION_SCHEDULE = os.getenv('ANONYMIZATION_SCHEDULE', '0 2 * * 0')  # Todo domingo às 2h
    
    # Análise de áudio
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '16000'))
    AUDIO_MAX_DURATION = int(os.getenv('AUDIO_MAX_DURATION', '300'))  # 5 minutos
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/2')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    
    # Monitoramento
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    PROMETHEUS_METRICS = os.getenv('PROMETHEUS_METRICS', 'True').lower() == 'true'

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    DATABASE_URL = os.getenv(
        'DATABASE_URL', 
        'postgresql://apexus_hr_user:secure_password@localhost:5432/apexus_hr_dev'
    )

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    DATABASE_URL = os.getenv(
        'DATABASE_URL', 
        'postgresql://apexus_hr_user:secure_password@localhost:5432/apexus_hr_test'
    )
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    
    # Configurações de segurança para produção
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # SSL
    PREFERRED_URL_SCHEME = 'https'

# Mapeamento de configurações por ambiente
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retorna a configuração baseada na variável de ambiente"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])


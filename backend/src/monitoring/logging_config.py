# backend/src/monitoring/logging_config.py
"""
Configuração de logging estruturado para produção
Implementa logging JSON, correlação de requests e auditoria
"""
import logging
import logging.config
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from flask import request, g, has_request_context
import traceback
from typing import Dict, Any, Optional

class StructuredFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }
        
        # Adicionar contexto da requisição se disponível
        if has_request_context():
            log_data.update({
                'request_id': getattr(g, 'request_id', None),
                'user_id': getattr(g, 'user_id', None),
                'endpoint': request.endpoint,
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
            })
        
        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Adicionar campos extras do record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class AuditLogger:
    """Logger especializado para auditoria de ações sensíveis"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
    
    def log_user_action(self, action: str, user_id: Optional[int] = None, 
                       details: Optional[Dict[str, Any]] = None):
        """Registra ação do usuário para auditoria"""
        audit_data = {
            'action': action,
            'user_id': user_id or getattr(g, 'user_id', None),
            'details': details or {},
            'ip_address': request.remote_addr if has_request_context() else None,
            'user_agent': request.headers.get('User-Agent', '') if has_request_context() else '',
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        self.logger.info("User action", extra={'audit_data': audit_data})
    
    def log_data_access(self, resource_type: str, resource_id: str, 
                       operation: str, user_id: Optional[int] = None):
        """Registra acesso a dados sensíveis (LGPD compliance)"""
        access_data = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'operation': operation,
            'user_id': user_id or getattr(g, 'user_id', None),
            'ip_address': request.remote_addr if has_request_context() else None,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        self.logger.info("Data access", extra={'access_data': access_data})
    
    def log_security_event(self, event_type: str, severity: str, 
                          details: Optional[Dict[str, Any]] = None):
        """Registra eventos de segurança"""
        security_data = {
            'event_type': event_type,
            'severity': severity,
            'details': details or {},
            'ip_address': request.remote_addr if has_request_context() else None,
            'user_agent': request.headers.get('User-Agent', '') if has_request_context() else '',
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        self.logger.warning("Security event", extra={'security_data': security_data})

class PerformanceLogger:
    """Logger especializado para métricas de performance"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def log_slow_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """Registra queries lentas do banco"""
        perf_data = {
            'type': 'slow_query',
            'query': query,
            'duration_ms': duration * 1000,
            'params': params or {},
            'threshold_exceeded': duration > 1.0  # 1 segundo
        }
        
        self.logger.warning("Slow database query", extra={'performance_data': perf_data})
    
    def log_ai_processing(self, operation: str, duration: float, 
                         success: bool, details: Optional[Dict] = None):
        """Registra processamento de IA"""
        perf_data = {
            'type': 'ai_processing',
            'operation': operation,
            'duration_ms': duration * 1000,
            'success': success,
            'details': details or {}
        }
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, "AI processing completed", extra={'performance_data': perf_data})
    
    def log_audio_processing(self, file_size: int, duration: float, 
                           format_type: str, success: bool):
        """Registra processamento de áudio"""
        perf_data = {
            'type': 'audio_processing',
            'file_size_bytes': file_size,
            'duration_ms': duration * 1000,
            'format': format_type,
            'success': success,
            'processing_rate_mb_per_sec': (file_size / (1024 * 1024)) / duration if duration > 0 else 0
        }
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, "Audio processing completed", extra={'performance_data': perf_data})

def setup_logging(app):
    """Configura sistema de logging para a aplicação"""
    
    # Determinar nível de log baseado no ambiente
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_dir = Path(os.getenv(
        'LOG_DIR',
        '/tmp/logs' if os.getenv('ENVIRONMENT') == 'production' and os.name != 'nt' else 'logs'
    ))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuração de logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'structured' if os.getenv('ENVIRONMENT') == 'production' else 'simple',
                'stream': sys.stdout,
                'level': log_level
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_dir / 'application.log'),
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'formatter': 'structured',
                'level': log_level
            },
            'audit_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_dir / 'audit.log'),
                'maxBytes': 100 * 1024 * 1024,  # 100MB
                'backupCount': 20,
                'formatter': 'structured',
                'level': 'INFO'
            },
            'performance_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_dir / 'performance.log'),
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'formatter': 'structured',
                'level': 'INFO'
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False
            },
            'audit': {
                'handlers': ['audit_file', 'console'],
                'level': 'INFO',
                'propagate': False
            },
            'performance': {
                'handlers': ['performance_file', 'console'],
                'level': 'INFO',
                'propagate': False
            },
            'werkzeug': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False
            },
            'sqlalchemy.engine': {
                'handlers': ['performance_file'],
                'level': 'INFO' if os.getenv('LOG_SQL') == 'true' else 'WARNING',
                'propagate': False
            }
        }
    }
    
    # Criar diretório de logs se não existir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Aplicar configuração
    logging.config.dictConfig(logging_config)
    
    # Configurar logger da aplicação Flask
    app.logger.handlers = []
    app.logger.propagate = True
    
    return logging.getLogger(__name__)

# Instâncias globais dos loggers especializados
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()

def log_request_start():
    """Registra início da requisição"""
    if has_request_context():
        logger = logging.getLogger('request')
        logger.info("Request started", extra={
            'method': request.method,
            'url': request.url,
            'remote_addr': request.remote_addr,
            'content_length': request.content_length,
            'content_type': request.content_type
        })

def log_request_end(response):
    """Registra fim da requisição"""
    if has_request_context():
        logger = logging.getLogger('request')
        logger.info("Request completed", extra={
            'status_code': response.status_code,
            'content_length': response.content_length,
            'duration_ms': getattr(g, 'request_duration', 0) * 1000
        })
    return response

def log_exception(error):
    """Registra exceções não tratadas"""
    logger = logging.getLogger('error')
    logger.error("Unhandled exception", exc_info=True, extra={
        'error_type': type(error).__name__,
        'error_message': str(error)
    })

# Configurar captura de logs do SQLAlchemy para monitorar queries
class SQLAlchemyLogHandler(logging.Handler):
    """Handler customizado para logs do SQLAlchemy"""
    
    def emit(self, record):
        if 'SELECT' in record.getMessage() or 'INSERT' in record.getMessage() or \
           'UPDATE' in record.getMessage() or 'DELETE' in record.getMessage():
            # Extrair informações da query
            query_info = {
                'query': record.getMessage(),
                'level': record.levelname,
                'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
            
            # Log para análise de performance
            perf_logger = logging.getLogger('performance')
            perf_logger.debug("Database query", extra={'query_info': query_info})

# Adicionar handler customizado para SQLAlchemy
sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
sqlalchemy_logger.addHandler(SQLAlchemyLogHandler())


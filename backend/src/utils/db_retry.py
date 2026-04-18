"""
Utilitário para retry de operações de banco de dados com problemas SSL
"""
import time
import logging
import functools
from sqlalchemy.exc import OperationalError, DisconnectionError


def retry_db_operation(max_retries=3, delay=1):
    """Decorator para retry de operações de banco que falham por problemas SSL"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    last_exception = e
                    error_message = str(e).lower()
                    
                    # Verifica se é um erro relacionado à SSL ou conexão
                    ssl_related_errors = [
                        'ssl connection has been closed unexpectedly',
                        'connection already closed',
                        'server closed the connection unexpectedly',
                        'connection reset by peer',
                        'broken pipe'
                    ]
                    
                    if any(ssl_error in error_message for ssl_error in ssl_related_errors):
                        if attempt < max_retries - 1:
                            logging.warning(f"SSL/Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                            time.sleep(delay * (attempt + 1))  # Backoff exponencial
                            
                            # Força reconexão do pool
                            try:
                                from src.models import db
                                db.engine.dispose()
                            except Exception as dispose_error:
                                logging.error(f"Erro ao dispose do engine: {dispose_error}")
                            
                            continue
                    
                    # Se não é SSL ou esgotamos tentativas, propaga o erro
                    raise e
                except Exception as e:
                    # Outros erros não relacionados a SSL
                    raise e
            
            # Se chegou aqui, esgotou as tentativas
            raise last_exception
        
        return wrapper
    return decorator
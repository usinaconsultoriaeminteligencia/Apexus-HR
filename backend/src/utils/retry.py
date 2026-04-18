"""
Sistema de retry com exponential backoff e jitter
"""
import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Exceção quando todas as tentativas de retry falharam"""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator para retry com exponential backoff e jitter
    
    Args:
        max_retries: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        max_delay: Delay máximo em segundos
        exponential_base: Base para cálculo exponencial
        jitter: Se True, adiciona aleatoriedade ao delay
        retry_on: Tupla de exceções que devem ser retentadas
        on_retry: Callback chamado a cada retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                
                except retry_on as e:
                    last_exception = e
                    
                    # Não retentar se for a última tentativa
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Todas as tentativas falharam para {func.__name__} "
                            f"(última tentativa: {attempt + 1}/{max_retries})"
                        )
                        raise RetryError(f"Falha após {max_retries} tentativas") from e
                    
                    # Calcular delay com exponential backoff
                    delay = initial_delay * (exponential_base ** attempt)
                    
                    # Aplicar jitter (aleatoriedade)
                    if jitter:
                        jitter_amount = delay * 0.1  # 10% de jitter
                        delay = delay + random.uniform(-jitter_amount, jitter_amount)
                    
                    # Limitar delay máximo
                    delay = min(delay, max_delay)
                    
                    # Log do retry
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} para {func.__name__} "
                        f"após {type(e).__name__}: {str(e)[:100]}. "
                        f"Aguardando {delay:.2f}s..."
                    )
                    
                    # Callback de retry
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Erro no callback de retry: {callback_error}")
                    
                    # Aguardar antes de retentar
                    time.sleep(delay)
                
                except Exception as e:
                    # Exceção não está na lista de retry_on - re-raise imediatamente
                    logger.error(f"Exceção não retentável em {func.__name__}: {type(e).__name__}: {e}")
                    raise
            
            # Não deveria chegar aqui, mas por segurança
            if last_exception:
                raise RetryError(f"Falha após {max_retries} tentativas") from last_exception
            raise RetryError(f"Falha inesperada em {func.__name__}")
        
        return wrapper
    return decorator


def retry_db_operation_improved(
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """
    Decorator específico para operações de banco de dados
    com reconexão automática
    """
    from sqlalchemy.exc import OperationalError, DisconnectionError
    
    def on_retry(attempt: int, exception: Exception, delay: float):
        """Callback para reconectar ao banco"""
        if isinstance(exception, (OperationalError, DisconnectionError)):
            try:
                from src.models import db
                # Forçar reconexão
                db.engine.dispose()
                logger.info(f"Pool de conexões reinicializado após erro de conexão")
            except Exception as e:
                logger.error(f"Erro ao reinicializar pool: {e}")
    
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
        retry_on=(OperationalError, DisconnectionError),
        on_retry=on_retry
    )


def retry_api_call(
    max_retries: int = 3,
    initial_delay: float = 0.5
):
    """
    Decorator para chamadas de API externas
    """
    import requests
    
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True,
        retry_on=(
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException
        )
    )


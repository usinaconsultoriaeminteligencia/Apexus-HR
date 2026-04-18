"""
Sistema de cache usando Redis com TTL e invalidação inteligente
"""
import json
import logging
import redis
import os
from typing import Optional, Any, Callable
from functools import wraps
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Gerenciador de cache Redis"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    @property
    def client(self) -> redis.Redis:
        """Lazy initialization do cliente Redis"""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Testar conexão
                self._client.ping()
                self._connected = True
                logger.info("Cache Redis conectado com sucesso")
            except Exception as e:
                logger.warning(f"Falha ao conectar ao Redis: {e}. Cache desabilitado.")
                self._connected = False
                self._client = None
        
        return self._client
    
    def is_available(self) -> bool:
        """Verifica se cache está disponível"""
        if not self._connected:
            return False
        
        try:
            self.client.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """Obtém valor do cache"""
        if not self.is_available():
            return default
        
        try:
            value = self.client.get(key)
            if value is None:
                return default
            
            # Tentar fazer parse JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Erro ao obter cache key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Define valor no cache com TTL"""
        if not self.is_available():
            return False
        
        try:
            # Serializar para JSON se necessário
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value, ensure_ascii=False)
            else:
                serialized = str(value)
            
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Erro ao definir cache key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove chave do cache"""
        if not self.is_available():
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Erro ao deletar cache key '{key}': {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Remove todas as chaves que correspondem ao padrão"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Erro ao deletar padrão '{pattern}': {e}")
            return 0
    
    def clear(self) -> bool:
        """Limpa todo o cache (cuidado!)"""
        if not self.is_available():
            return False
        
        try:
            self.client.flushdb()
            logger.warning("Cache limpo completamente")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    def get_or_set(self, key: str, func: Callable, ttl: int = 3600, *args, **kwargs) -> Any:
        """Obtém do cache ou executa função e armazena resultado"""
        # Tentar obter do cache
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached
        
        # Cache miss - executar função
        logger.debug(f"Cache miss: {key}")
        result = func(*args, **kwargs)
        
        # Armazenar no cache
        self.set(key, result, ttl)
        
        return result


# Instância global
cache_manager = CacheManager()


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """Decorator para cachear resultado de função"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave única baseada na função e argumentos
            import hashlib
            key_parts = [key_prefix, func.__name__, str(args), str(sorted(kwargs.items()))]
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            cache_key = f"{key_prefix}:{func.__name__}:{key}"
            
            # Tentar obter do cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Decorator para invalidar cache após operação"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidar cache após operação
            deleted = cache_manager.delete_pattern(pattern)
            if deleted > 0:
                logger.debug(f"Cache invalidado: {pattern} ({deleted} chaves)")
            
            return result
        
        return wrapper
    return decorator


"""
🚀 Cache Manager - Sistema de cache em memória e Redis (opcional)

Performance otimizada para queries frequentes:
- Dashboard
- Relatórios
- Listas de categorias/contas
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import json
import hashlib

# Cache em memória (fallback)
_memory_cache = {}
_cache_timestamps = {}
_cache_hits = 0
_cache_misses = 0

# Configuração
CACHE_DEFAULT_TTL = 300  # 5 minutos
CACHE_ENABLED = True


def _get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Gera chave única para o cache baseada nos argumentos"""
    key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _is_cache_valid(key: str, ttl: int) -> bool:
    """Verifica se o cache ainda é válido"""
    if key not in _cache_timestamps:
        return False
    
    timestamp = _cache_timestamps[key]
    return (datetime.now() - timestamp).total_seconds() < ttl


def get_cached(key: str) -> Optional[Any]:
    """Recupera valor do cache"""
    if not CACHE_ENABLED:
        return None
    
    if key in _memory_cache and _is_cache_valid(key, CACHE_DEFAULT_TTL):
        global _cache_hits
        _cache_hits += 1
        print(f"✅ Cache HIT: {key[:16]}...")
        return _memory_cache[key]
    
    global _cache_misses
    _cache_misses += 1
    print(f"❌ Cache MISS: {key[:16]}...")
    return None


def set_cached(key: str, value: Any, ttl: int = CACHE_DEFAULT_TTL):
    """Armazena valor no cache"""
    if not CACHE_ENABLED:
        return
    
    _memory_cache[key] = value
    _cache_timestamps[key] = datetime.now()
    print(f"💾 Cache SET: {key[:16]}... (TTL: {ttl}s)")


def invalidate_cache(pattern: str = None):
    """Invalida cache por padrão ou limpa tudo"""
    global _cache_hits, _cache_misses
    
    if pattern:
        keys_to_remove = [k for k in _memory_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del _memory_cache[key]
            del _cache_timestamps[key]
        print(f"🗑️ Cache invalidado: {len(keys_to_remove)} chaves com padrão '{pattern}'")
    else:
        _memory_cache.clear()
        _cache_timestamps.clear()
        _cache_hits = 0
        _cache_misses = 0
        print("🗑️ Cache completamente limpo")
        print("🗑️ Cache totalmente limpo")


def cached(ttl: int = CACHE_DEFAULT_TTL, prefix: str = ""):
    """
    Decorator para cachear resultado de funções
    
    Usage:
        @cached(ttl=600, prefix="dashboard")
        def get_dashboard_data(user_id):
            # query pesada...
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not CACHE_ENABLED:
                return func(*args, **kwargs)
            
            # Gerar chave do cache
            cache_prefix = prefix or func.__name__
            cache_key = _get_cache_key(cache_prefix, *args, **kwargs)
            
            # Tentar recuperar do cache
            cached_value = get_cached(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            set_cached(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache"""
    total_keys = len(_memory_cache)
    valid_keys = sum(1 for k in _memory_cache.keys() if _is_cache_valid(k, CACHE_DEFAULT_TTL))
    expired_keys = total_keys - valid_keys
    
    # Calcular hit rate
    total_requests = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    # Calcular tamanho da memória
    memory_kb = sum(len(str(v)) for v in _memory_cache.values()) / 1024
    memory_usage = f"{memory_kb:.2f} KB" if memory_kb < 1024 else f"{memory_kb/1024:.2f} MB"
    
    return {
        'enabled': CACHE_ENABLED,
        'total_keys': total_keys,
        'valid_keys': valid_keys,
        'expired_keys': expired_keys,
        'memory_size_kb': memory_kb,
        'memory_usage': memory_usage,
        'cache_hits': _cache_hits,
        'cache_misses': _cache_misses,
        'hit_rate': hit_rate
    }


def cleanup_expired():
    """Remove entradas expiradas do cache"""
    expired_keys = [
        k for k in _memory_cache.keys() 
        if not _is_cache_valid(k, CACHE_DEFAULT_TTL)
    ]
    
    for key in expired_keys:
        del _memory_cache[key]
        del _cache_timestamps[key]
    
    print(f"🧹 Limpeza automática: {len(expired_keys)} chaves expiradas removidas")
    return len(expired_keys)

"""
Cache helper - Sistema de cache simples para Flask
Usa functools.lru_cache para cache em memória
"""

from functools import wraps, lru_cache
from datetime import datetime, timedelta
import hashlib
import json


# Cache em memória para dados que mudam pouco
_cache_store = {}


def cache_with_timeout(timeout_seconds=300):
    """
    Decorator para cache com timeout
    
    Args:
        timeout_seconds: Tempo de expiração do cache em segundos
        
    Uso:
        @cache_with_timeout(600)  # 10 minutos
        def get_dashboard_data(empresa_id):
            # código aqui
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Criar chave única baseada em função e argumentos
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Verificar se está no cache e não expirou
            if cache_key in _cache_store:
                cached_data, expiry_time = _cache_store[cache_key]
                if datetime.now() < expiry_time:
                    return cached_data
                else:
                    # Expirou, remover do cache
                    del _cache_store[cache_key]
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            expiry_time = datetime.now() + timedelta(seconds=timeout_seconds)
            _cache_store[cache_key] = (result, expiry_time)
            
            return result
        
        # Adicionar método para limpar cache desta função
        def clear_cache(*args, **kwargs):
            if args or kwargs:
                # Limpar cache específico
                cache_key = _generate_cache_key(func.__name__, args, kwargs)
                if cache_key in _cache_store:
                    del _cache_store[cache_key]
            else:
                # Limpar todo cache desta função
                keys_to_delete = [k for k in _cache_store.keys() if k.startswith(func.__name__)]
                for key in keys_to_delete:
                    del _cache_store[key]
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


def _generate_cache_key(func_name, args, kwargs):
    """Gera chave única para cache"""
    # Converter args e kwargs em string serializável
    key_parts = [func_name]
    
    # Adicionar args
    for arg in args:
        key_parts.append(str(arg))
    
    # Adicionar kwargs ordenados
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")
    
    # Criar hash da chave
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def clear_all_cache():
    """Limpa todo o cache"""
    global _cache_store
    _cache_store = {}


def get_cache_stats():
    """Retorna estatísticas do cache"""
    total_items = len(_cache_store)
    expired_items = 0
    
    now = datetime.now()
    for cached_data, expiry_time in _cache_store.values():
        if now >= expiry_time:
            expired_items += 1
    
    return {
        'total_items': total_items,
        'active_items': total_items - expired_items,
        'expired_items': expired_items
    }


# Decorators específicos para diferentes tipos de cache

def cache_dashboard(timeout_seconds=300):
    """Cache para dashboard (5 minutos padrão)"""
    return cache_with_timeout(timeout_seconds)


def cache_relatorio(timeout_seconds=600):
    """Cache para relatórios (10 minutos padrão)"""
    return cache_with_timeout(timeout_seconds)


def cache_lookup(timeout_seconds=3600):
    """Cache para lookups estáticos (1 hora padrão)"""
    return cache_with_timeout(timeout_seconds)


def cache_lista(timeout_seconds=180):
    """Cache para listas (3 minutos padrão)"""
    return cache_with_timeout(timeout_seconds)


# LRU Cache para funções puras (sem timeout)

def lru_cache_small(func):
    """LRU cache para funções pequenas (maxsize=128)"""
    return lru_cache(maxsize=128)(func)


def lru_cache_medium(func):
    """LRU cache para funções médias (maxsize=512)"""
    return lru_cache(maxsize=512)(func)


def lru_cache_large(func):
    """LRU cache para funções grandes (maxsize=2048)"""
    return lru_cache(maxsize=2048)(func)


# Exemplo de uso:
"""
from app.utils.cache_helper import cache_dashboard, cache_lookup

@cache_dashboard(timeout_seconds=300)
def get_dashboard_summary(empresa_id):
    # Consultas ao banco aqui
    return {...}

@cache_lookup(timeout_seconds=3600)
def get_categorias_ativas(empresa_id):
    # Consulta de categorias
    return [...]

# Para limpar cache quando houver mudanças:
# get_dashboard_summary.clear_cache(empresa_id=1)
# ou clear_all_cache()
"""

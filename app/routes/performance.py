"""
⚡ Blueprint de Performance - Monitoramento e otimizações

Endpoints:
- GET /api/performance/stats - Estatísticas de cache e queries
- GET /api/performance/slow-queries - Queries lentas
- POST /api/performance/clear-cache - Limpar cache
- GET /api/performance/indexes - Sugestões de índices
"""

from flask import Blueprint, jsonify, request
from app.utils.cache_manager import get_cache_stats, invalidate_cache, cleanup_expired
from app.utils.query_optimizer import profiler
from app.decorators import require_permission

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')


@performance_bp.route('/stats', methods=['GET'])
@require_permission('admin')
def get_performance_stats():
    """Estatísticas de performance do sistema"""
    try:
        cache_stats = get_cache_stats()
        query_stats = profiler.get_stats()
        
        # Calcular hit rate
        hit_rate = 0
        if cache_stats['total_keys'] > 0:
            hit_rate = (cache_stats['valid_keys'] / cache_stats['total_keys']) * 100
        
        return jsonify({
            'success': True,
            'cache': {
                'enabled': cache_stats['enabled'],
                'total_keys': cache_stats['total_keys'],
                'valid_keys': cache_stats['valid_keys'],
                'expired_keys': cache_stats['expired_keys'],
                'hit_rate_percent': round(hit_rate, 2),
                'memory_size_kb': round(cache_stats['memory_size_kb'], 2)
            },
            'queries': {
                'total_queries': query_stats.get('total_queries', 0),
                'total_time_sec': round(query_stats.get('total_time', 0), 3),
                'avg_time_ms': round(query_stats.get('avg_time', 0) * 1000, 2) if query_stats.get('total_queries', 0) > 0 else 0,
                'max_time_ms': round(query_stats.get('max_time', 0) * 1000, 2) if query_stats.get('total_queries', 0) > 0 else 0,
                'slow_queries': query_stats.get('slow_queries', 0)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/slow-queries', methods=['GET'])
@require_permission('admin')
def get_slow_queries():
    """Lista queries lentas (> 100ms)"""
    try:
        threshold = request.args.get('threshold_ms', 100, type=float)
        slow_queries = profiler.get_slow_queries(threshold)
        
        # Formatar resultado
        formatted = []
        for q in slow_queries[-50:]:  # Últimas 50
            formatted.append({
                'query': q['query'][:200],  # Truncar query longa
                'duration_ms': round(q['duration'] * 1000, 2),
                'timestamp': q['timestamp'].isoformat()
            })
        
        return jsonify({
            'success': True,
            'total': len(slow_queries),
            'showing': len(formatted),
            'queries': formatted
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/clear-cache', methods=['POST'])
@require_permission('admin')
def clear_cache():
    """Limpa cache do sistema"""
    try:
        pattern = request.json.get('pattern') if request.json else None
        
        if pattern:
            invalidate_cache(pattern)
            message = f"Cache invalidado para padrão: {pattern}"
        else:
            invalidate_cache()
            message = "Cache totalmente limpo"
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/cleanup-cache', methods=['POST'])
@require_permission('admin')
def cleanup_cache():
    """Remove entradas expiradas do cache"""
    try:
        removed = cleanup_expired()
        
        return jsonify({
            'success': True,
            'message': f'{removed} entradas expiradas removidas',
            'removed_count': removed
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/indexes', methods=['GET'])
@require_permission('admin')
def suggest_indexes():
    """Sugere índices para otimização"""
    try:
        # Sugestões baseadas em padrões de uso comuns
        suggestions = [
            {
                'table': 'lancamentos',
                'index': 'idx_lancamentos_filtros',
                'sql': 'CREATE INDEX idx_lancamentos_filtros ON lancamentos(proprietario_id, status, data_pagamento);',
                'benefit': 'Otimiza queries de dashboard e relatórios que filtram por status e data',
                'estimated_improvement': '70-90%'
            },
            {
                'table': 'lancamentos',
                'index': 'idx_lancamentos_tipo_status',
                'sql': 'CREATE INDEX idx_lancamentos_tipo_status ON lancamentos(tipo, status, data_vencimento DESC);',
                'benefit': 'Acelera listagens filtradas por tipo e status',
                'estimated_improvement': '60-80%'
            },
            {
                'table': 'lancamentos',
                'index': 'idx_lancamentos_conta_data',
                'sql': 'CREATE INDEX idx_lancamentos_conta_data ON lancamentos(conta_bancaria, data_vencimento);',
                'benefit': 'Otimiza relatórios por conta bancária',
                'estimated_improvement': '50-70%'
            },
            {
                'table': 'lancamentos',
                'index': 'idx_lancamentos_categoria',
                'sql': 'CREATE INDEX idx_lancamentos_categoria ON lancamentos(categoria, data_pagamento) WHERE status = \'pago\';',
                'benefit': 'Índice parcial para análises por categoria (apenas lançamentos pagos)',
                'estimated_improvement': '40-60%'
            },
            {
                'table': 'contratos',
                'index': 'idx_contratos_ativo',
                'sql': 'CREATE INDEX idx_contratos_ativo ON contratos(ativo, data_inicio) WHERE ativo = true;',
                'benefit': 'Índice parcial para listagem de contratos ativos',
                'estimated_improvement': '30-50%'
            },
            {
                'table': 'clientes',
                'index': 'idx_clientes_ativo',
                'sql': 'CREATE INDEX idx_clientes_ativo ON clientes(ativo, nome) WHERE ativo = true;',
                'benefit': 'Acelera listagem de clientes ativos',
                'estimated_improvement': '30-40%'
            }
        ]
        
        return jsonify({
            'success': True,
            'total_suggestions': len(suggestions),
            'suggestions': suggestions,
            'note': 'Execute os comandos SQL no banco de dados para criar os índices'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/reset-profiler', methods=['POST'])
@require_permission('admin')
def reset_profiler():
    """Reseta estatísticas do profiler"""
    try:
        profiler.reset()
        
        return jsonify({
            'success': True,
            'message': 'Profiler resetado com sucesso'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

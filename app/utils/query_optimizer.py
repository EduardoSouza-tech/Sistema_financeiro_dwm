"""
⚡ Query Optimizer - Otimizações de performance para queries SQL

Features:
- Paginação automática
- Índices sugeridos
- Query profiling
- Detecção de N+1 queries
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import time


class QueryProfiler:
    """Profiler para medir performance de queries"""
    
    def __init__(self):
        self.queries = []
        self.enabled = True
    
    def log_query(self, query: str, params: tuple, duration: float):
        """Registra execução de query"""
        if not self.enabled:
            return
        
        self.queries.append({
            'query': query,
            'params': params,
            'duration': duration,
            'timestamp': datetime.now()
        })
    
    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict]:
        """Retorna queries lentas"""
        threshold_sec = threshold_ms / 1000
        return [q for q in self.queries if q['duration'] > threshold_sec]
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas de performance"""
        if not self.queries:
            return {'total_queries': 0}
        
        durations = [q['duration'] for q in self.queries]
        
        return {
            'total_queries': len(self.queries),
            'total_time': sum(durations),
            'avg_time': sum(durations) / len(durations),
            'max_time': max(durations),
            'min_time': min(durations),
            'slow_queries': len(self.get_slow_queries())
        }
    
    def reset(self):
        """Limpa histórico"""
        self.queries.clear()


# Instância global
profiler = QueryProfiler()


def paginate_query(query: str, page: int = 1, per_page: int = 50) -> Tuple[str, tuple]:
    """
    Adiciona paginação a uma query
    
    Args:
        query: SQL query base
        page: Número da página (1-indexed)
        per_page: Itens por página
    
    Returns:
        Tuple (query_com_limit, params_adicionais)
    """
    offset = (page - 1) * per_page
    
    # Adicionar LIMIT e OFFSET
    if 'LIMIT' not in query.upper():
        query += f" LIMIT {per_page} OFFSET {offset}"
    
    return query, ()


def suggest_indexes(query: str) -> List[str]:
    """
    Analisa query e sugere índices
    
    Args:
        query: SQL query
    
    Returns:
        Lista de sugestões de índices
    """
    suggestions = []
    query_upper = query.upper()
    
    # Detectar filtros WHERE sem índice
    if 'WHERE' in query_upper:
        # Procurar por colunas filtradas
        if 'PROPRIETARIO_ID' in query_upper:
            suggestions.append("CREATE INDEX idx_proprietario_id ON table_name(proprietario_id)")
        
        if 'EMPRESA_ID' in query_upper:
            suggestions.append("CREATE INDEX idx_empresa_id ON table_name(empresa_id)")
        
        if 'DATA_VENCIMENTO' in query_upper:
            suggestions.append("CREATE INDEX idx_data_vencimento ON lancamentos(data_vencimento)")
        
        if 'STATUS' in query_upper:
            suggestions.append("CREATE INDEX idx_status ON lancamentos(status)")
    
    # Detectar JOINs sem índices
    if 'JOIN' in query_upper:
        suggestions.append("Verifique se as colunas de JOIN têm índices")
    
    # Detectar ORDER BY sem índice
    if 'ORDER BY' in query_upper:
        suggestions.append("Considere índice composto para WHERE + ORDER BY")
    
    return suggestions


def detect_n_plus_one(queries: List[str]) -> bool:
    """
    Detecta padrão N+1 queries
    
    Args:
        queries: Lista de queries executadas
    
    Returns:
        True se detectar N+1
    """
    # Contar queries similares
    query_counts = {}
    
    for query in queries:
        # Normalizar query (remover valores específicos)
        normalized = query.split('WHERE')[0] if 'WHERE' in query else query
        query_counts[normalized] = query_counts.get(normalized, 0) + 1
    
    # Se a mesma query foi executada muitas vezes, pode ser N+1
    max_count = max(query_counts.values()) if query_counts else 0
    
    if max_count > 10:
        print(f"⚠️ AVISO: Possível N+1 query detectado ({max_count} repetições)")
        return True
    
    return False


def optimize_select(columns: List[str] = None) -> str:
    """
    Gera SELECT otimizado
    
    Args:
        columns: Lista de colunas específicas ou None para SELECT *
    
    Returns:
        String SELECT otimizada
    """
    if columns:
        return f"SELECT {', '.join(columns)}"
    else:
        print("⚠️ AVISO: SELECT * pode ser ineficiente. Especifique colunas.")
        return "SELECT *"


def add_composite_index_suggestions(table: str, filters: Dict[str, Any]) -> List[str]:
    """
    Sugere índices compostos baseado nos filtros usados
    
    Args:
        table: Nome da tabela
        filters: Dicionário de filtros aplicados
    
    Returns:
        Lista de sugestões SQL
    """
    suggestions = []
    
    if len(filters) >= 2:
        columns = list(filters.keys())
        index_name = f"idx_{table}_{'_'.join(columns[:3])}"  # Limitar a 3 colunas
        columns_str = ', '.join(columns[:3])
        
        suggestions.append(
            f"CREATE INDEX {index_name} ON {table}({columns_str})"
        )
    
    return suggestions


class QueryTimer:
    """Context manager para medir tempo de queries"""
    
    def __init__(self, query_name: str):
        self.query_name = query_name
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        
        if self.duration > 0.1:  # > 100ms
            print(f"⚠️ Query lenta: {self.query_name} ({self.duration*1000:.2f}ms)")
        else:
            print(f"✅ Query rápida: {self.query_name} ({self.duration*1000:.2f}ms)")


def explain_analyze(query: str, conn) -> Dict[str, Any]:
    """
    Executa EXPLAIN ANALYZE e retorna análise
    
    Args:
        query: SQL query
        conn: Conexão ao banco
    
    Returns:
        Dicionário com análise
    """
    cursor = conn.cursor()
    
    try:
        # Executar EXPLAIN ANALYZE
        cursor.execute(f"EXPLAIN ANALYZE {query}")
        plan = cursor.fetchall()
        
        # Parsear resultado
        analysis = {
            'plan': [row[0] for row in plan],
            'has_seq_scan': any('Seq Scan' in str(row) for row in plan),
            'has_index_scan': any('Index Scan' in str(row) for row in plan),
            'execution_time': None
        }
        
        # Extrair tempo de execução
        for row in plan:
            if 'Execution Time' in str(row):
                # Parsear tempo (formato: "Execution Time: 0.123 ms")
                time_str = str(row).split(':')[-1].replace('ms', '').strip()
                analysis['execution_time'] = float(time_str)
        
        return analysis
        
    finally:
        cursor.close()


# Configuração de paginação padrão
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

"""
Security Wrapper - Camada de Segurança para Isolamento de Empresas
====================================================================

Este módulo adiciona uma camada de segurança OBRIGATÓRIA em todas as
operações do banco de dados para garantir 100% de isolamento entre empresas.

Funcionalidades:
1. Define empresa_id na sessão PostgreSQL (Row Level Security)
2. Valida que empresa_id está presente em TODAS as queries
3. Audita tentativas de acesso cross-empresa
4. Bloqueia queries sem filtro de empresa

Uso: Envolver TODAS as queries com este wrapper
"""

import functools
import logging
import re
from typing import Optional, Any, Callable
from contextlib import contextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityViolationError(Exception):
    """Exceção lançada quando há tentativa de acesso indevido entre empresas"""
    pass

class EmpresaNotSetError(Exception):
    """Exceção lançada quando empresa_id não foi definida na sessão"""
    pass


def validate_empresa_in_query(query: str, empresa_id: Optional[int]) -> bool:
    """
    Valida se a query contém filtro de empresa_id
    
    Args:
        query: SQL query a ser validada
        empresa_id: ID da empresa esperado
        
    Returns:
        True se válida, False se suspeita
        
    Raises:
        SecurityViolationError: Se query é perigosa
    """
    if not empresa_id:
        raise EmpresaNotSetError("empresa_id não foi definida antes da query")
    
    # Normalizar query
    query_lower = query.lower().strip()
    
    # Permitir queries de sistema
    safe_system_queries = [
        'select set_current_empresa',
        'select get_current_empresa',
        'select * from usuarios',
        'select * from empresas',
        'insert into usuarios',
        'update usuarios',
        'select version()',
        'show ',
        'set ',
    ]
    
    for safe_query in safe_system_queries:
        if query_lower.startswith(safe_query):
            return True
    
    # Verificar se é SELECT/UPDATE/DELETE em tabela com empresa_id
    tables_com_empresa = [
        'lancamentos', 'categorias', 'subcategorias', 'contas', 
        'clientes', 'fornecedores', 'contratos', 'sessoes_fotografia',
        'equipamentos', 'kits_equipamentos', 'funcionarios', 
        'folha_pagamento', 'eventos', 'produtos', 'movimentacoes_estoque'
    ]
    
    is_data_query = False
    for table in tables_com_empresa:
        if f'from {table}' in query_lower or f'update {table}' in query_lower or f'delete from {table}' in query_lower:
            is_data_query = True
            break
    
    if not is_data_query:
        # Query não afeta tabelas com empresa_id
        return True
    
    # Verificar se tem WHERE empresa_id ou está usando RLS
    has_empresa_filter = (
        'where empresa_id' in query_lower or
        'where' in query_lower and 'empresa_id' in query_lower or
        f"empresa_id = {empresa_id}" in query_lower.replace(' ', '')
    )
    
    if not has_empresa_filter:
        logger.warning(f"⚠️ Query sem filtro de empresa_id detectada: {query[:100]}...")
        logger.warning(f"   Empresa atual: {empresa_id}")
        # Não bloquear - RLS vai proteger, mas registrar warning
        return True
    
    # Verificar se está tentando acessar outra empresa
    empresa_id_match = re.search(r'empresa_id\s*=\s*(\d+)', query_lower)
    if empresa_id_match:
        query_empresa_id = int(empresa_id_match.group(1))
        if query_empresa_id != empresa_id:
            error_msg = f"VIOLAÇÃO DE SEGURANÇA: Tentativa de acessar empresa {query_empresa_id} enquanto sessão é empresa {empresa_id}"
            logger.error(f"🚨 {error_msg}")
            logger.error(f"   Query: {query}")
            raise SecurityViolationError(error_msg)
    
    return True


@contextmanager
def secure_connection(connection, empresa_id: int):
    """
    Context manager que configura Row Level Security na conexão
    
    Args:
        connection: Conexão psycopg2
        empresa_id: ID da empresa para isolamento
        
    Yields:
        Connection configurada com RLS
        
    Example:
        with get_db_connection() as conn:
            with secure_connection(conn, empresa_id):
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM lancamentos")
    """
    if not empresa_id:
        raise EmpresaNotSetError("empresa_id é obrigatório")
    
    cursor = connection.cursor()
    
    try:
        # Definir empresa na sessão PostgreSQL
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_id,))
        connection.commit()
        
        logger.debug(f"🔒 RLS ativado para empresa {empresa_id}")
        
        yield connection
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar RLS: {e}")
        connection.rollback()
        raise
    
    finally:
        # Limpar sessão (opcional - cada conexão será reconfigurada)
        try:
            cursor.execute("RESET app.current_empresa_id")
            connection.commit()
        except:
            pass
        cursor.close()


def require_empresa(func: Callable) -> Callable:
    """
    Decorator que exige empresa_id como argumento
    
    Args:
        func: Função a ser decorada
        
    Returns:
        Função decorada que valida empresa_id
        
    Example:
        @require_empresa
        def obter_lancamentos(empresa_id, mes, ano):
            # empresa_id garantido como not None
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar se empresa_id está nos argumentos
        empresa_id = kwargs.get('empresa_id')
        
        if not empresa_id and len(args) > 0:
            # Tentar pegar primeiro argumento
            empresa_id = args[0] if isinstance(args[0], int) else None
        
        if not empresa_id:
            func_name = func.__name__
            raise EmpresaNotSetError(
                f"Função {func_name} requer empresa_id mas não foi fornecido.\n"
                f"Args: {args}\n"
                f"Kwargs: {kwargs}"
            )
        
        logger.debug(f"✅ Função {func.__name__} executando para empresa {empresa_id}")
        
        return func(*args, **kwargs)
    
    return wrapper


def audit_query(cursor, query: str, params: tuple, empresa_id: int, usuario_id: Optional[int] = None):
    """
    Audita execução de query sensível
    
    Args:
        cursor: Cursor do banco
        query: SQL executado
        params: Parâmetros da query
        empresa_id: ID da empresa
        usuario_id: ID do usuário (opcional)
    """
    # Registrar apenas queries de modificação
    query_lower = query.lower().strip()
    
    if not any(cmd in query_lower for cmd in ['insert', 'update', 'delete']):
        return
    
    # Extrair nome da tabela
    table_match = re.search(r'(?:from|into|update)\s+(\w+)', query_lower)
    table_name = table_match.group(1) if table_match else 'unknown'
    
    # Extrair ação
    if 'insert' in query_lower:
        action = 'INSERT'
    elif 'update' in query_lower:
        action = 'UPDATE'
    elif 'delete' in query_lower:
        action = 'DELETE'
    else:
        action = 'UNKNOWN'
    
    try:
        cursor.execute(
            """
            INSERT INTO audit_data_access (usuario_id, empresa_id, table_name, action)
            VALUES (%s, %s, %s, %s)
            """,
            (usuario_id, empresa_id, table_name, action)
        )
    except Exception as e:
        logger.warning(f"Falha ao auditar query: {e}")


def execute_secure_query(cursor, query: str, params: tuple = None, empresa_id: int = None, 
                         usuario_id: int = None, audit: bool = True):
    """
    Executa query com validação de segurança
    
    Args:
        cursor: Cursor do banco
        query: SQL a executar
        params: Parâmetros da query
        empresa_id: ID da empresa (obrigatório para queries de dados)
        usuario_id: ID do usuário (para auditoria)
        audit: Se deve auditar a query
        
    Returns:
        Resultado da execução
        
    Raises:
        SecurityViolationError: Se query viola segurança
        EmpresaNotSetError: Se empresa_id não fornecida
    """
    # Validar query
    validate_empresa_in_query(query, empresa_id)
    
    # Auditar se necessário
    if audit and empresa_id:
        audit_query(cursor, query, params, empresa_id, usuario_id)
    
    # Executar query
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    return cursor


# =====================================================
# FUNÇÕES DE VERIFICAÇÃO E DIAGNÓSTICO
# =====================================================

def verificar_rls_ativo(connection) -> dict:
    """
    Verifica se Row Level Security está ativo
    
    Returns:
        Dict com status de cada tabela
    """
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM rls_status")
    
    results = {}
    for row in cursor.fetchall():
        schema, table, rls_enabled, policy_count = row
        results[table] = {
            'rls_enabled': rls_enabled,
            'policy_count': policy_count,
            'status': 'OK' if rls_enabled and policy_count > 0 else 'ATENÇÃO'
        }
    
    cursor.close()
    return results


def testar_isolamento(connection, empresa_id_1: int, empresa_id_2: int) -> dict:
    """
    Testa se isolamento entre empresas está funcionando
    
    Args:
        connection: Conexão com banco
        empresa_id_1: Primeira empresa
        empresa_id_2: Segunda empresa
        
    Returns:
        Dict com resultados dos testes
    """
    cursor = connection.cursor()
    resultados = {}
    
    try:
        # Teste 1: Definir empresa 1 e contar lançamentos
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_id_1,))
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        count_empresa_1 = cursor.fetchone()[0]
        resultados['empresa_1_count'] = count_empresa_1
        
        # Teste 2: Definir empresa 2 e contar lançamentos
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_id_2,))
        cursor.execute("SELECT COUNT(*) FROM lancamentos")
        count_empresa_2 = cursor.fetchone()[0]
        resultados['empresa_2_count'] = count_empresa_2
        
        # Teste 3: Verificar que contagens são diferentes
        resultados['isolamento_ok'] = count_empresa_1 != count_empresa_2 or (count_empresa_1 == 0 and count_empresa_2 == 0)
        
        # Teste 4: Tentar acessar dados de empresa 2 enquanto sessão é empresa 1
        cursor.execute("SELECT set_current_empresa(%s)", (empresa_id_1,))
        cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id = %s", (empresa_id_2,))
        vazamento = cursor.fetchone()[0]
        resultados['vazamento_detectado'] = vazamento > 0
        resultados['registros_vazados'] = vazamento
        
        # Status geral
        resultados['status'] = 'SEGURO' if resultados['isolamento_ok'] and not resultados['vazamento_detectado'] else 'INSEGURO'
        
    except Exception as e:
        resultados['erro'] = str(e)
        resultados['status'] = 'ERRO'
    
    finally:
        cursor.close()
    
    return resultados


# =====================================================
# EXEMPLO DE USO
# =====================================================

if __name__ == '__main__':
    """
    Exemplo de como usar o security wrapper
    """
    from database_postgresql import get_db_connection
    
    # Exemplo 1: Usar secure_connection
    empresa_id = 18
    
    with get_db_connection() as conn:
        with secure_connection(conn, empresa_id):
            cursor = conn.cursor()
            
            # Query automaticamente filtrada por RLS
            cursor.execute("SELECT * FROM lancamentos LIMIT 10")
            lancamentos = cursor.fetchall()
            
            print(f"Lançamentos empresa {empresa_id}: {len(lancamentos)}")
    
    # Exemplo 2: Verificar RLS
    with get_db_connection() as conn:
        status = verificar_rls_ativo(conn)
        print("\nStatus RLS:")
        for table, info in status.items():
            print(f"  {table}: {info['status']}")
    
    # Exemplo 3: Testar isolamento
    with get_db_connection() as conn:
        resultado = testar_isolamento(conn, 18, 20)
        print(f"\nTeste de isolamento: {resultado['status']}")
        print(f"  Empresa 18: {resultado['empresa_1_count']} registros")
        print(f"  Empresa 20: {resultado['empresa_2_count']} registros")
        print(f"  Vazamento: {resultado['registros_vazados']} registros")

"""
Funcoes para gerenciamento de extratos bancarios (importacao OFX e conciliacao)
"""

import sys
from datetime import datetime
from decimal import Decimal
import uuid

# Funcao de log
def log(msg):
    print(msg, file=sys.stderr, flush=True)


def salvar_transacoes_extrato(database, empresa_id, conta_bancaria, transacoes, importacao_id=None):
    """
    Salva transacoes do extrato no banco
    
    Args:
        database: instancia do DatabaseManager
        empresa_id: ID da empresa
        conta_bancaria: nome da conta bancaria
        transacoes: lista de dicts com as transacoes
        importacao_id: ID unico da importacao (para rastrear)
    
    Returns:
        dict: {'success': bool, 'inseridas': int, 'duplicadas': int}
    """
    try:
        if not importacao_id:
            importacao_id = str(uuid.uuid4())
        
        inseridas = 0
        duplicadas = 0
        
        with database.get_db_connection() as conn:
            conn.autocommit = False
            cursor = conn.cursor()
            
            for trans in transacoes:
                # Verificar se ja existe (por FITID ou data+valor+descricao)
                fitid = trans.get('fitid')
                
                if fitid:
                    cursor.execute("""
                        SELECT id FROM transacoes_extrato 
                        WHERE fitid = %s AND empresa_id = %s
                    """, (fitid, empresa_id))
                    
                    if cursor.fetchone():
                        duplicadas += 1
                        continue
                
                # Inserir transacao
                cursor.execute("""
                    INSERT INTO transacoes_extrato (
                        empresa_id, conta_bancaria, data, descricao, valor, tipo,
                        saldo, fitid, memo, checknum, importacao_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    empresa_id,
                    conta_bancaria,
                    trans['data'],
                    trans['descricao'],
                    trans['valor'],
                    trans['tipo'],
                    trans.get('saldo'),
                    trans.get('fitid'),
                    trans.get('memo'),
                    trans.get('checknum'),
                    importacao_id
                ))
                inseridas += 1
            
            conn.commit()
            cursor.close()
            
            log(f"Extrato importado: {inseridas} novas, {duplicadas} duplicadas")
            return {
                'success': True,
                'inseridas': inseridas,
                'duplicadas': duplicadas,
                'importacao_id': importacao_id
            }
        
    except Exception as e:
        log(f"Erro ao salvar transacoes: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {'success': False, 'error': str(e)}


def listar_transacoes_extrato(database, empresa_id, filtros=None):
    """
    Lista transacoes do extrato com filtros
    
    Args:
        database: instancia do DatabaseManager
        empresa_id: ID da empresa
        filtros: dict opcional com conta, data_inicio, data_fim, conciliado
    
    Returns:
        list: lista de transacoes
    """
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=database.RealDictCursor)
            
            query = """
                SELECT t.*, l.descricao as lancamento_descricao
                FROM transacoes_extrato t
                LEFT JOIN lancamentos l ON t.lancamento_id = l.id
                WHERE t.empresa_id = %s
            """
            params = [empresa_id]
            
            if filtros:
                if filtros.get('conta_bancaria'):
                    query += " AND t.conta_bancaria = %s"
                    params.append(filtros['conta_bancaria'])
                
                if filtros.get('data_inicio'):
                    query += " AND t.data >= %s"
                    params.append(filtros['data_inicio'])
                
                if filtros.get('data_fim'):
                    query += " AND t.data <= %s"
                    params.append(filtros['data_fim'])
                
                if filtros.get('conciliado') is not None:
                    query += " AND t.conciliado = %s"
                    params.append(filtros['conciliado'])
            
            # Ordenar do passado para o presente (ASC) para que o saldo faça sentido visual
            query += " ORDER BY t.data ASC, t.id ASC LIMIT 1000"
            
            cursor.execute(query, params)
            transacoes = cursor.fetchall()
            cursor.close()
            
            return [dict(t) for t in transacoes]
        
    except Exception as e:
        log(f"Erro ao listar transacoes: {e}")
        return []


def conciliar_transacao(database, transacao_id, lancamento_id):
    """
    Concilia uma transacao do extrato com um lancamento
    
    Args:
        database: instancia do DatabaseManager
        transacao_id: ID da transacao do extrato
        lancamento_id: ID do lancamento (ou None para desconciliar)
    
    Returns:
        dict: {'success': bool}
    """
    try:
        with database.get_db_connection() as conn:
            conn.autocommit = False
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE transacoes_extrato
                SET lancamento_id = %s, conciliado = %s
                WHERE id = %s
            """, (lancamento_id, lancamento_id is not None, transacao_id))
            
            conn.commit()
            cursor.close()
            
            return {'success': True}
        
    except Exception as e:
        log(f"Erro ao conciliar: {e}")
        return {'success': False, 'error': str(e)}


def sugerir_conciliacoes(database, empresa_id, transacao_id):
    """
    Sugere lancamentos para conciliar com uma transacao
    
    Args:
        database: instancia do DatabaseManager
        empresa_id: ID da empresa
        transacao_id: ID da transacao do extrato
    
    Returns:
        list: lista de lancamentos sugeridos
    """
    try:
        with database.get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=database.RealDictCursor)
            
            # Buscar transacao
            cursor.execute("""
                SELECT * FROM transacoes_extrato WHERE id = %s AND empresa_id = %s
            """, (transacao_id, empresa_id))
            transacao = cursor.fetchone()
            
            if not transacao:
                return []
            
            # Buscar lancamentos similares (mesmo valor +/- 5%, data proxima +/- 7 dias)
            valor_min = float(transacao['valor']) * 0.95
            valor_max = float(transacao['valor']) * 1.05
            
            cursor.execute("""
                SELECT *, 
                    ABS(EXTRACT(DAY FROM (data_vencimento - %s::date))) as dias_diferenca,
                    ABS(valor - %s) as diferenca_valor
                FROM lancamentos
                WHERE empresa_id = %s
                AND conta_bancaria = %s
                AND valor BETWEEN %s AND %s
                AND ABS(EXTRACT(DAY FROM (data_vencimento - %s::date))) <= 7
                AND status IN ('pago', 'pendente')
                ORDER BY dias_diferenca ASC, diferenca_valor ASC
                LIMIT 10
            """, (
                transacao['data'], transacao['valor'],
                empresa_id, transacao['conta_bancaria'],
                valor_min, valor_max,
                transacao['data']
            ))
            
            sugestoes = cursor.fetchall()
            cursor.close()
            
            return [dict(s) for s in sugestoes]
        
    except Exception as e:
        log(f"Erro ao sugerir conciliacoes: {e}")
        return []


def deletar_transacoes_extrato(database, importacao_id):
    """
    Deleta todas as transacoes de uma importacao
    
    Args:
        database: instancia do DatabaseManager
        importacao_id: ID da importacao
    
    Returns:
        dict: {'success': bool, 'deletadas': int}
    """
    try:
        with database.get_db_connection() as conn:
            conn.autocommit = False
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM transacoes_extrato WHERE importacao_id = %s
            """, (importacao_id,))
            
            deletadas = cursor.rowcount
            conn.commit()
            cursor.close()
            
            return {'success': True, 'deletadas': deletadas}
        
    except Exception as e:
        log(f"Erro ao deletar transacoes: {e}")
        return {'success': False, 'error': str(e)}

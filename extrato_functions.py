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
        
        # 🔒 Passar empresa_id para RLS
        with database.get_db_connection(empresa_id=empresa_id) as conn:
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
        dict: {'transacoes': list, 'saldo_anterior': float}
    """
    try:
        log(f"🔍 listar_transacoes_extrato: empresa_id={empresa_id}, filtros={filtros}")
        
        # 🔒 Passar empresa_id para RLS
        log(f"🔍 Tentando obter conexão com empresa_id={empresa_id}")
        with database.get_db_connection(empresa_id=empresa_id) as conn:
            log(f"✅ Conexão obtida com sucesso!")
            cursor = conn.cursor(cursor_factory=database.RealDictCursor)
            
            # 🏦 CALCULAR SALDO ANTERIOR dinamicamente (imune a valores armazenados incorretos)
            # ESTRATÉGIA: saldo_inicial_conta + SUM(transacoes desde data_inicio_conta até data_filtro)
            # Isso é correto mesmo quando o campo 'saldo' armazenado foi calculado errado
            # (ex: OFX com transações fake como "SALDO ANTERIOR" ou data_inicio errada na conta)
            saldo_anterior = None
            data_inicio_filtro = filtros.get('data_inicio') if filtros else None

            if data_inicio_filtro:
                conta_bancaria_filtro = filtros.get('conta_bancaria') if filtros else None
                saldo_base = 0.0
                data_base = None

                # 1) Obter saldo_inicial e data_inicio da conta (se filtro por conta específica)
                if conta_bancaria_filtro:
                    cursor.execute("""
                        SELECT saldo_inicial, data_inicio
                        FROM contas_bancarias
                        WHERE empresa_id = %s AND nome = %s
                        LIMIT 1
                    """, (empresa_id, conta_bancaria_filtro))
                    conta_row = cursor.fetchone()
                    if conta_row:
                        saldo_base = float(conta_row['saldo_inicial'] or 0)
                        data_base = conta_row['data_inicio']
                        log(f"🏦 Conta encontrada: saldo_inicial={saldo_base}, data_inicio={data_base}")

                # 2) Somar transações: desde data_base (ou all-time) até data_filtro
                query_soma = """
                    SELECT COALESCE(SUM(valor), 0) AS soma
                    FROM transacoes_extrato
                    WHERE empresa_id = %s
                      AND data < %s
                """
                params_soma = [empresa_id, data_inicio_filtro]

                if conta_bancaria_filtro:
                    query_soma += " AND conta_bancaria = %s"
                    params_soma.append(conta_bancaria_filtro)

                # Só somar transações desde a data_inicio da conta (a partir de quando o saldo_inicial vale)
                if data_base:
                    query_soma += " AND data >= %s"
                    params_soma.append(data_base)

                cursor.execute(query_soma, params_soma)
                soma_row = cursor.fetchone()
                soma_anterior = float((soma_row['soma'] if isinstance(soma_row, dict) else soma_row[0]) or 0)

                saldo_anterior = saldo_base + soma_anterior
                log(f"🏦 Saldo anterior calculado: {saldo_base} (base) + {soma_anterior:.2f} (soma) = R$ {saldo_anterior:,.2f}")
            
            # Query principal de transações
            # Usar tabela conciliacoes para verificar conciliação
            query = """
                SELECT t.*, 
                       c.lancamento_id,
                       l.descricao as lancamento_descricao
                FROM transacoes_extrato t
                LEFT JOIN conciliacoes c ON c.transacao_extrato_id = t.id AND c.empresa_id = t.empresa_id
                LEFT JOIN lancamentos l ON l.id = c.lancamento_id AND l.empresa_id = t.empresa_id
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
            
            log(f"📊 Executando query: {query}")
            log(f"📊 Parâmetros: {params}")
            
            cursor.execute(query, params)
            transacoes = cursor.fetchall()
            
            log(f"📊 Query retornou {len(transacoes)} transação(ões)")
            
            cursor.close()
            
            # Converter date/datetime/Decimal para tipos JSON-safe
            result = []
            for t in transacoes:
                d = dict(t)
                for key, val in d.items():
                    if hasattr(val, 'isoformat'):
                        d[key] = val.isoformat()
                    elif isinstance(val, Decimal):
                        d[key] = float(val)
                result.append(d)
            
            log(f"✅ Retornando {len(result)} transação(ões) para o frontend")
            
            return {
                'transacoes': result,
                'saldo_anterior': saldo_anterior
            }
        
    except Exception as e:
        log(f"❌ ERRO ao listar transacoes: {e}")
        import traceback
        log(traceback.format_exc())
        return {'transacoes': [], 'saldo_anterior': None}


def conciliar_transacao(database, empresa_id, transacao_id, lancamento_id):
    """
    Concilia uma transacao do extrato com um lancamento
    
    NOVO COMPORTAMENTO (2026-02-26):
    - Se lancamento_id fornecido: Associa transação ao lançamento existente
    - Se lancamento_id = 'auto' ou None: Cria novo lançamento automaticamente
    - Sempre marca lançamento como status='PAGO' após conciliação
    
    Args:
        database: instancia do DatabaseManager
        empresa_id: ID da empresa [OBRIGATÓRIO]
        transacao_id: ID da transacao do extrato
        lancamento_id: ID do lancamento, 'auto' para criar, ou None para desconciliar
    
    Returns:
        dict: {'success': bool, 'lancamento_id': int (se criado)}
        
    Security:
        🔒 RLS aplicado via empresa_id
    """
    from datetime import date
    from decimal import Decimal
    
    try:
        # 🔒 Passar empresa_id para RLS
        with database.get_db_connection(empresa_id=empresa_id) as conn:
            conn.autocommit = False
            cursor = conn.cursor(cursor_factory=database.RealDictCursor)
            
            if lancamento_id is None or str(lancamento_id).lower() == 'none':
                # DESCONCILIAR: Deletar da tabela conciliacoes e voltar status para PENDENTE
                cursor.execute("""
                    DELETE FROM conciliacoes
                    WHERE transacao_extrato_id = %s AND empresa_id = %s
                    RETURNING lancamento_id
                """, (transacao_id, empresa_id))
                
                deleted = cursor.fetchone()
                if deleted:
                    # Voltar lançamento para PENDENTE
                    cursor.execute("""
                        UPDATE lancamentos
                        SET status = 'pendente', data_pagamento = NULL
                        WHERE id = %s AND empresa_id = %s
                    """, (deleted['lancamento_id'], empresa_id))
                    log(f"✅ Lançamento {deleted['lancamento_id']} voltou para PENDENTE")
                
                # Atualizar flag conciliado em transacoes_extrato
                cursor.execute("""
                    UPDATE transacoes_extrato
                    SET conciliado = FALSE
                    WHERE id = %s AND empresa_id = %s
                """, (transacao_id, empresa_id))
                
                conn.commit()
                cursor.close()
                log(f"✅ Transação {transacao_id} desconciliada com sucesso")
                return {'success': True}
                
            else:
                # CRIAR LANÇAMENTO AUTOMATICAMENTE se lancamento_id = 'auto'
                if str(lancamento_id).lower() == 'auto':
                    # Buscar dados da transação do extrato
                    cursor.execute("""
                        SELECT * FROM transacoes_extrato 
                        WHERE id = %s AND empresa_id = %s
                    """, (transacao_id, empresa_id))
                    
                    transacao = cursor.fetchone()
                    if not transacao:
                        conn.rollback()
                        cursor.close()
                        return {'success': False, 'error': 'Transação não encontrada'}
                    
                    # Determinar tipo (débito = despesa, crédito = receita)
                    # Aceita DÉBITO/DEBITO e CRÉDITO/CREDITO; fallback pelo sinal do valor
                    tipo_transacao = (transacao['tipo'] or '').upper()
                    valor_float = float(transacao['valor'] or 0)
                    if tipo_transacao in ('DÉBITO', 'DEBITO'):
                        tipo = 'despesa'
                    elif tipo_transacao in ('CRÉDITO', 'CREDITO'):
                        tipo = 'receita'
                    else:
                        # Tipo desconhecido: usar sinal do valor como desempate
                        tipo = 'receita' if valor_float >= 0 else 'despesa'
                        log(f"⚠️ Tipo desconhecido '{transacao['tipo']}' para transação {transacao_id} — usando sinal do valor ({valor_float:.2f} → {tipo})")
                    valor_abs = abs(valor_float)
                    
                    # Criar novo lançamento (copiando categoria, subcategoria e pessoa da transação)
                    cursor.execute("""
                        INSERT INTO lancamentos (
                            empresa_id, tipo, descricao, valor, 
                            data_vencimento, data_pagamento, status,
                            conta_bancaria, categoria, subcategoria, pessoa, observacoes
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s, 'pago',
                            %s, %s, %s, %s, %s
                        )
                        RETURNING id
                    """, (
                        empresa_id,
                        tipo,
                        transacao['descricao'] or 'Lançamento criado automaticamente via conciliação',
                        valor_abs,
                        transacao['data'],
                        transacao['data'],  # data_pagamento = data da transação
                        transacao['conta_bancaria'],
                        transacao.get('categoria') or 'Conciliação Bancária',  # categoria da transação ou padrão
                        transacao.get('subcategoria'),  # subcategoria da transação (pode ser None)
                        transacao.get('pessoa'),  # pessoa da transação (pode ser None)
                        f"Criado automaticamente pela conciliação com transação #{transacao_id}"
                    ))
                    
                    novo_lancamento = cursor.fetchone()
                    lancamento_id = novo_lancamento['id']
                    log(f"✅ Novo lançamento #{lancamento_id} criado automaticamente (tipo: {tipo}, valor: R$ {valor_abs:.2f})")
                
                # CONCILIAR: Inserir ou atualizar na tabela conciliacoes
                cursor.execute("""
                    INSERT INTO conciliacoes (
                        empresa_id, transacao_extrato_id, lancamento_id
                    ) VALUES (%s, %s, %s)
                    ON CONFLICT (transacao_extrato_id) 
                    DO UPDATE SET 
                        lancamento_id = EXCLUDED.lancamento_id,
                        data_conciliacao = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                """, (empresa_id, transacao_id, lancamento_id))

                # ✅ CORRIGIR TIPO DO LANÇAMENTO se diverge do extrato (DEBITO→despesa, CREDITO→receita)
                # Isso garante que um lançamento "receita" vinculado a DÉBITO seja corrigido para "despesa"
                cursor.execute(
                    "SELECT tipo, valor FROM transacoes_extrato WHERE id = %s AND empresa_id = %s",
                    (transacao_id, empresa_id)
                )
                te_row = cursor.fetchone()
                if te_row:
                    te_tipo_raw = (te_row['tipo'] or '').upper()
                    if te_tipo_raw in ('DÉBITO', 'DEBITO'):
                        tipo_correto = 'despesa'
                    elif te_tipo_raw in ('CRÉDITO', 'CREDITO'):
                        tipo_correto = 'receita'
                    else:
                        # Fallback: sinal do valor (negativo = débito)
                        valor_te = float(te_row['valor'] or 0)
                        tipo_correto = 'despesa' if valor_te < 0 else 'receita'
                    cursor.execute(
                        "UPDATE lancamentos SET tipo = %s "
                        "WHERE id = %s AND empresa_id = %s AND tipo != %s",
                        (tipo_correto, lancamento_id, empresa_id, tipo_correto)
                    )
                    if cursor.rowcount > 0:
                        log(f"⚠️  Tipo do lançamento #{lancamento_id} CORRIGIDO para '{tipo_correto}' "
                            f"(extrato tipo: '{te_tipo_raw}')")

                # ✅ MARCAR LANÇAMENTO COMO PAGO (requisito do usuário)
                cursor.execute("""
                    UPDATE lancamentos
                    SET status = 'pago',
                        data_pagamento = COALESCE(data_pagamento, (SELECT data FROM transacoes_extrato WHERE id = %s))
                    WHERE id = %s AND empresa_id = %s
                """, (transacao_id, lancamento_id, empresa_id))
                
                log(f"✅ Lançamento #{lancamento_id} marcado como PAGO")
                
                # Atualizar flag conciliado em transacoes_extrato
                cursor.execute("""
                    UPDATE transacoes_extrato
                    SET conciliado = TRUE
                    WHERE id = %s AND empresa_id = %s
                """, (transacao_id, empresa_id))
                
                conn.commit()
                cursor.close()
                
                log(f"✅ Conciliação bem-sucedida: transação #{transacao_id} ↔ lançamento #{lancamento_id}")
                return {'success': True, 'lancamento_id': lancamento_id}
        
    except Exception as e:
        log(f"❌ Erro ao conciliar: {e}")
        import traceback
        log(traceback.format_exc())
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
        # 🔒 Passar empresa_id para RLS
        with database.get_db_connection(empresa_id=empresa_id) as conn:
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
            
            result = []
            for s in sugestoes:
                d = dict(s)
                for key, val in d.items():
                    if hasattr(val, 'isoformat'):
                        d[key] = val.isoformat()
                    elif isinstance(val, Decimal):
                        d[key] = float(val)
                result.append(d)
            return result
        
    except Exception as e:
        log(f"Erro ao sugerir conciliacoes: {e}")
        return []


def deletar_transacoes_extrato(database, empresa_id, importacao_id):
    """
    Deleta todas as transacoes de uma importacao
    
    Args:
        database: instancia do DatabaseManager
        empresa_id: ID da empresa [OBRIGATÓRIO]
        importacao_id: ID da importacao
    
    Returns:
        dict: {'success': bool, 'deletadas': int}
        
    Security:
        🔒 RLS aplicado via empresa_id
    """
    try:
        # 🔒 Passar empresa_id para RLS
        with database.get_db_connection(empresa_id=empresa_id) as conn:
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

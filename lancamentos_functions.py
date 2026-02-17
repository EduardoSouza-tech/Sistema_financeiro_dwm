#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANÇAMENTOS CONTÁBEIS - FUNÇÕES BACKEND
FASE 2 - Speed Integration
Data: 17/02/2026

Gerenciamento de lançamentos contábeis com partidas dobradas.
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


def criar_lancamento(
    conn,
    empresa_id: int,
    data_lancamento: date,
    historico: str,
    itens: List[Dict],
    tipo_lancamento: str = 'manual',
    origem: Optional[str] = None,
    origem_id: Optional[int] = None,
    versao_plano_id: Optional[int] = None,
    observacoes: Optional[str] = None,
    created_by: Optional[int] = None
) -> Dict:
    """
    Cria um novo lançamento contábil com partidas dobradas.
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_lancamento: Data do lançamento
        historico: Histórico principal
        itens: Lista de dicionários com débitos e créditos
               [{'plano_contas_id': 1, 'tipo': 'debito', 'valor': 100.00, ...}]
        tipo_lancamento: 'manual', 'automatico', 'importado'
        origem: Origem do lançamento ('conta_pagar', 'conta_receber', etc)
        origem_id: ID da transação de origem
        versao_plano_id: ID da versão do plano de contas
        observacoes: Observações adicionais
        created_by: ID do usuário que criou
    
    Returns:
        Dict com o lançamento criado
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Validar partidas dobradas
        total_debito = sum(Decimal(str(i['valor'])) for i in itens if i['tipo'] == 'debito')
        total_credito = sum(Decimal(str(i['valor'])) for i in itens if i['tipo'] == 'credito')
        
        if total_debito != total_credito:
            raise ValueError(f"Partidas não estão dobradas! Débito: {total_debito}, Crédito: {total_credito}")
        
        if len(itens) < 2:
            raise ValueError("Lançamento deve ter pelo menos 2 itens (débito e crédito)")
        
        # Gerar número sequencial do lançamento
        cur.execute("SELECT nextval('seq_numero_lancamento')")
        numero_lancamento = f"LC{cur.fetchone()['nextval']:06d}"
        
        # Inserir cabeçalho do lançamento
        cur.execute("""
            INSERT INTO lancamentos_contabeis (
                empresa_id, versao_plano_id, numero_lancamento, data_lancamento,
                historico, tipo_lancamento, origem, origem_id, valor_total,
                observacoes, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, numero_lancamento, created_at
        """, (
            empresa_id, versao_plano_id, numero_lancamento, data_lancamento,
            historico, tipo_lancamento, origem, origem_id, total_debito,
            observacoes, created_by
        ))
        
        lancamento = cur.fetchone()
        lancamento_id = lancamento['id']
        
        # Inserir itens (débitos e créditos)
        itens_criados = []
        for item in itens:
            cur.execute("""
                INSERT INTO lancamentos_contabeis_itens (
                    lancamento_id, plano_contas_id, tipo, valor,
                    historico_complementar, centro_custo
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                RETURNING id, tipo, valor
            """, (
                lancamento_id,
                item['plano_contas_id'],
                item['tipo'],
                item['valor'],
                item.get('historico_complementar'),
                item.get('centro_custo')
            ))
            itens_criados.append(dict(cur.fetchone()))
        
        conn.commit()
        
        return {
            'success': True,
            'lancamento_id': lancamento_id,
            'numero_lancamento': lancamento['numero_lancamento'],
            'data_lancamento': data_lancamento.isoformat(),
            'valor_total': float(total_debito),
            'total_debito': float(total_debito),
            'total_credito': float(total_credito),
            'itens': itens_criados,
            'created_at': lancamento['created_at'].isoformat() if lancamento['created_at'] else None
        }
        
    except ValueError as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    except psycopg2.Error as e:
        conn.rollback()
        return {'success': False, 'error': f"Erro no banco: {e.pgerror}"}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def listar_lancamentos(
    conn,
    empresa_id: int,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    tipo_lancamento: Optional[str] = None,
    origem: Optional[str] = None,
    busca: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """
    Lista lançamentos contábeis com filtros.
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_inicio: Data inicial do filtro
        data_fim: Data final do filtro
        tipo_lancamento: Filtrar por tipo ('manual', 'automatico', 'importado')
        origem: Filtrar por origem ('conta_pagar', 'conta_receber', etc)
        busca: Busca por número ou histórico
        limit: Limite de registros
        offset: Offset para paginação
    
    Returns:
        Dict com lista de lançamentos
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Construir query base
        query = """
            SELECT 
                lc.id,
                lc.numero_lancamento,
                lc.data_lancamento,
                lc.historico,
                lc.tipo_lancamento,
                lc.origem,
                lc.origem_id,
                lc.valor_total,
                lc.is_estornado,
                lc.observacoes,
                lc.created_at,
                u.username AS criado_por,
                COUNT(lci.id) AS total_itens,
                SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END) AS total_debito,
                SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END) AS total_credito
            FROM lancamentos_contabeis lc
            LEFT JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            LEFT JOIN usuarios u ON u.id = lc.created_by
            WHERE lc.empresa_id = %s
        """
        
        params = [empresa_id]
        
        # Aplicar filtros
        if data_inicio:
            query += " AND lc.data_lancamento >= %s"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND lc.data_lancamento <= %s"
            params.append(data_fim)
        
        if tipo_lancamento:
            query += " AND lc.tipo_lancamento = %s"
            params.append(tipo_lancamento)
        
        if origem:
            query += " AND lc.origem = %s"
            params.append(origem)
        
        if busca:
            query += " AND (lc.numero_lancamento ILIKE %s OR lc.historico ILIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        
        # Agrupar e ordenar
        query += """
            GROUP BY lc.id, u.username
            ORDER BY lc.data_lancamento DESC, lc.numero_lancamento DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cur.execute(query, params)
        lancamentos = [dict(row) for row in cur.fetchall()]
        
        # Converter datas para string
        for lanc in lancamentos:
            if lanc['data_lancamento']:
                lanc['data_lancamento'] = lanc['data_lancamento'].isoformat()
            if lanc['created_at']:
                lanc['created_at'] = lanc['created_at'].isoformat()
            # Converter Decimal para float
            for key in ['valor_total', 'total_debito', 'total_credito']:
                if lanc.get(key) is not None:
                    lanc[key] = float(lanc[key])
        
        # Contar total de registros
        cur.execute("""
            SELECT COUNT(DISTINCT lc.id)
            FROM lancamentos_contabeis lc
            WHERE lc.empresa_id = %s
        """, [empresa_id])
        total = cur.fetchone()['count']
        
        return {
            'success': True,
            'lancamentos': lancamentos,
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def obter_lancamento_detalhado(conn, lancamento_id: int, empresa_id: int) -> Dict:
    """
    Obtém detalhes completos de um lançamento, incluindo todos os itens.
    
    Args:
        conn: Conexão com o banco
        lancamento_id: ID do lançamento
        empresa_id: ID da empresa (para segurança)
    
    Returns:
        Dict com lançamento e itens
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Buscar cabeçalho
        cur.execute("""
            SELECT 
                lc.*,
                u.username AS criado_por
            FROM lancamentos_contabeis lc
            LEFT JOIN usuarios u ON u.id = lc.created_by
            WHERE lc.id = %s AND lc.empresa_id = %s
        """, (lancamento_id, empresa_id))
        
        lancamento = cur.fetchone()
        if not lancamento:
            return {'success': False, 'error': 'Lançamento não encontrado'}
        
        lancamento = dict(lancamento)
        
        # Converter datas
        if lancamento['data_lancamento']:
            lancamento['data_lancamento'] = lancamento['data_lancamento'].isoformat()
        if lancamento['created_at']:
            lancamento['created_at'] = lancamento['created_at'].isoformat()
        if lancamento['updated_at']:
            lancamento['updated_at'] = lancamento['updated_at'].isoformat()
        
        # Converter Decimal para float
        if lancamento.get('valor_total'):
            lancamento['valor_total'] = float(lancamento['valor_total'])
        
        # Buscar itens
        cur.execute("""
            SELECT 
                lci.id,
                lci.tipo,
                lci.valor,
                lci.historico_complementar,
                lci.centro_custo,
                pc.id AS plano_contas_id,
                pc.codigo AS conta_codigo,
                pc.descricao AS conta_nome,
                pc.classificacao AS conta_classificacao
            FROM lancamentos_contabeis_itens lci
            INNER JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            WHERE lci.lancamento_id = %s
            ORDER BY lci.tipo DESC, lci.id
        """, (lancamento_id,))
        
        itens = [dict(row) for row in cur.fetchall()]
        
        # Converter valores
        for item in itens:
            item['valor'] = float(item['valor'])
        
        lancamento['itens'] = itens
        
        return {
            'success': True,
            'lancamento': lancamento
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def estornar_lancamento(
    conn,
    lancamento_id: int,
    empresa_id: int,
    historico_estorno: str,
    created_by: Optional[int] = None
) -> Dict:
    """
    Estorna um lançamento contábil criando lançamento inverso.
    
    Args:
        conn: Conexão com o banco
        lancamento_id: ID do lançamento a estornar
        empresa_id: ID da empresa
        historico_estorno: Histórico do estorno
        created_by: ID do usuário que está estornando
    
    Returns:
        Dict com resultado do estorno
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Buscar lançamento original
        resultado = obter_lancamento_detalhado(conn, lancamento_id, empresa_id)
        if not resultado['success']:
            return resultado
        
        lancamento_original = resultado['lancamento']
        
        # Verificar se já foi estornado
        if lancamento_original['is_estornado']:
            return {'success': False, 'error': 'Lançamento já foi estornado'}
        
        # Criar itens invertidos
        itens_estorno = []
        for item in lancamento_original['itens']:
            itens_estorno.append({
                'plano_contas_id': item['plano_contas_id'],
                'tipo': 'credito' if item['tipo'] == 'debito' else 'debito',  # Inverter
                'valor': item['valor'],
                'historico_complementar': f"Estorno: {item.get('historico_complementar', '')}",
                'centro_custo': item.get('centro_custo')
            })
        
        # Criar lançamento de estorno
        resultado_estorno = criar_lancamento(
            conn=conn,
            empresa_id=empresa_id,
            data_lancamento=date.today(),
            historico=f"ESTORNO: {historico_estorno}",
            itens=itens_estorno,
            tipo_lancamento='manual',
            origem='estorno',
            origem_id=lancamento_id,
            versao_plano_id=lancamento_original['versao_plano_id'],
            observacoes=f"Estorno do lançamento {lancamento_original['numero_lancamento']}",
            created_by=created_by
        )
        
        if not resultado_estorno['success']:
            return resultado_estorno
        
        # Marcar lançamento original como estornado
        cur.execute("""
            UPDATE lancamentos_contabeis
            SET is_estornado = TRUE,
                lancamento_estorno_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (resultado_estorno['lancamento_id'], lancamento_id, empresa_id))
        
        conn.commit()
        
        return {
            'success': True,
            'message': 'Lançamento estornado com sucesso',
            'lancamento_estorno_id': resultado_estorno['lancamento_id'],
            'numero_estorno': resultado_estorno['numero_lancamento']
        }
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def deletar_lancamento(conn, lancamento_id: int, empresa_id: int) -> Dict:
    """
    Deleta um lançamento contábil (hard delete).
    
    Args:
        conn: Conexão com o banco
        lancamento_id: ID do lançamento
        empresa_id: ID da empresa (para segurança)
    
    Returns:
        Dict com resultado
    """
    cur = conn.cursor()
    
    try:
        # Verificar se existe e pertence à empresa
        cur.execute("""
            SELECT id, is_estornado, origem
            FROM lancamentos_contabeis
            WHERE id = %s AND empresa_id = %s
        """, (lancamento_id, empresa_id))
        
        resultado = cur.fetchone()
        if not resultado:
            return {'success': False, 'error': 'Lançamento não encontrado'}
        
        # Não permitir deletar lançamentos estornados (apenas o estorno)
        if resultado[1] and resultado[2] != 'estorno':
            return {
                'success': False,
                'error': 'Não é possível deletar lançamento estornado. Delete o estorno primeiro.'
            }
        
        # Deletar (CASCADE vai deletar os itens automaticamente)
        cur.execute("""
            DELETE FROM lancamentos_contabeis
            WHERE id = %s AND empresa_id = %s
        """, (lancamento_id, empresa_id))
        
        conn.commit()
        
        return {'success': True, 'message': 'Lançamento deletado com sucesso'}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def obter_estatisticas_lancamentos(conn, empresa_id: int, ano: Optional[int] = None) -> Dict:
    """
    Obtém estatísticas dos lançamentos contábeis.
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        ano: Ano para filtrar (opcional, padrão: ano atual)
    
    Returns:
        Dict com estatísticas
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        if not ano:
            ano = datetime.now().year
        
        cur.execute("""
            SELECT 
                COUNT(*) AS total_lancamentos,
                COUNT(CASE WHEN tipo_lancamento = 'manual' THEN 1 END) AS total_manuais,
                COUNT(CASE WHEN tipo_lancamento = 'automatico' THEN 1 END) AS total_automaticos,
                COUNT(CASE WHEN tipo_lancamento = 'importado' THEN 1 END) AS total_importados,
                COUNT(CASE WHEN is_estornado THEN 1 END) AS total_estornados,
                SUM(valor_total) AS valor_total_lancamentos,
                MIN(data_lancamento) AS data_primeiro_lancamento,
                MAX(data_lancamento) AS data_ultimo_lancamento
            FROM lancamentos_contabeis
            WHERE empresa_id = %s
              AND EXTRACT(YEAR FROM data_lancamento) = %s
        """, (empresa_id, ano))
        
        stats = dict(cur.fetchone())
        
        # Converter valores
        if stats['valor_total_lancamentos']:
            stats['valor_total_lancamentos'] = float(stats['valor_total_lancamentos'])
        if stats['data_primeiro_lancamento']:
            stats['data_primeiro_lancamento'] = stats['data_primeiro_lancamento'].isoformat()
        if stats['data_ultimo_lancamento']:
            stats['data_ultimo_lancamento'] = stats['data_ultimo_lancamento'].isoformat()
        
        return {
            'success': True,
            'ano': ano,
            'estatisticas': stats
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()

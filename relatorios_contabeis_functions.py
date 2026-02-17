#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RELATÓRIOS CONTÁBEIS - FUNÇÕES BACKEND
FASE 3 - Speed Integration
Data: 17/02/2026

Geração de relatórios contábeis: Balancete, DRE, Balanço Patrimonial
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


def gerar_balancete_verificacao(
    conn,
    empresa_id: int,
    data_inicio: date,
    data_fim: date,
    versao_plano_id: Optional[int] = None,
    nivel_minimo: Optional[int] = None,
    nivel_maximo: Optional[int] = None,
    classificacao: Optional[str] = None,
    apenas_com_movimento: bool = False
) -> Dict:
    """
    Gera Balancete de Verificação para um período.
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_inicio: Data inicial do período
        data_fim: Data final do período
        versao_plano_id: ID da versão do plano de contas
        nivel_minimo: Nível mínimo de conta (1, 2, 3...)
        nivel_maximo: Nível máximo de conta
        classificacao: Filtrar por classificação (ativo, passivo, etc)
        apenas_com_movimento: Mostrar apenas contas com movimentação
    
    Returns:
        Dict com balancete completo
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Query base para buscar contas
        query_contas = """
            SELECT 
                pc.id,
                pc.codigo,
                pc.descricao,
                pc.nivel,
                pc.classificacao,
                pc.natureza,
                pc.tipo_conta
            FROM plano_contas pc
            WHERE pc.empresa_id = %s
        """
        
        params_contas = [empresa_id]
        
        if versao_plano_id:
            query_contas += " AND pc.versao_id = %s"
            params_contas.append(versao_plano_id)
        
        if nivel_minimo:
            query_contas += " AND pc.nivel >= %s"
            params_contas.append(nivel_minimo)
        
        if nivel_maximo:
            query_contas += " AND pc.nivel <= %s"
            params_contas.append(nivel_maximo)
        
        if classificacao:
            query_contas += " AND pc.classificacao = %s"
            params_contas.append(classificacao)
        
        query_contas += " ORDER BY pc.codigo"
        
        cur.execute(query_contas, params_contas)
        contas = [dict(row) for row in cur.fetchall()]
        
        # Para cada conta, calcular saldos
        balancete = []
        
        for conta in contas:
            # Saldo anterior (antes do período)
            cur.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) AS total_debito,
                    COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) AS total_credito
                FROM lancamentos_contabeis_itens lci
                INNER JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
                WHERE lci.plano_contas_id = %s
                  AND lc.empresa_id = %s
                  AND lc.data_lancamento < %s
                  AND lc.is_estornado = FALSE
            """, (conta['id'], empresa_id, data_inicio))
            
            saldo_ant = cur.fetchone()
            debito_anterior = float(saldo_ant['total_debito'])
            credito_anterior = float(saldo_ant['total_credito'])
            
            # Movimentação no período
            cur.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) AS total_debito,
                    COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) AS total_credito
                FROM lancamentos_contabeis_itens lci
                INNER JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
                WHERE lci.plano_contas_id = %s
                  AND lc.empresa_id = %s
                  AND lc.data_lancamento >= %s
                  AND lc.data_lancamento <= %s
                  AND lc.is_estornado = FALSE
            """, (conta['id'], empresa_id, data_inicio, data_fim))
            
            movimento = cur.fetchone()
            debito_periodo = float(movimento['total_debito'])
            credito_periodo = float(movimento['total_credito'])
            
            # Calcular saldo anterior
            if conta['natureza'] == 'devedora':
                saldo_anterior = debito_anterior - credito_anterior
            else:
                saldo_anterior = credito_anterior - debito_anterior
            
            # Calcular saldo atual
            debito_total = debito_anterior + debito_periodo
            credito_total = credito_anterior + credito_periodo
            
            if conta['natureza'] == 'devedora':
                saldo_atual = debito_total - credito_total
            else:
                saldo_atual = credito_total - debito_total
            
            # Determinar tipo de saldo
            tipo_saldo_anterior = 'devedor' if saldo_anterior >= 0 else 'credor'
            tipo_saldo_atual = 'devedor' if saldo_atual >= 0 else 'credor'
            
            # Filtro: apenas com movimento
            if apenas_com_movimento and debito_periodo == 0 and credito_periodo == 0:
                continue
            
            balancete.append({
                'codigo': conta['codigo'],
                'descricao': conta['descricao'],
                'nivel': conta['nivel'],
                'classificacao': conta['classificacao'],
                'tipo_conta': conta['tipo_conta'],
                'saldo_anterior': abs(saldo_anterior),
                'tipo_saldo_anterior': tipo_saldo_anterior,
                'debito_periodo': debito_periodo,
                'credito_periodo': credito_periodo,
                'saldo_atual': abs(saldo_atual),
                'tipo_saldo_atual': tipo_saldo_atual
            })
        
        # Calcular totais
        total_debito_periodo = sum(item['debito_periodo'] for item in balancete)
        total_credito_periodo = sum(item['credito_periodo'] for item in balancete)
        total_saldo_devedor = sum(item['saldo_atual'] for item in balancete if item['tipo_saldo_atual'] == 'devedor')
        total_saldo_credor = sum(item['saldo_atual'] for item in balancete if item['tipo_saldo_atual'] == 'credor')
        
        return {
            'success': True,
            'balancete': balancete,
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'totais': {
                'total_debito_periodo': total_debito_periodo,
                'total_credito_periodo': total_credito_periodo,
                'total_saldo_devedor': total_saldo_devedor,
                'total_saldo_credor': total_saldo_credor,
                'diferenca': abs(total_saldo_devedor - total_saldo_credor)
            },
            'total_contas': len(balancete)
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def gerar_dre(
    conn,
    empresa_id: int,
    data_inicio: date,
    data_fim: date,
    versao_plano_id: Optional[int] = None
) -> Dict:
    """
    Gera DRE (Demonstrativo de Resultado do Exercício) para um período.
    
    Estrutura:
    - Receitas (classificacao='receita')
    - (-) Custos (classificacao='despesa' + codigo inicia com '5')
    - = Lucro Bruto
    - (-) Despesas Operacionais (classificacao='despesa' + codigo inicia com '6')
    - = Resultado Operacional
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_inicio: Data inicial do período
        data_fim: Data final do período
        versao_plano_id: ID da versão do plano de contas
    
    Returns:
        Dict com DRE estruturada
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Função auxiliar para buscar saldo de contas por classificação
        def buscar_saldo_grupo(classificacao_conta: str, prefixo_codigo: Optional[str] = None):
            query = """
                SELECT 
                    pc.codigo,
                    pc.descricao,
                    pc.classificacao,
                    COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) AS total_debito,
                    COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) AS total_credito
                FROM plano_contas pc
                LEFT JOIN lancamentos_contabeis_itens lci ON lci.plano_contas_id = pc.id
                LEFT JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
                    AND lc.data_lancamento >= %s
                    AND lc.data_lancamento <= %s
                    AND lc.is_estornado = FALSE
                    AND lc.empresa_id = %s
                WHERE pc.empresa_id = %s
                  AND pc.classificacao = %s
                  AND pc.tipo_conta = 'analitica'
            """
            
            params = [data_inicio, data_fim, empresa_id, empresa_id, classificacao_conta]
            
            if versao_plano_id:
                query += " AND pc.versao_id = %s"
                params.append(versao_plano_id)
            
            if prefixo_codigo:
                query += " AND pc.codigo LIKE %s"
                params.append(f"{prefixo_codigo}%")
            
            query += " GROUP BY pc.id, pc.codigo, pc.descricao, pc.classificacao"
            query += " HAVING (COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) > 0"
            query += "     OR COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) > 0)"
            query += " ORDER BY pc.codigo"
            
            cur.execute(query, params)
            resultados = []
            
            for row in cur.fetchall():
                debito = float(row['total_debito'])
                credito = float(row['total_credito'])
                
                # Receitas: crédito aumenta, débito diminui
                # Despesas/Custos: débito aumenta, crédito diminui
                if classificacao_conta == 'receita':
                    valor = credito - debito
                else:  # despesa
                    valor = debito - credito
                
                if valor != 0:
                    resultados.append({
                        'codigo': row['codigo'],
                        'descricao': row['descricao'],
                        'valor': valor
                    })
            
            return resultados
        
        # 1. RECEITAS (grupo 4)
        receitas = buscar_saldo_grupo('receita')
        receita_bruta = sum(item['valor'] for item in receitas)
        
        # 2. CUSTOS (grupo 5 - começam com 5)
        custos = buscar_saldo_grupo('despesa', '5')
        total_custos = sum(item['valor'] for item in custos)
        
        # 3. LUCRO BRUTO
        lucro_bruto = receita_bruta - total_custos
        
        # 4. DESPESAS OPERACIONAIS (grupo 6 - começam com 6)
        despesas = buscar_saldo_grupo('despesa', '6')
        total_despesas = sum(item['valor'] for item in despesas)
        
        # 5. RESULTADO OPERACIONAL
        resultado_operacional = lucro_bruto - total_despesas
        
        # 6. OUTRAS RECEITAS/DESPESAS (grupo 7 - começam com 7)
        outras_receitas_despesas = buscar_saldo_grupo('despesa', '7')
        total_outras = sum(item['valor'] for item in outras_receitas_despesas)
        
        # 7. RESULTADO LÍQUIDO
        resultado_liquido = resultado_operacional - total_outras
        
        return {
            'success': True,
            'dre': {
                'receitas': {
                    'itens': receitas,
                    'total': receita_bruta
                },
                'custos': {
                    'itens': custos,
                    'total': total_custos
                },
                'lucro_bruto': lucro_bruto,
                'despesas_operacionais': {
                    'itens': despesas,
                    'total': total_despesas
                },
                'resultado_operacional': resultado_operacional,
                'outras_receitas_despesas': {
                    'itens': outras_receitas_despesas,
                    'total': total_outras
                },
                'resultado_liquido': resultado_liquido
            },
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'indicadores': {
                'margem_bruta': (lucro_bruto / receita_bruta * 100) if receita_bruta > 0 else 0,
                'margem_operacional': (resultado_operacional / receita_bruta * 100) if receita_bruta > 0 else 0,
                'margem_liquida': (resultado_liquido / receita_bruta * 100) if receita_bruta > 0 else 0
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def gerar_balanco_patrimonial(
    conn,
    empresa_id: int,
    data_referencia: date,
    versao_plano_id: Optional[int] = None
) -> Dict:
    """
    Gera Balanço Patrimonial em uma data específica.
    
    Estrutura:
    - ATIVO (classificacao='ativo')
    - PASSIVO (classificacao='passivo')
    - PATRIMÔNIO LÍQUIDO (classificacao='patrimonio_liquido')
    
    Validação: Ativo = Passivo + PL
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_referencia: Data de referência para o balanço
        versao_plano_id: ID da versão do plano de contas
    
    Returns:
        Dict com Balanço Patrimonial estruturado
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Função auxiliar para buscar saldo acumulado até a data
        def buscar_saldo_classificacao(classificacao_conta: str, nivel: Optional[int] = None):
            query = """
                SELECT 
                    pc.codigo,
                    pc.descricao,
                    pc.nivel,
                    pc.tipo_conta,
                    pc.natureza,
                    COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) AS total_debito,
                    COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) AS total_credito
                FROM plano_contas pc
                LEFT JOIN lancamentos_contabeis_itens lci ON lci.plano_contas_id = pc.id
                LEFT JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
                    AND lc.data_lancamento <= %s
                    AND lc.is_estornado = FALSE
                    AND lc.empresa_id = %s
                WHERE pc.empresa_id = %s
                  AND pc.classificacao = %s
            """
            
            params = [data_referencia, empresa_id, empresa_id, classificacao_conta]
            
            if versao_plano_id:
                query += " AND pc.versao_id = %s"
                params.append(versao_plano_id)
            
            if nivel:
                query += " AND pc.nivel = %s"
                params.append(nivel)
            
            query += " GROUP BY pc.id, pc.codigo, pc.descricao, pc.nivel, pc.tipo_conta, pc.natureza"
            query += " ORDER BY pc.codigo"
            
            cur.execute(query, params)
            resultados = []
            
            for row in cur.fetchall():
                debito = float(row['total_debito'])
                credito = float(row['total_credito'])
                
                # Calcular saldo baseado na natureza
                if row['natureza'] == 'devedora':
                    saldo = debito - credito
                else:
                    saldo = credito - debito
                
                # Incluir apenas contas com saldo ou sintéticas
                if saldo != 0 or row['tipo_conta'] == 'sintetica':
                    resultados.append({
                        'codigo': row['codigo'],
                        'descricao': row['descricao'],
                        'nivel': row['nivel'],
                        'tipo_conta': row['tipo_conta'],
                        'saldo': saldo
                    })
            
            return resultados
        
        # 1. ATIVO (grupo 1)
        ativo = buscar_saldo_classificacao('ativo')
        total_ativo = sum(item['saldo'] for item in ativo if item['saldo'] > 0)
        
        # Separar Ativo Circulante e Não Circulante
        ativo_circulante = [item for item in ativo if item['codigo'].startswith('1.1')]
        ativo_nao_circulante = [item for item in ativo if item['codigo'].startswith('1.2')]
        
        total_ativo_circulante = sum(item['saldo'] for item in ativo_circulante if item['saldo'] > 0)
        total_ativo_nao_circulante = sum(item['saldo'] for item in ativo_nao_circulante if item['saldo'] > 0)
        
        # 2. PASSIVO (grupo 2)
        passivo = buscar_saldo_classificacao('passivo')
        total_passivo_obrigacoes = sum(item['saldo'] for item in passivo if item['saldo'] > 0)
        
        # Separar Passivo Circulante e Não Circulante
        passivo_circulante = [item for item in passivo if item['codigo'].startswith('2.1')]
        passivo_nao_circulante = [item for item in passivo if item['codigo'].startswith('2.2')]
        
        total_passivo_circulante = sum(item['saldo'] for item in passivo_circulante if item['saldo'] > 0)
        total_passivo_nao_circulante = sum(item['saldo'] for item in passivo_nao_circulante if item['saldo'] > 0)
        
        # 3. PATRIMÔNIO LÍQUIDO (grupo 3)
        patrimonio_liquido = buscar_saldo_classificacao('patrimonio_liquido')
        total_patrimonio_liquido = sum(item['saldo'] for item in patrimonio_liquido if item['saldo'] > 0)
        
        # 4. VALIDAÇÃO: Ativo = Passivo + PL
        total_passivo_mais_pl = total_passivo_obrigacoes + total_patrimonio_liquido
        diferenca = abs(total_ativo - total_passivo_mais_pl)
        balanco_fechado = diferenca < 0.01  # Tolerância de 1 centavo
        
        return {
            'success': True,
            'balanco': {
                'ativo': {
                    'circulante': {
                        'itens': ativo_circulante,
                        'total': total_ativo_circulante
                    },
                    'nao_circulante': {
                        'itens': ativo_nao_circulante,
                        'total': total_ativo_nao_circulante
                    },
                    'total': total_ativo
                },
                'passivo': {
                    'circulante': {
                        'itens': passivo_circulante,
                        'total': total_passivo_circulante
                    },
                    'nao_circulante': {
                        'itens': passivo_nao_circulante,
                        'total': total_passivo_nao_circulante
                    },
                    'total': total_passivo_obrigacoes
                },
                'patrimonio_liquido': {
                    'itens': patrimonio_liquido,
                    'total': total_patrimonio_liquido
                },
                'total_passivo_pl': total_passivo_mais_pl
            },
            'data_referencia': data_referencia.isoformat(),
            'validacao': {
                'balanco_fechado': balanco_fechado,
                'diferenca': diferenca,
                'formula': f"Ativo ({total_ativo:.2f}) = Passivo ({total_passivo_obrigacoes:.2f}) + PL ({total_patrimonio_liquido:.2f})"
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()


def gerar_razao_contabil(
    conn,
    empresa_id: int,
    conta_id: int,
    data_inicio: date,
    data_fim: date
) -> Dict:
    """
    Gera Razão Contábil (extrato) de uma conta específica.
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        conta_id: ID da conta contábil
        data_inicio: Data inicial
        data_fim: Data final
    
    Returns:
        Dict com extrato da conta
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Buscar dados da conta
        cur.execute("""
            SELECT codigo, descricao, natureza, classificacao
            FROM plano_contas
            WHERE id = %s AND empresa_id = %s
        """, (conta_id, empresa_id))
        
        conta = cur.fetchone()
        if not conta:
            return {'success': False, 'error': 'Conta não encontrada'}
        
        conta = dict(conta)
        
        # Saldo anterior
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) AS total_debito,
                COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) AS total_credito
            FROM lancamentos_contabeis_itens lci
            INNER JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
            WHERE lci.plano_contas_id = %s
              AND lc.empresa_id = %s
              AND lc.data_lancamento < %s
              AND lc.is_estornado = FALSE
        """, (conta_id, empresa_id, data_inicio))
        
        saldo_ant = cur.fetchone()
        debito_anterior = float(saldo_ant['total_debito'])
        credito_anterior = float(saldo_ant['total_credito'])
        
        if conta['natureza'] == 'devedora':
            saldo_anterior = debito_anterior - credito_anterior
        else:
            saldo_anterior = credito_anterior - debito_anterior
        
        # Movimentações do período
        cur.execute("""
            SELECT 
                lc.data_lancamento,
                lc.numero_lancamento,
                lc.historico,
                lci.tipo,
                lci.valor,
                lci.historico_complementar
            FROM lancamentos_contabeis_itens lci
            INNER JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
            WHERE lci.plano_contas_id = %s
              AND lc.empresa_id = %s
              AND lc.data_lancamento >= %s
              AND lc.data_lancamento <= %s
              AND lc.is_estornado = FALSE
            ORDER BY lc.data_lancamento, lc.numero_lancamento, lci.id
        """, (conta_id, empresa_id, data_inicio, data_fim))
        
        movimentacoes = []
        saldo_atual = saldo_anterior
        
        for row in cur.fetchall():
            valor = float(row['valor'])
            
            if row['tipo'] == 'debito':
                if conta['natureza'] == 'devedora':
                    saldo_atual += valor
                else:
                    saldo_atual -= valor
            else:  # credito
                if conta['natureza'] == 'devedora':
                    saldo_atual -= valor
                else:
                    saldo_atual += valor
            
            movimentacoes.append({
                'data': row['data_lancamento'].isoformat(),
                'numero_lancamento': row['numero_lancamento'],
                'historico': row['historico'],
                'historico_complementar': row['historico_complementar'],
                'tipo': row['tipo'],
                'debito': valor if row['tipo'] == 'debito' else 0,
                'credito': valor if row['tipo'] == 'credito' else 0,
                'saldo': saldo_atual
            })
        
        return {
            'success': True,
            'conta': conta,
            'saldo_anterior': saldo_anterior,
            'movimentacoes': movimentacoes,
            'saldo_atual': saldo_atual,
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat()
            },
            'total_movimentacoes': len(movimentacoes)
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()

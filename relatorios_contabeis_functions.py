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
    versao_plano_id: Optional[int] = None,
    comparar_periodo_anterior: bool = False
) -> Dict:
    """
    Gera DRE (Demonstração do Resultado do Exercício) COMPLETA para um período.
    
    Estrutura melhorada:
    1. RECEITA BRUTA (grupo 4, exceto 4.9)
    2. (-) DEDUÇÕES DA RECEITA (grupo 4.9)
    3. = RECEITA LÍQUIDA
    4. (-) CUSTOS (grupo 5)
    5. = LUCRO BRUTO
    6. (-) DESPESAS OPERACIONAIS (grupo 6)
    7. = RESULTADO OPERACIONAL
    8. (+/-) RESULTADO FINANCEIRO (7.1 receitas - 7.2 despesas financeiras)
    9. = LUCRO LÍQUIDO DO EXERCÍCIO
    
    + Percentuais sobre receita bruta para cada linha
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_inicio: Data inicial do período
        data_fim: Data final do período
        versao_plano_id: ID da versão do plano de contas
        comparar_periodo_anterior: Se True, retorna dados comparativos também
    
    Returns:
        Dict com DRE estruturada e indicadores
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Função auxiliar para buscar saldo de contas por classificação e prefixo
        def buscar_saldo_grupo(
            classificacao_conta: Optional[str] = None, 
            prefixo_codigo: Optional[str] = None,
            excluir_prefixo: Optional[str] = None,
            data_ini: date = None,
            data_fi: date = None
        ):
            """
            Busca saldo de grupo de contas com filtros flexíveis
            
            Args:
                classificacao_conta: 'receita' ou 'despesa'
                prefixo_codigo: Código deve começar com (ex: '4', '5', '6')
                excluir_prefixo: Código NÃO deve começar com (ex: '4.9')  
                data_ini, data_fi: Período customizado (se None, usa data_inicio/data_fim)
            """
            di = data_ini or data_inicio
            df = data_fi or data_fim
            
            query = """
                SELECT 
                    pc.codigo,
                    pc.descricao,
                    pc.classificacao,
                    pc.natureza,
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
                  AND pc.tipo_conta = 'analitica'
                  AND pc.deleted_at IS NULL
            """
            
            params = [di, df, empresa_id, empresa_id]
            
            if classificacao_conta:
                query += " AND pc.classificacao = %s"
                params.append(classificacao_conta)
            
            if versao_plano_id:
                query += " AND pc.versao_id = %s"
                params.append(versao_plano_id)
            
            if prefixo_codigo:
                query += " AND pc.codigo LIKE %s"
                params.append(f"{prefixo_codigo}%")
            
            if excluir_prefixo:
                query += " AND pc.codigo NOT LIKE %s"
                params.append(f"{excluir_prefixo}%")
            
            query += " GROUP BY pc.id, pc.codigo, pc.descricao, pc.classificacao, pc.natureza"
            query += " HAVING (COALESCE(SUM(CASE WHEN lci.tipo = 'debito' THEN lci.valor ELSE 0 END), 0) > 0"
            query += "     OR COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) > 0)"
            query += " ORDER BY pc.codigo"
            
            cur.execute(query, params)
            resultados = []
            
            for row in cur.fetchall():
                debito = float(row['total_debito'])
                credito = float(row['total_credito'])
                
                # Lógica de saldo baseada na natureza da conta
                natureza = row['natureza']
                if natureza == 'credora':  # Receitas
                    valor = credito - debito
                else:  # Devedora - Despesas/Custos
                    valor = debito - credito
                
                if valor != 0:
                    resultados.append({
                        'codigo': row['codigo'],
                        'descricao': row['descricao'],
                        'valor': valor
                    })
            
            return resultados
        
        def calcular_dre_periodo(di: date, df: date):
            """Calcula DRE para um período específico"""
            
            # 1. RECEITA BRUTA (grupo 4, excluindo 4.9 - deduções)
            receitas_brutas = buscar_saldo_grupo(
                classificacao_conta='receita', 
                prefixo_codigo='4',
                excluir_prefixo='4.9',
                data_ini=di,
                data_fi=df
            )
            receita_bruta = sum(item['valor'] for item in receitas_brutas)
            
            # 2. DEDUÇÕES DA RECEITA (grupo 4.9)
            deducoes = buscar_saldo_grupo(
                classificacao_conta='receita', 
                prefixo_codigo='4.9',
                data_ini=di,
                data_fi=df
            )
            total_deducoes = sum(item['valor'] for item in deducoes)
            
            # 3. RECEITA LÍQUIDA
            receita_liquida = receita_bruta - abs(total_deducoes)
            
            # 4. CUSTOS (grupo 5)
            custos = buscar_saldo_grupo(
                classificacao_conta='despesa', 
                prefixo_codigo='5',
                data_ini=di,
                data_fi=df
            )
            total_custos = sum(item['valor'] for item in custos)
            
            # 5. LUCRO BRUTO
            lucro_bruto = receita_liquida - total_custos
            
            # 6. DESPESAS OPERACIONAIS (grupo 6)
            despesas_operacionais = buscar_saldo_grupo(
                classificacao_conta='despesa', 
                prefixo_codigo='6',
                data_ini=di,
                data_fi=df
            )
            total_despesas_operacionais = sum(item['valor'] for item in despesas_operacionais)
            
            # 7. RESULTADO OPERACIONAL
            resultado_operacional = lucro_bruto - total_despesas_operacionais
            
            # 8. RESULTADO FINANCEIRO
            # 8.1 Receitas Financeiras (7.1)
            receitas_financeiras = buscar_saldo_grupo(
                classificacao_conta='receita', 
                prefixo_codigo='7.1',
                data_ini=di,
                data_fi=df
            )
            total_receitas_financeiras = sum(item['valor'] for item in receitas_financeiras)
            
            # 8.2 Despesas Financeiras (7.2)
            despesas_financeiras = buscar_saldo_grupo(
                classificacao_conta='despesa', 
                prefixo_codigo='7.2',
                data_ini=di,
                data_fi=df
            )
            total_despesas_financeiras = sum(item['valor'] for item in despesas_financeiras)
            
            resultado_financeiro = total_receitas_financeiras - total_despesas_financeiras
            
            # 9. LUCRO LÍQUIDO DO EXERCÍCIO
            lucro_liquido = resultado_operacional + resultado_financeiro
            
            # Cálculo de percentuais sobre receita bruta
            def percentual(valor, base):
                return (valor / base * 100) if base != 0 else 0
            
            return {
                'receita_bruta': {
                    'itens': receitas_brutas,
                    'total': receita_bruta,
                    'percentual': 100.0
                },
                'deducoes': {
                    'itens': deducoes,
                    'total': abs(total_deducoes),
                    'percentual': percentual(abs(total_deducoes), receita_bruta)
                },
                'receita_liquida': {
                    'total': receita_liquida,
                    'percentual': percentual(receita_liquida, receita_bruta)
                },
                'custos': {
                    'itens': custos,
                    'total': total_custos,
                    'percentual': percentual(total_custos, receita_bruta)
                },
                'lucro_bruto': {
                    'total': lucro_bruto,
                    'percentual': percentual(lucro_bruto, receita_bruta)
                },
                'despesas_operacionais': {
                    'itens': despesas_operacionais,
                    'total': total_despesas_operacionais,
                    'percentual': percentual(total_despesas_operacionais, receita_bruta)
                },
                'resultado_operacional': {
                    'total': resultado_operacional,
                    'percentual': percentual(resultado_operacional, receita_bruta)
                },
                'resultado_financeiro': {
                    'receitas_financeiras': {
                        'itens': receitas_financeiras,
                        'total': total_receitas_financeiras
                    },
                    'despesas_financeiras': {
                        'itens': despesas_financeiras,
                        'total': total_despesas_financeiras
                    },
                    'total': resultado_financeiro,
                    'percentual': percentual(resultado_financeiro, receita_bruta)
                },
                'lucro_liquido': {
                    'total': lucro_liquido,
                    'percentual': percentual(lucro_liquido, receita_bruta)
                }
            }
        
        # Calcular DRE do período solicitado
        dre_atual = calcular_dre_periodo(data_inicio, data_fim)
        
        resultado = {
            'success': True,
            'dre': dre_atual,
            'periodo': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat(),
                'descricao': f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            },
            'indicadores': {
                'margem_bruta': dre_atual['lucro_bruto']['percentual'],
                'margem_operacional': dre_atual['resultado_operacional']['percentual'],
                'margem_liquida': dre_atual['lucro_liquido']['percentual'],
                'rentabilidade': (dre_atual['lucro_liquido']['total'] / dre_atual['receita_bruta']['total'] * 100) if dre_atual['receita_bruta']['total'] > 0 else 0
            }
        }
        
        # Se solicitado comparativo com período anterior
        if comparar_periodo_anterior:
            from dateutil.relativedelta import relativedelta
            
            # Calcular período anterior (mesmo intervalo de dias)
            dias_periodo = (data_fim - data_inicio).days
            data_inicio_anterior = data_inicio - relativedelta(days=dias_periodo + 1)
            data_fim_anterior = data_inicio - relativedelta(days=1)
            
            dre_anterior = calcular_dre_periodo(data_inicio_anterior, data_fim_anterior)
            
            # Calcular variações
            def calcular_variacao(atual, anterior):
                if anterior == 0:
                    return 0 if atual == 0 else 100
                return ((atual - anterior) / abs(anterior)) * 100
            
            resultado['dre_anterior'] = dre_anterior
            resultado['periodo_anterior'] = {
                'data_inicio': data_inicio_anterior.isoformat(),
                'data_fim': data_fim_anterior.isoformat(),
                'descricao': f"{data_inicio_anterior.strftime('%d/%m/%Y')} a {data_fim_anterior.strftime('%d/%m/%Y')}"
            }
            resultado['variacoes'] = {
                'receita_bruta': calcular_variacao(dre_atual['receita_bruta']['total'], dre_anterior['receita_bruta']['total']),
                'receita_liquida': calcular_variacao(dre_atual['receita_liquida']['total'], dre_anterior['receita_liquida']['total']),
                'lucro_bruto': calcular_variacao(dre_atual['lucro_bruto']['total'], dre_anterior['lucro_bruto']['total']),
                'resultado_operacional': calcular_variacao(dre_atual['resultado_operacional']['total'], dre_anterior['resultado_operacional']['total']),
                'lucro_liquido': calcular_variacao(dre_atual['lucro_liquido']['total'], dre_anterior['lucro_liquido']['total'])
            }
        
        return resultado
        
    except Exception as e:
        import traceback
        print(f"ERRO em gerar_dre: {e}")
        print(traceback.format_exc())
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

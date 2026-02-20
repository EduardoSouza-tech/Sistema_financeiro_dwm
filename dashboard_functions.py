#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DASHBOARD GERENCIAL - FUNÇÕES BACKEND
Data: 19/02/2026

Geração de dashboard gerencial com KPIs e indicadores
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, date
from typing import Dict, List, Optional
from dateutil.relativedelta import relativedelta
from calendar import monthrange


def gerar_dashboard_gerencial(
    conn,
    empresa_id: int,
    data_referencia: Optional[date] = None,
    versao_plano_id: Optional[int] = None
) -> Dict:
    """
    Gera Dashboard Gerencial com KPIs e indicadores para o mês
    
    Métricas:
    - Receita do mês
    - Despesas do mês
    - Lucro líquido
    - Margem %
    - Evolução mensal (últimos 12 meses para gráficos)
    - Ponto de equilíbrio
    
    Args:
        conn: Conexão com o banco
        empresa_id: ID da empresa
        data_referencia: Data de referência (padrão: hoje)
        versao_plano_id: ID da versão do plano de contas
    
    Returns:
        Dict com métricas do dashboard
    """
    if data_referencia is None:
        data_referencia = date.today()
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Período do mês atual
        primeiro_dia_mes = data_referencia.replace(day=1)
        ultimo_dia_mes = data_referencia.replace(day=monthrange(data_referencia.year, data_referencia.month)[1])
        
        # Gerar DRE do mês atual
        from relatorios_contabeis_functions import gerar_dre
        dre_mes = gerar_dre(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=primeiro_dia_mes,
            data_fim=ultimo_dia_mes,
            versao_plano_id=versao_plano_id,
            comparar_periodo_anterior=False
        )
        
        if not dre_mes['success']:
            return dre_mes
        
        dre = dre_mes['dre']
        
        # KPIs do mês
        receita_mes = dre['receita_bruta']['total']
        despesas_mes = dre['custos']['total'] + dre['despesas_operacionais']['total']
        lucro_liquido_mes = dre['lucro_liquido']['total']
        margem_liquida = dre['lucro_liquido']['percentual']
        
        # ===== DETALHAMENTO PARA GRÁFICOS =====
        
        # Pie Chart: Despesas por categoria (top 5 + outros)
        despesas_detalhadas = []
        
        # Adicionar despesas operacionais
        for item in dre['despesas_operacionais'].get('itens', []):
            despesas_detalhadas.append({
                'categoria': item['descricao'],
                'valor': abs(item['valor'])  # Garantir valor positivo
            })
        
        # Adicionar custos
        for item in dre['custos'].get('itens', []):
            despesas_detalhadas.append({
                'categoria': item['descricao'],
                'valor': abs(item['valor'])
            })
        
        # Ordenar por valor e pegar top 5
        despesas_detalhadas_sorted = sorted(despesas_detalhadas, key=lambda x: x['valor'], reverse=True)
        
        if len(despesas_detalhadas_sorted) > 5:
            top_5_despesas = despesas_detalhadas_sorted[:5]
            outros_valor = sum(item['valor'] for item in despesas_detalhadas_sorted[5:])
            if outros_valor > 0:
                top_5_despesas.append({'categoria': 'Outros', 'valor': outros_valor})
            despesas_por_categoria = top_5_despesas
        else:
            despesas_por_categoria = despesas_detalhadas_sorted
        
        # Bar Chart: Receitas por categoria
        receitas_detalhadas = []
        for item in dre['receita_bruta'].get('itens', []):
            if item['valor'] > 0:  # Apenas receitas positivas
                receitas_detalhadas.append({
                    'categoria': item['descricao'],
                    'valor': item['valor']
                })
        
        # Ordenar por valor (top 10)
        receitas_por_categoria = sorted(receitas_detalhadas, key=lambda x: x['valor'], reverse=True)[:10]
        
        # ===== EVOLUÇÃO MENSAL (últimos 12 meses para gráficos) =====
        evolucao_mensal = []
        
        for i in range(11, -1, -1):  # 12 meses (de 11 meses atrás até o mês atual)
            mes_ref = primeiro_dia_mes - relativedelta(months=i)
            ultimo_dia = mes_ref.replace(day=monthrange(mes_ref.year, mes_ref.month)[1])
            
            dre_mensal = gerar_dre(
                conn=conn,
                empresa_id=empresa_id,
                data_inicio=mes_ref,
                data_fim=ultimo_dia,
                versao_plano_id=versao_plano_id,
                comparar_periodo_anterior=False
            )
            
            if dre_mensal['success']:
                dre_m = dre_mensal['dre']
                evolucao_mensal.append({
                    'mes': mes_ref.strftime('%m/%Y'),
                    'mes_nome': mes_ref.strftime('%b/%Y'),
                    'receita': dre_m['receita_bruta']['total'],
                    'despesas': dre_m['custos']['total'] + dre_m['despesas_operacionais']['total'],
                    'lucro_liquido': dre_m['lucro_liquido']['total'],
                    'margem': dre_m['lucro_liquido']['percentual']
                })
        
        # ===== PONTO DE EQUILÍBRIO =====
        # Ponto de Equilíbrio = Custos Fixos / Margem de Contribuição (%)
        # Simplificação: assumir despesas operacionais como fixas
        custos_fixos = dre['despesas_operacionais']['total']
        custos_variaveis = dre['custos']['total']
        
        margem_contribuicao = receita_mes - custos_variaveis
        margem_contribuicao_percentual = (margem_contribuicao / receita_mes * 100) if receita_mes > 0 else 0
        
        ponto_equilibrio = (custos_fixos / (margem_contribuicao_percentual / 100)) if margem_contribuicao_percentual > 0 else 0
        
        # Percentual atingido do ponto de equilíbrio
        percentual_ponto_equilibrio = (receita_mes / ponto_equilibrio * 100) if ponto_equilibrio > 0 else 0
        atingiu_ponto_equilibrio = receita_mes >= ponto_equilibrio
        
        # ===== INDICADORES ADICIONAIS =====
        # Comparação com mês anterior
        mes_anterior = primeiro_dia_mes - relativedelta(months=1)
        ultimo_dia_anterior = mes_anterior.replace(day=monthrange(mes_anterior.year, mes_anterior.month)[1])
        
        dre_anterior = gerar_dre(
            conn=conn,
            empresa_id=empresa_id,
            data_inicio=mes_anterior,
            data_fim=ultimo_dia_anterior,
            versao_plano_id=versao_plano_id,
            comparar_periodo_anterior=False
        )
        
        variacao_receita = 0
        variacao_lucro = 0
        receita_anterior = 0
        lucro_anterior = 0
        
        if dre_anterior['success']:
            dre_ant = dre_anterior['dre']
            receita_anterior = dre_ant['receita_bruta']['total']
            lucro_anterior = dre_ant['lucro_liquido']['total']
            
            if receita_anterior > 0:
                variacao_receita = ((receita_mes - receita_anterior) / receita_anterior) * 100
            if lucro_anterior != 0:
                variacao_lucro = ((lucro_liquido_mes - lucro_anterior) / abs(lucro_anterior)) * 100
        
        return {
            'success': True,
            'dashboard': {
                'mes_referencia': data_referencia.strftime('%B/%Y'),
                'periodo': {
                    'data_inicio': primeiro_dia_mes.isoformat(),
                    'data_fim': ultimo_dia_mes.isoformat()
                },
                'kpis': {
                    'receita_mes': {
                        'valor': receita_mes,
                        'variacao_percentual': variacao_receita,
                        'tendencia': 'positiva' if variacao_receita > 0 else 'negativa' if variacao_receita < 0 else 'estavel'
                    },
                    'despesas_mes': {
                        'valor': despesas_mes,
                        'percentual_receita': (despesas_mes / receita_mes * 100) if receita_mes > 0 else 0
                    },
                    'lucro_liquido_mes': {
                        'valor': lucro_liquido_mes,
                        'variacao_percentual': variacao_lucro,
                        'tendencia': 'positiva' if variacao_lucro > 0 else 'negativa' if variacao_lucro < 0 else 'estavel'
                    },
                    'margem_liquida': {
                        'percentual': margem_liquida,
                        'status': 'excelente' if margem_liquida > 20 else 'bom' if margem_liquida > 10 else 'atencao' if margem_liquida > 0 else 'critico'
                    }
                },
                'evolucao_mensal': evolucao_mensal,
                'ponto_equilibrio': {
                    'valor': ponto_equilibrio,
                    'percentual_atingido': percentual_ponto_equilibrio,
                    'atingiu': atingiu_ponto_equilibrio,
                    'falta_para_equilibrio': max(0, ponto_equilibrio - receita_mes),
                    'custos_fixos': custos_fixos,
                    'margem_contribuicao_percentual': margem_contribuicao_percentual
                },
                'comparacao': {
                    'mes_anterior': {
                        'receita': receita_anterior,
                        'lucro': lucro_anterior
                    },
                    'variacoes': {
                        'receita': variacao_receita,
                        'lucro': variacao_lucro
                    }
                },
                'graficos_adicionais': {
                    'despesas_por_categoria': despesas_por_categoria,
                    'receitas_por_categoria': receitas_por_categoria
                }
            }
        }
        
    except Exception as e:
        import traceback
        print(f"ERRO em gerar_dashboard_gerencial: {e}")
        print(traceback.format_exc())
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()

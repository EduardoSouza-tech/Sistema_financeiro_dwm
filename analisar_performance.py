"""
📊 Analisador de Performance de Queries com RLS
Sistema Financeiro DWM - Fase 5

OBJETIVO:
    Executar EXPLAIN ANALYZE nas queries mais críticas do sistema
    e gerar relatório completo de performance.

FUNCIONALIDADES:
    - Análise de planos de execução PostgreSQL
    - Detecção de queries sem índices
    - Verificação de uso de RLS
    - Benchmark antes/depois dos índices
    - Relatório HTML completo

QUERIES ANALISADAS:
    1. Dashboard completo (lançamentos + contas + categorias)
    2. Listagem de lançamentos por empresa + período
    3. Relatórios por categoria
    4. Conciliação bancária (transações de extrato)
    5. Busca de clientes por CPF/CNPJ
    6. Contratos ativos por empresa
    7. Eventos de folha de pagamento
    8. Listagem de funcionários
    9. Kits de equipamentos por funcionário
    10. Produtos por categoria
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Adicionar pasta raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection
from logger_config import logger


class PerformanceAnalyzer:
    """Analisador de performance de queries"""
    
    def __init__(self):
        self.results = []
        self.empresa_id_teste = 1  # Empresa de teste
    
    def analyze_query(self, query_name: str, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Executa EXPLAIN ANALYZE em uma query
        
        Args:
            query_name: Nome descritivo da query
            query: SQL da query
            params: Parâmetros da query
        
        Returns:
            Dicionário com análise completa
        """
        logger.info(f"📊 Analisando: {query_name}")
        
        try:
            with get_db_connection(empresa_id=self.empresa_id_teste) as conn:
                with conn.cursor() as cursor:
                    # Executa EXPLAIN ANALYZE
                    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT JSON) {query}"
                    cursor.execute(explain_query, params or ())
                    explain_result = cursor.fetchone()[0]
                    
                    # Extrai métricas
                    plan = explain_result[0]
                    execution_time = plan['Execution Time']
                    planning_time = plan['Planning Time']
                    total_time = execution_time + planning_time
                    
                    # Verifica uso de índices
                    plan_str = json.dumps(plan, indent=2)
                    uses_index = 'Index Scan' in plan_str or 'Index Only Scan' in plan_str
                    uses_seq_scan = 'Seq Scan' in plan_str
                    
                    result = {
                        'query_name': query_name,
                        'query': query[:200] + '...' if len(query) > 200 else query,
                        'execution_time_ms': round(execution_time, 2),
                        'planning_time_ms': round(planning_time, 2),
                        'total_time_ms': round(total_time, 2),
                        'uses_index': uses_index,
                        'uses_seq_scan': uses_seq_scan,
                        'full_plan': plan,
                        'status': 'OK' if total_time < 200 else 'SLOW' if total_time < 500 else 'CRITICAL'
                    }
                    
                    self.results.append(result)
                    
                    # Log resultado
                    status_emoji = '✅' if result['status'] == 'OK' else '⚠️' if result['status'] == 'SLOW' else '🚨'
                    logger.info(
                        f"{status_emoji} {query_name}: {total_time:.0f}ms "
                        f"(índice: {'✅' if uses_index else '❌'})"
                    )
                    
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Erro ao analisar {query_name}: {str(e)}")
            return {
                'query_name': query_name,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def run_all_analyses(self):
        """Executa todas as análises de queries críticas"""
        logger.info("="*80)
        logger.info("🚀 INICIANDO ANÁLISE DE PERFORMANCE")
        logger.info("="*80)
        
        # Data ranges para testes
        data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        data_fim = datetime.now().strftime('%Y-%m-%d')
        
        # 1. Dashboard - Lançamentos por período
        self.analyze_query(
            query_name="Dashboard - Lançamentos Pagos (30 dias)",
            query="""
                SELECT 
                    l.id, l.descricao, l.valor, l.data_pagamento,
                    l.tipo, l.status, l.categoria, l.pessoa
                FROM lancamentos l
                WHERE l.empresa_id = %s
                  AND l.status = 'pago'
                  AND l.data_pagamento BETWEEN %s AND %s
                ORDER BY l.data_pagamento DESC
                LIMIT 100
            """,
            params=(self.empresa_id_teste, data_inicio, data_fim)
        )
        
        # 2. Dashboard - Análise por Categoria
        self.analyze_query(
            query_name="Dashboard - Totais por Categoria",
            query="""
                SELECT 
                    c.nome as categoria,
                    l.tipo,
                    COUNT(*) as quantidade,
                    SUM(l.valor) as total
                FROM lancamentos l
                JOIN categorias c ON c.id = l.categoria
                WHERE l.empresa_id = %s
                  AND c.empresa_id = %s
                  AND l.status = 'pago'
                  AND l.data_pagamento BETWEEN %s AND %s
                GROUP BY c.nome, l.tipo
                ORDER BY total DESC
            """,
            params=(self.empresa_id_teste, self.empresa_id_teste, data_inicio, data_fim)
        )
        
        # 3. Lançamentos Pendentes/Vencidos
        self.analyze_query(
            query_name="Alertas - Lançamentos Vencidos",
            query="""
                SELECT 
                    l.id, l.descricao, l.valor, l.data_vencimento,
                    l.tipo, l.categoria, l.pessoa
                FROM lancamentos l
                WHERE l.empresa_id = %s
                  AND l.status = 'pendente'
                  AND l.data_vencimento < CURRENT_DATE
                ORDER BY l.data_vencimento
                LIMIT 50
            """,
            params=(self.empresa_id_teste,)
        )
        
        # 4. Listagem de Clientes Ativos
        self.analyze_query(
            query_name="Clientes - Listagem Ativos",
            query="""
                SELECT 
                    id, nome, cpf_cnpj, email, telefone
                FROM clientes
                WHERE empresa_id = %s
                  AND ativo = true
                ORDER BY nome
                LIMIT 100
            """,
            params=(self.empresa_id_teste,)
        )
        
        # 5. Busca de Cliente por CPF/CNPJ
        self.analyze_query(
            query_name="Clientes - Busca por CPF/CNPJ",
            query="""
                SELECT 
                    id, nome, cpf_cnpj, email, telefone
                FROM clientes
                WHERE empresa_id = %s
                  AND cpf_cnpj = %s
            """,
            params=(self.empresa_id_teste, '12345678901')
        )
        
        # 6. Transações de Extrato - Não Conciliadas
        self.analyze_query(
            query_name="Extrato - Transações Pendentes de Conciliação",
            query="""
                SELECT 
                    id, data, descricao, valor, tipo, conta_bancaria
                FROM transacoes_extrato
                WHERE empresa_id = %s
                  AND conciliado = false
                ORDER BY data DESC
                LIMIT 50
            """,
            params=(self.empresa_id_teste,)
        )
        
        # 7. Contratos Ativos
        self.analyze_query(
            query_name="Contratos - Listagem Ativos",
            query="""
                SELECT 
                    id, descricao, cliente_id, valor, data_inicio, data_fim
                FROM contratos
                WHERE empresa_id = %s
                  AND status = 'ativo'
                ORDER BY data_inicio DESC
                LIMIT 50
            """,
            params=(self.empresa_id_teste,)
        )
        
        # 8. Eventos de Folha - Próximos 30 dias
        self.analyze_query(
            query_name="Folha - Eventos Próximos",
            query="""
                SELECT 
                    e.id, e.descricao, e.data, e.tipo, 
                    f.nome as funcionario
                FROM eventos e
                JOIN funcionarios f ON f.id = e.funcionario_id
                WHERE e.empresa_id = %s
                  AND f.empresa_id = %s
                  AND e.data BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                ORDER BY e.data
                LIMIT 50
            """,
            params=(self.empresa_id_teste, self.empresa_id_teste)
        )
        
        # 9. Funcionários Ativos
        self.analyze_query(
            query_name="Folha - Funcionários Ativos",
            query="""
                SELECT 
                    id, nome, cpf, cargo, salario
                FROM funcionarios
                WHERE empresa_id = %s
                  AND ativo = true
                ORDER BY nome
            """,
            params=(self.empresa_id_teste,)
        )
        
        # 10. Kits de Equipamentos por Funcionário
        self.analyze_query(
            query_name="Equipamentos - Kits por Funcionário",
            query="""
                SELECT 
                    k.id, k.nome, k.tipo, k.data_atribuicao,
                    f.nome as funcionario
                FROM kits_equipamentos k
                JOIN funcionarios f ON f.id = k.funcionario_id
                WHERE k.empresa_id = %s
                  AND f.empresa_id = %s
                  AND k.ativo = true
                ORDER BY k.data_atribuicao DESC
                LIMIT 50
            """,
            params=(self.empresa_id_teste, self.empresa_id_teste)
        )
        
        logger.info("="*80)
        logger.info("✅ ANÁLISE CONCLUÍDA")
        logger.info("="*80)
    
    def generate_html_report(self, output_file: str = 'relatorio_performance.html'):
        """Gera relatório HTML com os resultados"""
        
        # Calcula estatísticas gerais
        total_queries = len(self.results)
        queries_ok = len([r for r in self.results if r.get('status') == 'OK'])
        queries_slow = len([r for r in self.results if r.get('status') == 'SLOW'])
        queries_critical = len([r for r in self.results if r.get('status') == 'CRITICAL'])
        queries_error = len([r for r in self.results if r.get('status') == 'ERROR'])
        
        avg_time = sum([r.get('total_time_ms', 0) for r in self.results]) / total_queries if total_queries > 0 else 0
        
        queries_with_index = len([r for r in self.results if r.get('uses_index')])
        queries_without_index = total_queries - queries_with_index
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório de Performance - Sistema Financeiro DWM</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card.ok {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .summary-card.slow {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .summary-card.critical {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
        }}
        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
        }}
        .query-result {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .query-result.ok {{
            border-left-color: #27ae60;
        }}
        .query-result.slow {{
            border-left-color: #f39c12;
        }}
        .query-result.critical {{
            border-left-color: #e74c3c;
        }}
        .query-result.error {{
            border-left-color: #95a5a6;
        }}
        .query-name {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .query-metrics {{
            display: flex;
            gap: 20px;
            margin: 10px 0;
        }}
        .metric {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge.ok {{
            background: #27ae60;
            color: white;
        }}
        .badge.slow {{
            background: #f39c12;
            color: white;
        }}
        .badge.critical {{
            background: #e74c3c;
            color: white;
        }}
        .badge.yes {{
            background: #27ae60;
            color: white;
        }}
        .badge.no {{
            background: #e74c3c;
            color: white;
        }}
        code {{
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        .query-sql {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin: 10px 0;
        }}
        .timestamp {{
            text-align: right;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Relatório de Performance - Sistema Financeiro DWM</h1>
        <p>Análise de queries críticas com Row Level Security (RLS) ativo</p>
        
        <h2>📈 Resumo Geral</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>Total de Queries</h3>
                <div class="value">{total_queries}</div>
            </div>
            <div class="summary-card ok">
                <h3>✅ Queries OK (&lt;200ms)</h3>
                <div class="value">{queries_ok}</div>
            </div>
            <div class="summary-card slow">
                <h3>⚠️ Queries Lentas (200-500ms)</h3>
                <div class="value">{queries_slow}</div>
            </div>
            <div class="summary-card critical">
                <h3>🚨 Queries Críticas (&gt;500ms)</h3>
                <div class="value">{queries_critical}</div>
            </div>
            <div class="summary-card">
                <h3>Tempo Médio</h3>
                <div class="value">{avg_time:.0f}ms</div>
            </div>
            <div class="summary-card ok">
                <h3>Com Índice</h3>
                <div class="value">{queries_with_index}</div>
            </div>
        </div>
        
        <h2>🔍 Detalhamento das Queries</h2>
"""
        
        # Adiciona cada query analisada
        for result in self.results:
            status = result.get('status', 'UNKNOWN')
            query_name = result.get('query_name', 'Unknown')
            query = result.get('query', '')
            exec_time = result.get('execution_time_ms', 0)
            plan_time = result.get('planning_time_ms', 0)
            total_time = result.get('total_time_ms', 0)
            uses_index = result.get('uses_index', False)
            uses_seq_scan = result.get('uses_seq_scan', False)
            error = result.get('error')
            
            status_lower = status.lower()
            index_badge = 'yes' if uses_index else 'no'
            index_text = '✅ Sim' if uses_index else '❌ Não'
            
            html += f"""
        <div class="query-result {status_lower}">
            <div class="query-name">{query_name}</div>
            <div class="query-metrics">
                <div class="metric">
                    <strong>Status:</strong>
                    <span class="badge {status_lower}">{status}</span>
                </div>
                <div class="metric">
                    <strong>Tempo Total:</strong>
                    <code>{total_time:.2f}ms</code>
                </div>
                <div class="metric">
                    <strong>Execução:</strong>
                    <code>{exec_time:.2f}ms</code>
                </div>
                <div class="metric">
                    <strong>Planejamento:</strong>
                    <code>{plan_time:.2f}ms</code>
                </div>
                <div class="metric">
                    <strong>Usa Índice:</strong>
                    <span class="badge {index_badge}">{index_text}</span>
                </div>
            </div>
"""
            
            if error:
                html += f"""
            <div style="color: #e74c3c; margin: 10px 0;">
                <strong>❌ Erro:</strong> {error}
            </div>
"""
            
            if uses_seq_scan:
                html += """
            <div style="color: #f39c12; margin: 10px 0;">
                ⚠️ <strong>Atenção:</strong> Query usa Sequential Scan - considere adicionar índice
            </div>
"""
            
            html += f"""
            <div class="query-sql">{query}</div>
        </div>
"""
        
        html += f"""
        
        <h2>💡 Recomendações</h2>
        <ul>
            <li>✅ Queries com tempo &lt;200ms estão excelentes</li>
            <li>⚠️ Queries entre 200-500ms podem ser otimizadas</li>
            <li>🚨 Queries &gt;500ms DEVEM ser otimizadas urgentemente</li>
            <li>📌 Execute <code>create_rls_performance_indexes.sql</code> para criar índices otimizados</li>
            <li>🔄 Após criar índices, execute <code>ANALYZE</code> nas tabelas</li>
            <li>📊 Monitore queries lentas no log da aplicação</li>
        </ul>
        
        <div class="timestamp">
            Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        # Salva arquivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"📄 Relatório HTML gerado: {output_file}")
        return output_file
    
    def generate_json_report(self, output_file: str = 'relatorio_performance.json'):
        """Gera relatório JSON com os resultados"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'empresa_id_teste': self.empresa_id_teste,
            'total_queries': len(self.results),
            'queries_ok': len([r for r in self.results if r.get('status') == 'OK']),
            'queries_slow': len([r for r in self.results if r.get('status') == 'SLOW']),
            'queries_critical': len([r for r in self.results if r.get('status') == 'CRITICAL']),
            'queries_error': len([r for r in self.results if r.get('status') == 'ERROR']),
            'results': self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Relatório JSON gerado: {output_file}")
        return output_file


def main():
    """Função principal"""
    analyzer = PerformanceAnalyzer()
    
    try:
        # Executa todas as análises
        analyzer.run_all_analyses()
        
        # Gera relatórios
        html_file = analyzer.generate_html_report()
        json_file = analyzer.generate_json_report()
        
        logger.info("")
        logger.info("="*80)
        logger.info("✅ ANÁLISE DE PERFORMANCE CONCLUÍDA COM SUCESSO!")
        logger.info("="*80)
        logger.info(f"📄 Relatório HTML: {html_file}")
        logger.info(f"📄 Relatório JSON: {json_file}")
        logger.info("")
        logger.info("💡 Próximos passos:")
        logger.info("   1. Abra o relatório HTML no navegador")
        logger.info("   2. Execute create_rls_performance_indexes.sql no banco")
        logger.info("   3. Execute este script novamente para comparar")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {str(e)}")
        raise


if __name__ == "__main__":
    main()

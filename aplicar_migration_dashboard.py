#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migration de dashboard e relatórios de sessões
PARTE 9: Sistema completo de análise e métricas

Este script:
1. Cria 5 views de estatísticas
2. Cria 2 funções para análise
3. Cria 4 índices de performance
4. Testa queries de relatórios

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

import sys
import os
import psycopg2
from datetime import datetime, date, timedelta

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import DATABASE_CONFIG
except ImportError:
    print("⚠️  ERRO: Arquivo config.py não encontrado!")
    sys.exit(1)


def conectar_banco():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        print("✅ Conectado ao banco de dados PostgreSQL")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)


def aplicar_migration(cursor):
    """Aplica a migration de dashboard de sessões"""
    
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_dashboard_sessoes.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        return False
    
    print(f"\n📄 Lendo arquivo: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        print("\n🔄 Executando migration...")
        cursor.execute(sql_content)
        print("✅ Migration executada com sucesso!")
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        print(f"   Detalhes: {e.pgerror}")
        return False


def validar_migration(cursor):
    """Valida se a migration foi aplicada corretamente"""
    print("\n🔍 Validando migration...")
    
    erros = []
    
    # 1. Verificar views
    views_esperadas = [
        'vw_sessoes_estatisticas',
        'vw_sessoes_por_periodo',
        'vw_top_clientes_sessoes',
        'vw_comissoes_por_sessao',
        'vw_sessoes_atencao'
    ]
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_name IN %s
    """, (tuple(views_esperadas),))
    
    views_criadas = [row[0] for row in cursor.fetchall()]
    
    if len(views_criadas) == len(views_esperadas):
        print(f"   ✅ Todas as {len(views_esperadas)} views foram criadas")
    else:
        faltando = set(views_esperadas) - set(views_criadas)
        erros.append(f"Views faltando: {', '.join(faltando)}")
    
    # 2. Verificar funções
    funcoes_esperadas = ['obter_estatisticas_periodo', 'comparativo_periodos']
    
    cursor.execute("""
        SELECT proname 
        FROM pg_proc 
        WHERE proname IN %s
    """, (tuple(funcoes_esperadas),))
    
    funcoes_criadas = [row[0] for row in cursor.fetchall()]
    
    if len(funcoes_criadas) == len(funcoes_esperadas):
        print(f"   ✅ Todas as {len(funcoes_esperadas)} funções foram criadas")
    else:
        faltando = set(funcoes_esperadas) - set(funcoes_criadas)
        erros.append(f"Funções faltando: {', '.join(faltando)}")
    
    # 3. Verificar índices
    indices_esperados = [
        'idx_sessoes_empresa_data_status',
        'idx_sessoes_cliente_data',
        'idx_sessoes_prazo_status',
        'idx_comissoes_sessao_empresa'
    ]
    
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE indexname IN %s
    """, (tuple(indices_esperados),))
    
    indices = [row[0] for row in cursor.fetchall()]
    
    if len(indices) == len(indices_esperados):
        print(f"   ✅ Todos os {len(indices_esperados)} índices foram criados")
    else:
        faltando = set(indices_esperados) - set(indices)
        erros.append(f"Índices faltando: {', '.join(faltando)}")
    
    return len(erros) == 0, erros


def gerar_relatorio(cursor):
    """Gera relatório com testes das views e funções"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE TESTES")
    print("="*60)
    
    # Teste 1: Estatísticas gerais
    print("\n📈 Teste 1: Estatísticas Gerais (vw_sessoes_estatisticas)")
    try:
        cursor.execute("""
            SELECT 
                empresa_id,
                total_geral,
                total_concluidas,
                total_canceladas,
                valor_total_ativo,
                ticket_medio
            FROM vw_sessoes_estatisticas
            LIMIT 3
        """)
        
        resultados = cursor.fetchall()
        if resultados:
            print(f"   {'Empresa':<10} {'Total':<8} {'Concl.':<8} {'Cancel.':<8} {'Valor Total':<15} {'Ticket Médio':<15}")
            print("   " + "-" * 70)
            for empresa_id, total, concluidas, canceladas, valor_total, ticket in resultados:
                valor_fmt = f"R$ {valor_total:.2f}" if valor_total else "R$ 0,00"
                ticket_fmt = f"R$ {ticket:.2f}" if ticket else "R$ 0,00"
                print(f"   {empresa_id:<10} {total:<8} {concluidas:<8} {canceladas:<8} {valor_fmt:<15} {ticket_fmt:<15}")
        else:
            print("   ℹ️ Nenhuma sessão cadastrada ainda")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Top clientes
    print("\n🏆 Teste 2: Top 5 Clientes (vw_top_clientes_sessoes)")
    try:
        cursor.execute("""
            SELECT 
                cliente_nome,
                total_sessoes,
                valor_total,
                taxa_conclusao_pct
            FROM vw_top_clientes_sessoes
            LIMIT 5
        """)
        
        resultados = cursor.fetchall()
        if resultados:
            print(f"   {'Cliente':<30} {'Sessões':<10} {'Valor Total':<15} {'Taxa Conclusão':<15}")
            print("   " + "-" * 70)
            for nome, sessoes, valor, taxa in resultados:
                valor_fmt = f"R$ {valor:.2f}" if valor else "R$ 0,00"
                taxa_fmt = f"{taxa}%" if taxa else "N/A"
                print(f"   {nome:<30} {sessoes:<10} {valor_fmt:<15} {taxa_fmt:<15}")
        else:
            print("   ℹ️ Nenhuma sessão com cliente cadastrada ainda")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Sessões com atenção
    print("\n⚠️  Teste 3: Sessões Requerendo Atenção (vw_sessoes_atencao)")
    try:
        cursor.execute("""
            SELECT 
                cliente_nome,
                data,
                prazo_entrega,
                dias_ate_prazo,
                urgencia,
                valor_total
            FROM vw_sessoes_atencao
            WHERE urgencia IN ('ATRASADO', 'URGENTE - HOJE', 'URGENTE - 3 DIAS')
            LIMIT 5
        """)
        
        resultados = cursor.fetchall()
        if resultados:
            print(f"   {'Cliente':<25} {'Data':<12} {'Prazo':<12} {'Dias':<6} {'Urgência':<18} {'Valor':<12}")
            print("   " + "-" * 90)
            for nome, data, prazo, dias, urgencia, valor in resultados:
                data_fmt = data.strftime('%d/%m/%Y') if data else 'N/A'
                prazo_fmt = prazo.strftime('%d/%m/%Y') if prazo else 'N/A'
                valor_fmt = f"R$ {valor:.2f}" if valor else "R$ 0,00"
                print(f"   {nome:<25} {data_fmt:<12} {prazo_fmt:<12} {dias:<6} {urgencia:<18} {valor_fmt:<12}")
        else:
            print("   ✅ Nenhuma sessão requerendo atenção urgente")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Função obter_estatisticas_periodo
    print("\n📅 Teste 4: Função obter_estatisticas_periodo (últimos 30 dias)")
    try:
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()
        
        cursor.execute("""
            SELECT * FROM obter_estatisticas_periodo(1, %s, %s)
        """, (data_inicio, data_fim))
        
        resultado = cursor.fetchone()
        if resultado:
            labels = [
                'Total Sessões', 'Concluídas', 'Canceladas', 'Taxa Conclusão (%)',
                'Faturamento Total', 'Faturamento Entregue', 'Comissões Total',
                'Lucro Líquido', 'Ticket Médio', 'Horas Trabalhadas', 'Clientes Únicos'
            ]
            print(f"   Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
            print("   " + "-" * 50)
            for label, valor in zip(labels, resultado):
                if isinstance(valor, (int, float)):
                    if 'R$' in label or 'Total' in label or 'Líquido' in label or 'Médio' in label:
                        print(f"   {label:<25}: R$ {valor:,.2f}")
                    else:
                        print(f"   {label:<25}: {valor:,}")
                else:
                    print(f"   {label:<25}: {valor}")
        else:
            print("   ℹ️ Nenhuma sessão no período")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🚀 APLICANDO MIGRATION: DASHBOARD DE SESSÕES")
    print("="*60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Arquivo: migration_dashboard_sessoes.sql")
    
    conn = conectar_banco()
    cursor = conn.cursor()
    
    try:
        # Aplicar migration
        if not aplicar_migration(cursor):
            print("\n❌ Migration falhou!")
            conn.rollback()
            return
        
        # Validar
        sucesso, erros = validar_migration(cursor)
        
        if not sucesso:
            print("\n⚠️  AVISOS durante validação:")
            for erro in erros:
                print(f"   • {erro}")
            
            resposta = input("\n❓ Deseja fazer COMMIT mesmo assim? (s/N): ").strip().lower()
            if resposta != 's':
                print("❌ Rollback realizado")
                conn.rollback()
                return
        
        # Commit
        conn.commit()
        print("\n✅ COMMIT realizado com sucesso!")
        
        # Gerar relatório
        gerar_relatorio(cursor)
        
        print("\n" + "="*60)
        print("🎉 MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\n📝 Próximos passos:")
        print("   1. Criar endpoint GET /api/sessoes/dashboard")
        print("   2. Implementar frontend com gráficos")
        print("   3. Testar relatórios em produção")
        print("")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        conn.rollback()
        raise
        
    finally:
        cursor.close()
        conn.close()
        print("🔌 Conexão fechada")


if __name__ == "__main__":
    main()

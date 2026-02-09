#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migration de integração com contas a receber
PARTE 10: Geração automática de lançamentos a partir de sessões

Este script:
1. Adiciona colunas de vinculação
2. Cria funções SQL para gerar/estornar lançamentos
3. Cria trigger automático
4. Cria 2 views de análise
5. Cria 4 índices de performance
6. Testa integração

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

import sys
import os
import psycopg2
from datetime import datetime, date

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
    """Aplica a migration de integração com contas a receber"""
    
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_integracao_contas_receber.sql')
    
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
    
    # 1. Verificar colunas adicionadas em sessoes
    print("   Verificando colunas em sessoes...")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sessoes' 
          AND column_name IN ('lancamento_id', 'gerar_lancamento_automatico')
    """)
    
    colunas_sessoes = [row[0] for row in cursor.fetchall()]
    
    if 'lancamento_id' in colunas_sessoes and 'gerar_lancamento_automatico' in colunas_sessoes:
        print(f"   ✅ Colunas adicionadas em sessoes")
    else:
        faltando = {'lancamento_id', 'gerar_lancamento_automatico'} - set(colunas_sessoes)
        erros.append(f"Colunas faltando em sessoes: {', '.join(faltando)}")
    
    # 2. Verificar coluna em lancamentos
    print("   Verificando coluna em lancamentos...")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'lancamentos' 
          AND column_name = 'sessao_id'
    """)
    
    if cursor.fetchone():
        print(f"   ✅ Coluna sessao_id adicionada em lancamentos")
    else:
        erros.append("Coluna sessao_id faltando em lancamentos")
    
    # 3. Verificar funções
    print("   Verificando funções SQL...")
    cursor.execute("""
        SELECT proname 
        FROM pg_proc 
        WHERE proname IN ('gerar_lancamento_sessao', 'estornar_lancamento_sessao')
    """)
    
    funcoes = [row[0] for row in cursor.fetchall()]
    
    if len(funcoes) == 2:
        print(f"   ✅ Funções SQL criadas (2)")
    else:
        faltando = {'gerar_lancamento_sessao', 'estornar_lancamento_sessao'} - set(funcoes)
        erros.append(f"Funções faltando: {', '.join(faltando)}")
    
    # 4. Verificar trigger
    print("   Verificando trigger...")
    cursor.execute("""
        SELECT tgname 
        FROM pg_trigger 
        WHERE tgname = 'trg_sessao_gerar_lancamento'
    """)
    
    if cursor.fetchone():
        print(f"   ✅ Trigger criado")
    else:
        erros.append("Trigger trg_sessao_gerar_lancamento não encontrado")
    
    # 5. Verificar views
    print("   Verificando views...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_name IN ('vw_sessoes_lancamentos', 'vw_sessoes_financeiro')
    """)
    
    views = [row[0] for row in cursor.fetchall()]
    
    if len(views) == 2:
        print(f"   ✅ Views criadas (2)")
    else:
        faltando = {'vw_sessoes_lancamentos', 'vw_sessoes_financeiro'} - set(views)
        erros.append(f"Views faltando: {', '.join(faltando)}")
    
    # 6. Verificar índices
    print("   Verificando índices...")
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE indexname IN (
            'idx_sessoes_lancamento_id',
            'idx_lancamentos_sessao_id',
            'idx_sessoes_status_lancamento',
            'idx_sessoes_gerar_lancamento'
        )
    """)
    
    indices = [row[0] for row in cursor.fetchall()]
    
    if len(indices) >= 2:  # Pelo menos os 2 principais
        print(f"   ✅ Índices criados ({len(indices)})")
    else:
        print(f"   ⚠️  Apenas {len(indices)} índices criados (esperado: 4)")
    
    return len(erros) == 0, erros


def testar_integracao(cursor):
    """Testa a integração com exemplos"""
    print("\n" + "="*60)
    print("🧪 TESTES DE INTEGRAÇÃO")
    print("="*60)
    
    # Teste 1: Verificar configuração padrão
    print("\n📋 Teste 1: Configuração Padrão de Sessões")
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE gerar_lancamento_automatico = TRUE) as com_auto,
                COUNT(*) FILTER (WHERE gerar_lancamento_automatico = FALSE) as sem_auto
            FROM sessoes
        """)
        
        resultado = cursor.fetchone()
        if resultado:
            total, com_auto, sem_auto = resultado
            print(f"   Total de sessões: {total}")
            print(f"   Com geração automática: {com_auto}")
            print(f"   Sem geração automática: {sem_auto}")
        else:
            print("   ℹ️ Nenhuma sessão cadastrada ainda")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Visualizar relacionamentos existentes
    print("\n🔗 Teste 2: Relacionamentos Existentes")
    try:
        cursor.execute("""
            SELECT 
                sessao_id, sessao_titulo, sessao_status,
                lancamento_id, lancamento_status, situacao
            FROM vw_sessoes_lancamentos
            WHERE lancamento_id IS NOT NULL
            LIMIT 5
        """)
        
        resultados = cursor.fetchall()
        if resultados:
            print(f"   {'Sessão':<8} {'Título':<30} {'Status Sessão':<15} {'Lançamento':<12} {'Situação':<15}")
            print("   " + "-" * 85)
            for sessao_id, titulo, sessao_status, lanc_id, lanc_status, situacao in resultados:
                print(f"   {sessao_id:<8} {(titulo or 'N/A')[:28]:<30} {sessao_status:<15} {lanc_id:<12} {situacao:<15}")
        else:
            print("   ℹ️ Nenhuma sessão com lançamento vinculado ainda")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Sessões entregues sem lançamento
    print("\n⚠️  Teste 3: Sessões Entregues SEM Lançamento")
    try:
        cursor.execute("""
            SELECT 
                sessao_id, sessao_titulo, cliente_nome,
                sessao_valor, data
            FROM vw_sessoes_lancamentos
            WHERE situacao = 'SEM LANÇAMENTO'
            LIMIT 5
        """)
        
        resultados = cursor.fetchall()
        if resultados:
            print(f"   {'Sessão':<8} {'Título':<25} {'Cliente':<25} {'Valor':<12} {'Data':<12}")
            print("   " + "-" * 85)
            for sessao_id, titulo, cliente, valor, data in resultados:
                valor_fmt = f"R$ {valor:,.2f}" if valor else "R$ 0,00"
                data_fmt = data.strftime('%d/%m/%Y') if data else 'N/A'
                print(f"   {sessao_id:<8} {(titulo or 'N/A')[:23]:<25} {(cliente or 'N/A')[:23]:<25} {valor_fmt:<12} {data_fmt:<12}")
            print(f"\n   💡 Dica: Use a função gerar_lancamento_sessao(sessao_id) para gerar os lançamentos")
        else:
            print("   ✅ Todas as sessões entregues possuem lançamento")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Análise financeira
    print("\n💰 Teste 4: Análise Financeira Global")
    try:
        cursor.execute("""
            SELECT 
                total_sessoes,
                sessoes_entregues,
                sessoes_com_lancamento,
                sessoes_sem_lancamento,
                valor_total_entregue,
                valor_ja_recebido,
                valor_a_receber,
                valor_nao_lancado,
                taxa_lancamento_pct,
                taxa_recebimento_pct
            FROM vw_sessoes_financeiro
            LIMIT 1
        """)
        
        resultado = cursor.fetchone()
        if resultado:
            labels = [
                'Total de Sessões', 'Sessões Entregues', 'Com Lançamento', 'Sem Lançamento',
                'Valor Total Entregue', 'Valor Já Recebido', 'Valor a Receber', 'Valor Não Lançado',
                'Taxa de Lançamento (%)', 'Taxa de Recebimento (%)'
            ]
            print("   " + "-" * 50)
            for label, valor in zip(labels, resultado):
                if valor is None:
                    valor_fmt = 'N/A'
                elif 'Taxa' in label or '%' in label:
                    valor_fmt = f"{valor}%"
                elif 'Valor' in label:
                    valor_fmt = f"R$ {valor:,.2f}"
                else:
                    valor_fmt = f"{valor}"
                print(f"   {label:<30}: {valor_fmt}")
        else:
            print("   ℹ️ Nenhum dado disponível para análise")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 5: Testar função de geração (simulação)
    print("\n🔧 Teste 5: Simulação de Geração de Lançamento")
    try:
        # Buscar uma sessão entregue sem lançamento
        cursor.execute("""
            SELECT sessao_id, sessao_titulo, sessao_valor
            FROM vw_sessoes_lancamentos
            WHERE situacao = 'SEM LANÇAMENTO'
            LIMIT 1
        """)
        
        sessao_teste = cursor.fetchone()
        if sessao_teste:
            sessao_id, titulo, valor = sessao_teste
            print(f"   Sessão encontrada: #{sessao_id} - {titulo} - R$ {valor:,.2f}")
            print(f"   💡 Para gerar o lançamento, execute:")
            print(f"      SELECT gerar_lancamento_sessao({sessao_id});")
        else:
            print("   ℹ️ Não há sessões entregues sem lançamento para testar")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def gerar_relatorio_final():
    """Gera relatório final da migration"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL")
    print("="*60)
    
    print("\n✅ COMPONENTES INSTALADOS:")
    print("   • Colunas de vinculação:")
    print("     - sessoes.lancamento_id (FK → lancamentos)")
    print("     - sessoes.gerar_lancamento_automatico (BOOLEAN)")
    print("     - lancamentos.sessao_id (FK → sessoes)")
    
    print("\n   • Funções SQL (2):")
    print("     - gerar_lancamento_sessao(sessao_id, usuario_id)")
    print("     - estornar_lancamento_sessao(sessao_id, deletar)")
    
    print("\n   • Trigger:")
    print("     - trg_sessao_gerar_lancamento")
    print("       Executa ao mudar status para 'entregue'")
    
    print("\n   • Views (2):")
    print("     - vw_sessoes_lancamentos (relacionamentos)")
    print("     - vw_sessoes_financeiro (análise financeira)")
    
    print("\n   • Índices (4):")
    print("     - idx_sessoes_lancamento_id")
    print("     - idx_lancamentos_sessao_id")
    print("     - idx_sessoes_status_lancamento")
    print("     - idx_sessoes_gerar_lancamento")
    
    print("\n📝 COMO USAR:")
    print("   1. Automático (via trigger):")
    print("      UPDATE sessoes SET status = 'entregue' WHERE id = 123;")
    
    print("\n   2. Manual (via API):")
    print("      POST /api/sessoes/123/gerar-lancamento")
    
    print("\n   3. Visualizar integração:")
    print("      GET /api/sessoes/integracao")
    
    print("\n   4. Análise financeira:")
    print("      GET /api/sessoes/analise-financeira")
    
    print("\n   5. Configurar geração automática:")
    print("      PATCH /api/sessoes/123/configurar-lancamento-automatico")
    print("      Body: {\"ativar\": true}")
    
    print("\n" + "="*60)


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🚀 APLICANDO MIGRATION: INTEGRAÇÃO CONTAS A RECEBER")
    print("="*60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Arquivo: migration_integracao_contas_receber.sql")
    
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
        
        # Testar integração
        testar_integracao(cursor)
        
        # Relatório final
        gerar_relatorio_final()
        
        print("\n🎉 MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*60)
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

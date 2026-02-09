#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migration de comissões calculadas automaticamente
PARTE 8: Sistema de cálculo automático de comissões

Este script:
1. Adiciona 4 campos novos em comissoes (sessao_id, valor_calculado, calculo_automatico, base_calculo)
2. Cria função calcular_valor_comissao() para calcular baseado em tipo/percentual/base
3. Cria função formatar_comissao() para exibição formatada
4. Cria 3 triggers automáticos (comissão, sessão, contrato)
5. Cria view vw_comissoes_calculadas
6. Atualiza comissões existentes com valor_calculado
7. Cria 3 índices de performance

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

import sys
import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import DATABASE_CONFIG
except ImportError:
    print("⚠️  ERRO: Arquivo config.py não encontrado!")
    print("   Certifique-se de que DATABASE_CONFIG está configurado")
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


def verificar_campos_existentes(cursor):
    """Verifica se os campos de comissão calculada já existem"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'comissoes' 
          AND column_name IN ('sessao_id', 'valor_calculado', 'calculo_automatico', 'base_calculo')
        ORDER BY column_name
    """)
    campos_existentes = [row[0] for row in cursor.fetchall()]
    return campos_existentes


def contar_comissoes(cursor):
    """Conta total de comissões"""
    cursor.execute("SELECT COUNT(*) FROM comissoes")
    return cursor.fetchone()[0]


def contar_comissoes_por_tipo(cursor):
    """Estatísticas de comissões por tipo"""
    cursor.execute("""
        SELECT 
            tipo,
            COUNT(*) as total,
            AVG(COALESCE(valor, 0)) as media_valor,
            AVG(COALESCE(percentual, 0)) as media_percentual
        FROM comissoes
        GROUP BY tipo
        ORDER BY total DESC
    """)
    return cursor.fetchall()


def aplicar_migration(cursor):
    """Aplica a migration de comissões calculadas"""
    
    # Ler arquivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_comissoes_calculadas.sql')
    
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
    
    # 1. Verificar se os campos foram criados
    campos_esperados = ['sessao_id', 'valor_calculado', 'calculo_automatico', 'base_calculo']
    campos_existentes = verificar_campos_existentes(cursor)
    
    campos_faltando = set(campos_esperados) - set(campos_existentes)
    if campos_faltando:
        erros.append(f"Campos faltando: {', '.join(campos_faltando)}")
    else:
        print(f"   ✅ Todos os {len(campos_esperados)} campos foram criados")
    
    # 2. Verificar se a função calcular_valor_comissao foi criada
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pg_proc 
        WHERE proname = 'calcular_valor_comissao'
    """)
    if cursor.fetchone()[0] > 0:
        print("   ✅ Função calcular_valor_comissao() criada")
    else:
        erros.append("Função calcular_valor_comissao() não encontrada")
    
    # 3. Verificar se a função formatar_comissao foi criada
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pg_proc 
        WHERE proname = 'formatar_comissao'
    """)
    if cursor.fetchone()[0] > 0:
        print("   ✅ Função formatar_comissao() criada")
    else:
        erros.append("Função formatar_comissao() não encontrada")
    
    # 4. Verificar se os triggers foram criados
    cursor.execute("""
        SELECT trigger_name 
        FROM information_schema.triggers 
        WHERE trigger_name IN (
            'trg_comissao_calculada_insert_update',
            'trg_sessao_atualiza_comissoes',
            'trg_contrato_atualiza_comissoes'
        )
    """)
    triggers = [row[0] for row in cursor.fetchall()]
    
    if len(triggers) == 3:
        print(f"   ✅ Todos os 3 triggers criados")
    else:
        erros.append(f"Apenas {len(triggers)}/3 triggers criados")
    
    # 5. Verificar se a view foi criada
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.views 
        WHERE table_name = 'vw_comissoes_calculadas'
    """)
    if cursor.fetchone()[0] > 0:
        print("   ✅ View vw_comissoes_calculadas criada")
    else:
        erros.append("View vw_comissoes_calculadas não encontrada")
    
    # 6. Verificar se os índices foram criados
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = 'comissoes' 
          AND indexname IN ('idx_comissoes_sessao', 'idx_comissoes_contrato', 'idx_comissoes_auto_calculo')
    """)
    indices = [row[0] for row in cursor.fetchall()]
    
    if len(indices) == 3:
        print(f"   ✅ Todos os 3 índices criados")
    else:
        erros.append(f"Apenas {len(indices)}/3 índices criados")
    
    return len(erros) == 0, erros


def gerar_relatorio(cursor):
    """Gera relatório pós-migration"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DA MIGRATION")
    print("="*60)
    
    # Total de comissões
    total = contar_comissoes(cursor)
    print(f"\n📋 Total de comissões: {total}")
    
    # Comissões por tipo
    print(f"\n🎯 Comissões por Tipo:")
    print(f"{'Tipo':<15} {'Total':<10} {'Média Valor':<15} {'Média %':<10}")
    print("-" * 60)
    
    stats = contar_comissoes_por_tipo(cursor)
    for tipo, qtd, media_valor, media_percentual in stats:
        valor_fmt = f"R$ {media_valor:.2f}" if media_valor else "N/A"
        perc_fmt = f"{media_percentual:.1f}%" if media_percentual else "N/A"
        print(f"{tipo:<15} {qtd:<10} {valor_fmt:<15} {perc_fmt:<10}")
    
    # Comissões com valor calculado
    cursor.execute("""
        SELECT COUNT(*) 
        FROM comissoes 
        WHERE valor_calculado IS NOT NULL
    """)
    com_calculo = cursor.fetchone()[0]
    
    print(f"\n💰 Comissões com valor_calculado: {com_calculo}/{total}")
    if total > 0:
        percentual = (com_calculo / total * 100)
        print(f"   ({percentual:.1f}% do total)")
    
    # Teste da função calcular_valor_comissao
    print("\n🧪 Teste das funções criadas:")
    
    # Testar calcular_valor_comissao
    cursor.execute("""
        SELECT calcular_valor_comissao(id) as calc, valor_calculado, tipo, percentual
        FROM comissoes
        WHERE calculo_automatico = true
        LIMIT 3
    """)
    
    resultados = cursor.fetchall()
    if resultados:
        print("   Exemplos de cálculos:")
        for calc, valor_calc, tipo, percentual in resultados:
            print(f"   • Tipo: {tipo}, Percentual: {percentual}% → Calculado: R$ {calc:.2f if calc else 0:.2f}")
    else:
        print("   Nenhuma comissão com cálculo automático ainda")
    
    # Testar formatar_comissao
    cursor.execute("""
        SELECT formatar_comissao(id) as formatado
        FROM comissoes
        LIMIT 3
    """)
    
    formatados = cursor.fetchall()
    if formatados:
        print("\n   Exemplos de formatação:")
        for (formatado,) in formatados:
            print(f"   • {formatado}")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🚀 APLICANDO MIGRATION: COMISSÕES CALCULADAS")
    print("="*60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Arquivo: migration_comissoes_calculadas.sql")
    
    # Conectar ao banco
    conn = conectar_banco()
    cursor = conn.cursor()
    
    try:
        # Verificar estado atual
        print("\n🔍 Verificando estado atual...")
        campos_existentes = verificar_campos_existentes(cursor)
        
        if campos_existentes:
            print(f"⚠️  Atenção: {len(campos_existentes)} campos já existem:")
            for campo in campos_existentes:
                print(f"   • {campo}")
            
            resposta = input("\n❓ Deseja continuar mesmo assim? (s/N): ").strip().lower()
            if resposta != 's':
                print("❌ Operação cancelada pelo usuário")
                return
        
        total_comissoes = contar_comissoes(cursor)
        print(f"   Total de comissões existentes: {total_comissoes}")
        
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
        print("   1. Atualizar backend para usar campos novos")
        print("   2. Atualizar frontend para mostrar valor_calculado")
        print("   3. Testar cálculo automático ao criar/editar sessão")
        print("   4. Verificar atualização em tempo real")
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

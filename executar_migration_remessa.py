#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar migration de Remessa de Pagamento Sicredi
Executa DIRETAMENTE no banco do Railway via PostgreSQL
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

print("="*80)
print("🏦 EXECUTANDO MIGRATION - REMESSA DE PAGAMENTO SICREDI")
print("="*80)

# URL de conexão do Railway
DATABASE_URL = os.getenv('DATABASE_URL') or input("\n📝 Cole a DATABASE_URL do Railway: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL não fornecida!")
    sys.exit(1)

try:
    print("\n📡 Conectando ao PostgreSQL do Railway...")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("✅ Conexão estabelecida!")
    
    # Verificar se tabelas já existem
    print("\n🔍 Verificando tabelas existentes...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('remessas_pagamento', 'remessas_pagamento_itens', 'sicredi_configuracao')
    """)
    
    count = cursor.fetchone()['count']
    print(f"   📊 Encontradas {count}/3 tabelas do módulo Remessa")
    
    if count > 0:
        print("\n⚠️  ATENÇÃO: Algumas tabelas já existem!")
        
        # Contar remessas se existir
        try:
            cursor.execute("SELECT COUNT(*) as total FROM remessas_pagamento")
            total_remessas = cursor.fetchone()['total']
            print(f"   📋 {total_remessas} remessas cadastradas")
        except:
            pass
        
        resposta = input("\n⚠️ Deseja RECRIAR as tabelas? Isso apagará todos os dados! (s/N): ").lower()
        if resposta != 's':
            print("\n✅ Operação cancelada - tabelas preservadas")
            cursor.close()
            conn.close()
            sys.exit(0)
        
        print("\n🗑️ Removendo tabelas antigas...")
        cursor.execute("DROP TABLE IF EXISTS remessas_pagamento_itens CASCADE")
        cursor.execute("DROP TABLE IF EXISTS remessas_pagamento CASCADE")
        cursor.execute("DROP TABLE IF EXISTS sicredi_configuracao CASCADE")
        cursor.execute("DROP VIEW IF EXISTS v_remessas_resumo CASCADE")
        cursor.execute("DROP VIEW IF EXISTS v_contas_pagar_pendentes_remessa CASCADE")
        cursor.execute("DROP FUNCTION IF EXISTS obter_proximo_sequencial_remessa(INTEGER) CASCADE")
        conn.commit()
        print("✅ Tabelas antigas removidas")
    
    # Ler arquivo SQL
    print("\n📂 Lendo arquivo SQL da migration...")
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_remessa_pagamento.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Arquivo não encontrado: {sql_file}")
        print(f"   Procurando em: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content)} bytes)")
    print(f"   📄 Arquivo: migration_remessa_pagamento.sql")
    
    # Executar SQL
    print("\n📝 Executando migration...")
    print("   ⏳ Criando tabelas...")
    print("   ⏳ Criando views...")
    print("   ⏳ Criando funções...")
    print("   ⏳ Criando triggers...")
    print("   ⏳ Criando permissões...")
    
    cursor.execute(sql_content)
    conn.commit()
    
    print("✅ SQL executado e commitado com sucesso!")
    
    # Verificar criação
    print("\n✅ Verificando estrutura criada...")
    
    # Verificar tabelas
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%remessa%' OR table_name = 'sicredi_configuracao'
        ORDER BY table_name
    """)
    tabelas = cursor.fetchall()
    print(f"\n📊 Tabelas criadas ({len(tabelas)}):")
    for t in tabelas:
        print(f"   ✓ {t['table_name']}")
    
    # Verificar views
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%remessa%'
        ORDER BY table_name
    """)
    views = cursor.fetchall()
    print(f"\n👁️ Views criadas ({len(views)}):")
    for v in views:
        print(f"   ✓ {v['table_name']}")
    
    # Verificar função
    cursor.execute("""
        SELECT routine_name 
        FROM information_schema.routines 
        WHERE routine_schema = 'public' 
        AND routine_name LIKE '%remessa%'
    """)
    funcoes = cursor.fetchall()
    print(f"\n⚙️ Funções criadas ({len(funcoes)}):")
    for f in funcoes:
        print(f"   ✓ {f['routine_name']}()")
    
    # Verificar permissões
    cursor.execute("""
        SELECT codigo, nome 
        FROM permissoes 
        WHERE codigo LIKE 'remessa_%'
        ORDER BY codigo
    """)
    permissoes = cursor.fetchall()
    print(f"\n🔐 Permissões criadas ({len(permissoes)}):")
    for p in permissoes:
        print(f"   ✓ {p['codigo']} - {p['nome']}")
    
    # Verificar triggers
    cursor.execute("""
        SELECT trigger_name, event_object_table
        FROM information_schema.triggers 
        WHERE trigger_schema = 'public' 
        AND event_object_table LIKE '%remessa%' OR event_object_table = 'sicredi_configuracao'
        ORDER BY event_object_table, trigger_name
    """)
    triggers = cursor.fetchall()
    print(f"\n⚡ Triggers criados ({len(triggers)}):")
    for tr in triggers:
        print(f"   ✓ {tr['trigger_name']} em {tr['event_object_table']}")
    
    print("\n" + "="*80)
    print("🎉 MIGRATION CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\n✅ Módulo de Remessa de Pagamento Sicredi instalado!")
    print("\n📋 Próximos passos:")
    print("   1. Configurar permissões para grupos/usuários")
    print("   2. Acessar 'Remessa Pagamentos' no sistema")
    print("   3. Configurar convênio Sicredi")
    print("   4. Gerar primeira remessa de teste")
    print("\n💡 Documentação completa: DOCS_REMESSA_PAGAMENTO_COMPLETO.md")
    
    cursor.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"\n❌ ERRO NO BANCO DE DADOS:")
    print(f"   {e}")
    print(f"\n💡 Dica: Verifique se a DATABASE_URL está correta")
    sys.exit(1)
    
except FileNotFoundError as e:
    print(f"\n❌ ERRO: Arquivo não encontrado")
    print(f"   {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERRO INESPERADO:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

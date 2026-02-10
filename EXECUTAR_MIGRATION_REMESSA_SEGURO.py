#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTA MIGRATION REMESSA - USA CONEXÃO DO PRÓPRIO PROJETO
Mais seguro: Usa database_postgresql.py já configurado
"""
import sys
import os

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# CARREGAR .ENV MANUALMENTE (antes de importar database_postgresql)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

print("="*80)
print("🏦 EXECUTANDO MIGRATION - REMESSA PAGAMENTO SICREDI")
print("="*80)

try:
    # Importar módulo de banco já configurado
    print("\n📦 Importando database_postgresql...")
    import database_postgresql as db
    print("✅ Módulo de banco importado!")
    
    # Conectar ao banco
    print("\n📡 Conectando ao PostgreSQL...")
    conn = db.get_connection()
    cursor = conn.cursor()
    print("✅ Conectado!")
    
    # Verificar tabelas existentes
    print("\n🔍 Verificando tabelas existentes...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('remessas_pagamento', 'remessas_pagamento_itens', 'sicredi_configuracao')
    """)
    result = cursor.fetchone()
    count = result['count'] if isinstance(result, dict) else result[0]
    print(f"   Encontradas: {count}/3 tabelas")
    
    if count == 3:
        print("\n✅ TABELAS JÁ EXISTEM!")
        cursor.execute("SELECT COUNT(*) as total FROM remessas_pagamento")
        result = cursor.fetchone()
        total = result['total'] if isinstance(result, dict) else result[0]
        print(f"   📋 {total} remessas cadastradas")
        cursor.close()
        conn.close()
        print("\n✅ Módulo já instalado - nada a fazer!")
        input("\nPressione ENTER para sair...")
        sys.exit(0)
    
    # Ler arquivo SQL
    print("\n📂 Lendo migration_remessa_pagamento.sql...")
    sql_path = os.path.join(os.path.dirname(__file__), 'migration_remessa_pagamento.sql')
    
    if not os.path.exists(sql_path):
        print(f"❌ ERRO: Arquivo não encontrado!")
        print(f"   Procurado em: {sql_path}")
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL lido ({len(sql_content):,} caracteres)")
    
    # Executar SQL
    print("\n📝 EXECUTANDO MIGRATION...")
    print("   ⏳ Criando tabelas...")
    print("   ⏳ Criando views...")
    print("   ⏳ Criando funções...")
    print("   ⏳ Criando permissões...")
    print("   ⏳ Criando triggers...")
    
    cursor.execute(sql_content)
    conn.commit()
    print("✅ SQL EXECUTADO E COMMITADO!")
    
    # Verificar resultado
    print("\n🔍 Verificando estrutura criada...")
    
    # Tabelas
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('remessas_pagamento', 'remessas_pagamento_itens', 'sicredi_configuracao')
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"\n📊 {len(tables)} TABELAS CRIADAS:")
    for table in tables:
        name = table['table_name'] if isinstance(table, dict) else table[0]
        print(f"   ✓ {name}")
    
    # Views
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        AND table_name LIKE '%remessa%'
        ORDER BY table_name
    """)
    views = cursor.fetchall()
    print(f"\n👁️  {len(views)} VIEWS CRIADAS:")
    for view in views:
        name = view['table_name'] if isinstance(view, dict) else view[0]
        print(f"   ✓ {name}")
    
    # Funções
    cursor.execute("""
        SELECT routine_name 
        FROM information_schema.routines 
        WHERE routine_schema = 'public'
        AND routine_name LIKE '%remessa%'
        ORDER BY routine_name
    """)
    functions = cursor.fetchall()
    print(f"\n⚙️  {len(functions)} FUNÇÕES CRIADAS:")
    for func in functions:
        name = func['routine_name'] if isinstance(func, dict) else func[0]
        print(f"   ✓ {name}()")
    
    # Permissões
    cursor.execute("""
        SELECT codigo, nome 
        FROM permissoes 
        WHERE codigo LIKE 'remessa_%'
        ORDER BY codigo
    """)
    perms = cursor.fetchall()
    print(f"\n🔐 {len(perms)} PERMISSÕES CRIADAS:")
    for perm in perms:
        codigo = perm['codigo'] if isinstance(perm, dict) else perm[0]
        nome = perm['nome'] if isinstance(perm, dict) else perm[1]
        print(f"   ✓ {codigo} - {nome}")
    
    # Triggers
    cursor.execute("""
        SELECT trigger_name, event_object_table
        FROM information_schema.triggers 
        WHERE trigger_schema = 'public'
        AND (event_object_table LIKE '%remessa%' OR event_object_table = 'sicredi_configuracao')
        ORDER BY event_object_table, trigger_name
    """)
    triggers = cursor.fetchall()
    print(f"\n⚡ {len(triggers)} TRIGGERS CRIADOS:")
    for trigger in triggers:
        trig_name = trigger['trigger_name'] if isinstance(trigger, dict) else trigger[0]
        table_name = trigger['event_object_table'] if isinstance(trigger, dict) else trigger[1]
        print(f"   ✓ {trig_name} em {table_name}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅✅✅ MIGRATION CONCLUÍDA COM SUCESSO! ✅✅✅")
    print("="*80)
    print("\n📋 Próximos passos:")
    print("   1. Configure permissões para grupos/usuários no sistema")
    print("   2. Acesse 'Remessa Pagamentos' no menu")
    print("   3. Configure convênio Sicredi (primeira vez)")
    print("   4. Gere remessa de teste")
    print("\n🔄 Deploy Railway já deve estar concluído")
    print("✅ Módulo de Remessa de Pagamento Sicredi está FUNCIONANDO!")
    
    input("\n\nPressione ENTER para sair...")
    
except ModuleNotFoundError as e:
    print(f"\n❌ ERRO: Módulo não encontrado!")
    print(f"   {e}")
    print("\n💡 Solução: Instale as dependências:")
    print("   pip install psycopg2-binary")
    input("\nPressione ENTER para sair...")
    sys.exit(1)
    
except FileNotFoundError as e:
    print(f"\n❌ ERRO: Arquivo não encontrado!")
    print(f"   {e}")
    print("   Certifique-se de estar no diretório correto")
    input("\nPressione ENTER para sair...")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERRO:")
    print(f"   {e}")
    print("\n📋 Detalhes:")
    import traceback
    traceback.print_exc()
    input("\nPressione ENTER para sair...")
    sys.exit(1)

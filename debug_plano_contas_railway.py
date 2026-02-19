"""
Script manual para verificar Plano de Contas - CONEXÃO DIRETA
Cole a DATABASE_URL do Railway quando solicitado
"""
import psycopg2
from psycopg2.extras import RealDictCursor

print("="*80)
print("🔍 VERIFICAÇÃO MANUAL - PLANO DE CONTAS")
print("="*80)
print()

DATABASE_URL = input("📋 Cole a DATABASE_URL do Railway: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL vazia!")
    exit(1)

print(f"\n🔗 Conectando: {DATABASE_URL[:30]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Conectado!\n")
    
    # =============================================================================
    # VERIFICAR TABELAS
    # =============================================================================
    
    print("📊 VERIFICANDO TABELAS...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('plano_contas_versao', 'plano_contas')
    """)
    
    tabelas = [r['table_name'] for r in cursor.fetchall()]
    print(f"   ✅ Tabelas encontradas: {tabelas}\n")
    
    if 'plano_contas_versao' not in tabelas:
        print("❌ TABELA 'plano_contas_versao' NÃO EXISTE!")
        print("   Execute o script de migração: migration_plano_contas.py\n")
        exit(1)
    
    # =============================================================================
    # VERIFICAR DADOS - EMPRESA 20 (COOPSERVICOS)
    # =============================================================================
    
    print("🔍 VERIFICANDO EMPRESA 20 (COOPSERVICOS)...\n")
    
    # Teste 1: SELECT simples
    print("📋 Teste 1: SELECT simples (fetchall)")
    cursor.execute("""
        SELECT id, nome_versao, exercicio_fiscal, is_ativa
        FROM plano_contas_versao
        WHERE empresa_id = 20
        ORDER BY id
    """)
    
    rows = cursor.fetchall()
    print(f"   Total de registros: {len(rows)}")
    
    if rows:
        print(f"   Tipo do primeiro registro: {type(rows[0])}")
        print(f"   Conteúdo do primeiro registro:")
        print(f"   {rows[0]}\n")
    else:
        print("   ⚠️ NENHUM REGISTRO ENCONTRADO!\n")
    
    # Teste 2: Verificar colunas
    print("📋 Teste 2: Verificar descrição das colunas")
    cursor.execute("""
        SELECT id, nome_versao, exercicio_fiscal
        FROM plano_contas_versao
        WHERE empresa_id = 20
        LIMIT 1
    """)
    
    print(f"   Descrição do cursor: {cursor.description}")
    
    if cursor.description:
        colunas = [desc[0] for desc in cursor.description]
        print(f"   Nomes das colunas: {colunas}")
        
        row = cursor.fetchone()
        if row:
            print(f"   Tipo do row: {type(row)}")
            print(f"   Conteúdo do row: {row}")
            print(f"   row['id']: {row.get('id')}")
            print(f"   row['nome_versao']: {row.get('nome_versao')}\n")
        else:
            print("   ⚠️ fetchone() retornou None\n")
    
    # Teste 3: Verificar se há dados mas estão ocultos
    print("📋 Teste 3: Contar registros")
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM plano_contas_versao
        WHERE empresa_id = 20
    """)
    
    count = cursor.fetchone()
    print(f"   Total de registros (COUNT): {count['total']}\n")
    
    # Teste 4: Listar TODOS os registros (sem WHERE)
    print("📋 Teste 4: Listar TODAS as versões (sem filtro de empresa)")
    cursor.execute("""
        SELECT empresa_id, id, nome_versao, exercicio_fiscal, is_ativa
        FROM plano_contas_versao
        ORDER BY empresa_id, id
    """)
    
    all_rows = cursor.fetchall()
    print(f"   Total de registros no sistema: {len(all_rows)}")
    
    if all_rows:
        print("\n   📋 Registros encontrados:")
        for r in all_rows:
            print(f"      Empresa {r['empresa_id']}: ID {r['id']} - {r['nome_versao']} ({r['exercicio_fiscal']}) Ativa={r['is_ativa']}")
    else:
        print("   ⚠️ NENHUM REGISTRO EM TODO O SISTEMA!\n")
    
    print()
    print("="*80)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("="*80)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

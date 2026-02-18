"""
Script para APLICAR correção de subcategorias e evento_fornecedores DIRETO NO RAILWAY
Executa AGORA a correção do erro 500
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔧 APLICANDO CORREÇÃO - SUBCATEGORIAS E EVENTO_FORNECEDORES")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # ========================================================================
    # 1. VERIFICAR E ADICIONAR COLUNA 'ativa' NA TABELA SUBCATEGORIAS
    # ========================================================================
    print("\n📋 1. Verificando tabela subcategorias...")
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'subcategorias' 
            AND column_name = 'ativa'
        );
    """)
    
    coluna_ativa_existe = cursor.fetchone()['exists']
    
    if coluna_ativa_existe:
        print("   ✅ Coluna 'ativa' já existe")
    else:
        print("   ⚠️  Coluna 'ativa' não existe - ADICIONANDO...")
        
        cursor.execute("""
            ALTER TABLE subcategorias ADD COLUMN ativa BOOLEAN DEFAULT TRUE;
        """)
        
        cursor.execute("""
            UPDATE subcategorias SET ativa = TRUE WHERE ativa IS NULL;
        """)
        
        conn.commit()
        print("   ✅ Coluna 'ativa' adicionada com sucesso!")
    
    # Verificar quantas subcategorias existem
    cursor.execute("SELECT COUNT(*) as total FROM subcategorias")
    total_subcat = cursor.fetchone()['total']
    print(f"   📊 Total de subcategorias: {total_subcat}")
    
    # ========================================================================
    # 2. VERIFICAR E CRIAR TABELA EVENTO_FORNECEDORES
    # ========================================================================
    print("\n📋 2. Verificando tabela evento_fornecedores...")
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'evento_fornecedores'
        );
    """)
    
    tabela_existe = cursor.fetchone()['exists']
    
    if tabela_existe:
        print("   ✅ Tabela evento_fornecedores já existe")
        
        cursor.execute("SELECT COUNT(*) as total FROM evento_fornecedores")
        total_fornec = cursor.fetchone()['total']
        print(f"   📊 Total de fornecedores cadastrados: {total_fornec}")
    else:
        print("   ⚠️  Tabela evento_fornecedores não existe - CRIANDO...")
        
        cursor.execute("""
            CREATE TABLE evento_fornecedores (
                id SERIAL PRIMARY KEY,
                evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
                fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE CASCADE,
                categoria_id INTEGER REFERENCES categorias(id),
                subcategoria_id INTEGER REFERENCES subcategorias(id),
                valor NUMERIC(15,2) NOT NULL DEFAULT 0.00,
                observacao TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                created_by INTEGER REFERENCES usuarios(id),
                UNIQUE(evento_id, fornecedor_id)
            );
        """)
        
        cursor.execute("""
            CREATE INDEX idx_evento_fornecedores_evento ON evento_fornecedores(evento_id);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_evento_fornecedores_fornecedor ON evento_fornecedores(fornecedor_id);
        """)
        
        cursor.execute("""
            COMMENT ON TABLE evento_fornecedores IS 'Relaciona fornecedores com eventos, incluindo custos e categorização';
        """)
        
        conn.commit()
        print("   ✅ Tabela evento_fornecedores criada com sucesso!")
    
    # ========================================================================
    # 3. VERIFICAÇÃO FINAL
    # ========================================================================
    print("\n" + "=" * 80)
    print("🔍 VERIFICAÇÃO FINAL")
    print("=" * 80)
    
    # Verificar coluna ativa
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'subcategorias' 
            AND column_name = 'ativa'
        );
    """)
    
    if cursor.fetchone()['exists']:
        print("✅ subcategorias.ativa - OK")
    else:
        print("❌ subcategorias.ativa - FALHOU")
    
    # Verificar tabela evento_fornecedores
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'evento_fornecedores'
        );
    """)
    
    if cursor.fetchone()['exists']:
        print("✅ evento_fornecedores - OK")
    else:
        print("❌ evento_fornecedores - FALHOU")
    
    # ========================================================================
    # 4. TESTAR ENDPOINTS
    # ========================================================================
    print("\n" + "=" * 80)
    print("🧪 TESTANDO QUERIES")
    print("=" * 80)
    
    # Testar query de subcategorias
    print("\n1️⃣ Testando query de subcategorias...")
    cursor.execute("""
        SELECT id, nome, categoria_id, ativa
        FROM subcategorias
        WHERE categoria_id = 15 AND ativa = TRUE
        LIMIT 3
    """)
    
    subcat_test = cursor.fetchall()
    if subcat_test:
        print(f"   ✅ Query funciona! Retornou {len(subcat_test)} resultado(s)")
        for sc in subcat_test:
            print(f"      - ID={sc['id']} Nome={sc['nome']}")
    else:
        print("   ⚠️  Query funcionou mas não retornou resultados (categoria_id=15 pode não ter subcategorias)")
    
    # Testar query de evento_fornecedores
    print("\n2️⃣ Testando query de evento_fornecedores...")
    cursor.execute("""
        SELECT 
            ef.id,
            ef.fornecedor_id,
            f.nome as fornecedor_nome,
            ef.valor
        FROM evento_fornecedores ef
        JOIN fornecedores f ON ef.fornecedor_id = f.id
        LIMIT 3
    """)
    
    fornec_test = cursor.fetchall()
    if fornec_test:
        print(f"   ✅ Query funciona! Retornou {len(fornec_test)} resultado(s)")
        for fn in fornec_test:
            print(f"      - ID={fn['id']} Fornecedor={fn['fornecedor_nome']} Valor={fn['valor']}")
    else:
        print("   ⚠️  Query funcionou mas não retornou resultados (tabela vazia)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CORREÇÃO APLICADA COM SUCESSO!")
    print("=" * 80)
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("   1. O código já foi atualizado e enviado para o GitHub")
    print("   2. Aguarde ~2 minutos para o Railway fazer o deploy automático")
    print("   3. Acesse a aplicação e teste os dropdowns de subcategorias")
    print("   4. Vá em Eventos → Aba Fornecedores e teste")
    print("\n💡 Se ainda houver erro 500, verifique os logs do Railway")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

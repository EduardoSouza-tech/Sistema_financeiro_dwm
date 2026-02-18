"""
Criar tabelas subcategorias e evento_fornecedores no Railway
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# URL do Railway
DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

print("=" * 80)
print("🔧 CRIANDO TABELAS NO RAILWAY")
print("=" * 80)

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # ========================================================================
    # 1. CRIAR TABELA SUBCATEGORIAS
    # ========================================================================
    print("\n📋 1. Criando tabela subcategorias...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcategorias (
            id SERIAL PRIMARY KEY,
            categoria_id INTEGER REFERENCES categorias(id) ON DELETE CASCADE,
            nome VARCHAR(100) NOT NULL,
            ativa BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_subcategorias_categoria 
        ON subcategorias(categoria_id);
    """)
    
    conn.commit()
    print("   ✅ Tabela subcategorias criada!")
    
    # ========================================================================
    # 2. MIGRAR DADOS DE categorias.subcategorias PARA A TABELA
    # ========================================================================
    print("\n📋 2. Migrando dados das categorias...")
    
    cursor.execute("""
        SELECT id, nome, subcategorias
        FROM categorias
        WHERE subcategorias IS NOT NULL AND subcategorias != ''
    """)
    
    categorias_com_sub = cursor.fetchall()
    print(f"   📊 Encontradas {len(categorias_com_sub)} categorias com subcategorias")
    
    total_migradas = 0
    for cat in categorias_com_sub:
        try:
            # Tentar parsear como JSON
            try:
                if cat['subcategorias'].startswith('['):
                    subcats_list = json.loads(cat['subcategorias'])
                else:
                    # Se não for JSON, dividir por vírgula
                    subcats_list = [s.strip() for s in cat['subcategorias'].split(',') if s.strip()]
            except:
                subcats_list = [s.strip() for s in cat['subcategorias'].split(',') if s.strip()]
            
            print(f"   → Categoria '{cat['nome']}': {len(subcats_list)} subcategoria(s)")
            
            for subcat_nome in subcats_list:
                if subcat_nome:
                    # Verificar se já existe
                    cursor.execute("""
                        SELECT id FROM subcategorias
                        WHERE categoria_id = %s AND nome = %s
                    """, (cat['id'], subcat_nome))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO subcategorias (categoria_id, nome, ativa)
                            VALUES (%s, %s, TRUE)
                        """, (cat['id'], subcat_nome))
                        total_migradas += 1
        except Exception as e:
            print(f"   ⚠️  Erro ao processar categoria {cat['nome']}: {e}")
    
    conn.commit()
    print(f"\n   ✅ Migradas {total_migradas} subcategorias!")
    
    # ========================================================================
    # 3. CRIAR TABELA EVENTO_FORNECEDORES
    # ========================================================================
    print("\n📋 3. Criando tabela evento_fornecedores...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evento_fornecedores (
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
        CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_evento 
        ON evento_fornecedores(evento_id);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_fornecedor 
        ON evento_fornecedores(fornecedor_id);
    """)
    
    conn.commit()
    print("   ✅ Tabela evento_fornecedores criada!")
    
    # ========================================================================
    # 4. VERIFICAÇÃO FINAL
    # ========================================================================
    print("\n" + "=" * 80)
    print("🔍 VERIFICAÇÃO FINAL")
    print("=" * 80)
    
    cursor.execute("SELECT COUNT(*) as total FROM subcategorias")
    total_sub = cursor.fetchone()['total']
    print(f"✅ Subcategorias: {total_sub} registro(s)")
    
    cursor.execute("SELECT COUNT(*) as total FROM evento_fornecedores")
    total_evt = cursor.fetchone()['total']
    print(f"✅ Evento_fornecedores: {total_evt} registro(s)")
    
    # Testar query
    print("\n🧪 Testando query de subcategorias...")
    cursor.execute("""
        SELECT s.id, s.nome, c.nome as categoria_nome
        FROM subcategorias s
        JOIN categorias c ON s.categoria_id = c.id
        LIMIT 5
    """)
    
    exemplos = cursor.fetchall()
    if exemplos:
        print("   ✅ Query funcionando!")
        for ex in exemplos:
            print(f"      - {ex['nome']} (categoria: {ex['categoria_nome']})")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ TABELAS CRIADAS COM SUCESSO!")
    print("=" * 80)
    print("\n🎯 RESULTADO:")
    print(f"   ✅ {total_sub} subcategorias migradas")
    print(f"   ✅ Tabela evento_fornecedores pronta para uso")
    print("\n💡 Aguarde o deploy do Railway (~2 min) e teste a aplicação!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

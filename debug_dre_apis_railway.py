"""
Script para debugar erros 500 nas APIs de mapeamento DRE
Verifica estrutura da tabela e testa queries
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Conexão Railway
DATABASE_URL = "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def check_table_exists(cursor):
    """Verifica se a tabela existe"""
    print_section("1️⃣ VERIFICANDO SE TABELA EXISTE")
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'dre_mapeamento_subcategoria'
        )
    """)
    
    exists = cursor.fetchone()['exists']
    
    if exists:
        print("✅ Tabela dre_mapeamento_subcategoria EXISTS")
        return True
    else:
        print("❌ Tabela dre_mapeamento_subcategoria NÃO EXISTE")
        return False

def check_related_tables(cursor):
    """Verifica se as tabelas relacionadas existem"""
    print_section("2️⃣ VERIFICANDO TABELAS RELACIONADAS")
    
    tables = ['empresas', 'categorias', 'subcategorias', 'plano_contas']
    
    for table in tables:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table}'
            )
        """)
        
        exists = cursor.fetchone()['exists']
        
        if exists:
            cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
            count = cursor.fetchone()['total']
            print(f"   ✅ {table:20s} - {count:5d} registros")
        else:
            print(f"   ❌ {table:20s} - NÃO EXISTE")

def test_query_subcategorias(cursor, empresa_id=20):
    """Testa query de subcategorias disponíveis"""
    print_section("3️⃣ TESTANDO QUERY: SUBCATEGORIAS DISPONÍVEIS")
    
    try:
        query = """
            SELECT 
                s.id,
                s.nome,
                s.categoria_id,
                c.nome as categoria_nome,
                c.tipo as categoria_tipo
            FROM subcategorias s
            INNER JOIN categorias c ON c.id = s.categoria_id
            WHERE c.empresa_id = %s
              AND s.id NOT IN (
                  SELECT subcategoria_id 
                  FROM dre_mapeamento_subcategoria 
                  WHERE empresa_id = %s
              )
            ORDER BY c.nome, s.nome
        """
        
        print(f"Executando para empresa_id = {empresa_id}...")
        cursor.execute(query, (empresa_id, empresa_id))
        
        results = cursor.fetchall()
        
        print(f"✅ Query executada com sucesso!")
        print(f"📊 {len(results)} subcategorias disponíveis encontradas")
        
        if results:
            print("\n   Primeiros 5 resultados:")
            for i, row in enumerate(results[:5]):
                print(f"      {i+1}. {row['categoria_nome']} → {row['nome']} ({row['categoria_tipo']})")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na query: {str(e)}")
        print(f"   Tipo do erro: {type(e).__name__}")
        return False

def test_query_plano_contas(cursor, empresa_id=20):
    """Testa query de plano de contas DRE"""
    print_section("4️⃣ TESTANDO QUERY: PLANO DE CONTAS DRE")
    
    try:
        query = """
            SELECT 
                id,
                codigo,
                descricao,
                tipo_conta,
                classificacao
            FROM plano_contas
            WHERE empresa_id = %s
              AND tipo_conta = 'analitica'
              AND (
                  codigo LIKE '4%%' OR 
                  codigo LIKE '5%%' OR 
                  codigo LIKE '6%%' OR 
                  codigo LIKE '7%%'
              )
              AND deleted_at IS NULL
            ORDER BY codigo
        """
        
        print(f"Executando para empresa_id = {empresa_id}...")
        cursor.execute(query, (empresa_id,))
        
        results = cursor.fetchall()
        
        print(f"✅ Query executada com sucesso!")
        print(f"📊 {len(results)} contas DRE encontradas")
        
        if results:
            # Agrupar por código inicial
            grupos = {}
            for row in results:
                inicial = row['codigo'][0]
                if inicial not in grupos:
                    grupos[inicial] = []
                grupos[inicial].append(row)
            
            print("\n   Distribuição por grupo:")
            for grupo, contas in sorted(grupos.items()):
                nome_grupo = {
                    '4': 'Receitas',
                    '5': 'Custos',
                    '6': 'Despesas',
                    '7': 'Financeiro'
                }.get(grupo, 'Outros')
                print(f"      Grupo {grupo}.x ({nome_grupo:10s}): {len(contas):3d} contas")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na query: {str(e)}")
        print(f"   Tipo do erro: {type(e).__name__}")
        return False

def test_query_mapeamentos(cursor, empresa_id=20):
    """Testa query de mapeamentos existentes"""
    print_section("5️⃣ TESTANDO QUERY: MAPEAMENTOS EXISTENTES")
    
    try:
        query = """
            SELECT 
                m.id,
                m.subcategoria_id,
                s.nome as subcategoria_nome,
                c.nome as categoria_nome,
                c.tipo as categoria_tipo,
                m.plano_contas_id,
                pc.codigo as plano_contas_codigo,
                pc.descricao as plano_contas_descricao,
                pc.classificacao as plano_contas_classificacao,
                m.ativo,
                m.created_at,
                m.updated_at
            FROM dre_mapeamento_subcategoria m
            INNER JOIN subcategorias s ON s.id = m.subcategoria_id
            INNER JOIN categorias c ON c.id = s.categoria_id
            INNER JOIN plano_contas pc ON pc.id = m.plano_contas_id
            WHERE m.empresa_id = %s
            ORDER BY c.nome, s.nome
        """
        
        print(f"Executando para empresa_id = {empresa_id}...")
        cursor.execute(query, (empresa_id,))
        
        results = cursor.fetchall()
        
        print(f"✅ Query executada com sucesso!")
        print(f"📊 {len(results)} mapeamentos encontrados")
        
        if results:
            print("\n   Mapeamentos existentes:")
            for i, row in enumerate(results[:10]):
                status = "✅ Ativo" if row['ativo'] else "⏸️ Inativo"
                print(f"      {i+1}. {row['categoria_nome']} → {row['subcategoria_nome']}")
                print(f"         Para: {row['plano_contas_codigo']} - {row['plano_contas_descricao']}")
                print(f"         Status: {status}")
        else:
            print("   ℹ️ Nenhum mapeamento configurado ainda")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na query: {str(e)}")
        print(f"   Tipo do erro: {type(e).__name__}")
        return False

def check_table_structure(cursor):
    """Verifica estrutura da tabela"""
    print_section("6️⃣ VERIFICANDO ESTRUTURA DA TABELA")
    
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'dre_mapeamento_subcategoria'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    
    print(f"📋 Colunas ({len(columns)}):")
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
        print(f"   • {col['column_name']:20s} {col['data_type']:25s} {nullable}{default}")

def check_foreign_keys(cursor):
    """Verifica foreign keys"""
    print_section("7️⃣ VERIFICANDO FOREIGN KEYS")
    
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'dre_mapeamento_subcategoria'
    """)
    
    fks = cursor.fetchall()
    
    print(f"🔗 Foreign Keys ({len(fks)}):")
    for fk in fks:
        print(f"   • {fk['column_name']:20s} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")

def main():
    print_section("🔍 DEBUG: APIs DE MAPEAMENTO DRE")
    
    try:
        print("📡 Conectando ao Railway PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("   ✅ Conectado!\n")
        
        # Verificações
        table_exists = check_table_exists(cursor)
        
        if not table_exists:
            print("\n❌ PROBLEMA CRÍTICO: Tabela não existe!")
            print("   Execute novamente: python migration_railway_NOW.py")
            return
        
        check_table_structure(cursor)
        check_foreign_keys(cursor)
        check_related_tables(cursor)
        
        # Testes de queries
        test1 = test_query_subcategorias(cursor)
        test2 = test_query_plano_contas(cursor)
        test3 = test_query_mapeamentos(cursor)
        
        # Resumo
        print_section("📊 RESUMO")
        
        print("Status dos testes:")
        print(f"   {'✅' if table_exists else '❌'} Tabela existe")
        print(f"   {'✅' if test1 else '❌'} Query subcategorias")
        print(f"   {'✅' if test2 else '❌'} Query plano de contas")
        print(f"   {'✅' if test3 else '❌'} Query mapeamentos")
        
        if table_exists and test1 and test2 and test3:
            print("\n✅ Todas as queries funcionam corretamente!")
            print("\n🔍 Próximo passo: Verificar logs do Railway para ver erro específico")
            print("   https://railway.app/dashboard → Logs")
        else:
            print("\n❌ Há problemas nas queries ou estrutura do banco")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Erro de conexão/banco: {str(e)}")
        print(f"   Código: {e.pgcode}")
        print(f"   Detalhes: {e.pgerror}")
        
    except Exception as e:
        print(f"\n❌ Erro geral: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")

if __name__ == "__main__":
    main()

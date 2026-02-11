"""
Script para testar criação de regra de conciliação diretamente no banco
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# URL do Railway
DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:YLUSNALOpzJtzGGQNQbhsNFJYjdHmZXl@autorack.proxy.rlwy.net:45113/railway'

def testar_criar_regra():
    """Testa criar uma regra de conciliação"""
    conn = None
    cursor = None
    
    try:
        print("🔍 Conectando ao banco de dados...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Conexão estabelecida!")
        
        # 1. Verificar estrutura da tabela
        print("\n📊 1. ESTRUTURA DA TABELA regras_conciliacao:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'regras_conciliacao'
            ORDER BY ordinal_position
        """)
        colunas = cursor.fetchall()
        
        for col in colunas:
            print(f"   • {col['column_name']}: {col['data_type']} | Nullable: {col['is_nullable']} | Default: {col['column_default']}")
        
        # 2. Verificar se a coluna usa_integracao_folha existe
        print("\n🔍 2. VERIFICANDO SE COLUNA usa_integracao_folha EXISTE:")
        coluna_existe = any(c['column_name'] == 'usa_integracao_folha' for c in colunas)
        if coluna_existe:
            print("   ⚠️ COLUNA usa_integracao_folha AINDA EXISTE (deveria ter sido removida!)")
        else:
            print("   ✅ Coluna usa_integracao_folha não existe (correto)")
        
        # 3. Verificar empresas disponíveis
        print("\n🏢 3. EMPRESAS DISPONÍVEIS:")
        cursor.execute("SELECT id, razao_social FROM empresas ORDER BY id")
        empresas = cursor.fetchall()
        for emp in empresas:
            print(f"   • ID {emp['id']}: {emp['razao_social']}")
        
        if not empresas:
            print("   ⚠️ NENHUMA EMPRESA ENCONTRADA!")
            return
        
        empresa_id = empresas[0]['id']
        print(f"\n🎯 Usando empresa_id: {empresa_id}")
        
        # 4. Tentar inserir regra de teste
        print("\n💾 4. TENTANDO CRIAR REGRA DE TESTE:")
        
        query = """
            INSERT INTO regras_conciliacao (
                empresa_id, palavra_chave, categoria, subcategoria,
                cliente_padrao, descricao, ativo
            ) VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            RETURNING *
        """
        params = (
            empresa_id,
            'TESTE_SCRIPT',
            'RECEITA',
            'VENDAS',
            'Cliente Teste',
            'Regra criada via script de teste'
        )
        
        print(f"   Query: {query}")
        print(f"   Params: {params}")
        
        cursor.execute(query, params)
        regra = cursor.fetchone()
        
        print("\n✅ REGRA CRIADA COM SUCESSO!")
        print(f"   ID: {regra['id']}")
        print(f"   Palavra-chave: {regra['palavra_chave']}")
        print(f"   Categoria: {regra['categoria']}")
        print(f"   Subcategoria: {regra['subcategoria']}")
        
        # 5. Limpar teste (rollback)
        print("\n🔄 Fazendo ROLLBACK para não deixar lixo no banco...")
        conn.rollback()
        print("✅ Rollback executado. Regra de teste removida.")
        
        print("\n" + "="*60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("   A tabela está correta e aceita inserções normalmente.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("\n🔌 Conexão fechada.")

if __name__ == '__main__':
    testar_criar_regra()

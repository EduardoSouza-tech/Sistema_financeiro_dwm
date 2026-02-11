"""
Script para listar todas as regras de conciliação existentes
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# URL do Railway
DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:YLUSNALOpzJtzGGQNQbhsNFJYjdHmZXl@autorack.proxy.rlwy.net:45113/railway'

def listar_regras():
    """Lista todas as regras de conciliação"""
    conn = None
    cursor = None
    
    try:
        print("🔍 Conectando ao banco de dados...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Conexão estabelecida!")
        
        # Buscar todas as regras
        print("\n" + "="*80)
        print(" 📋 REGRAS DE CONCILIAÇÃO CADASTRADAS")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                r.id,
                r.empresa_id,
                e.razao_social as empresa,
                r.palavra_chave,
                r.categoria,
                r.subcategoria,
                r.cliente_padrao,
                r.descricao,
                r.ativo,
                r.created_at
            FROM regras_conciliacao r
            LEFT JOIN empresas e ON e.id = r.empresa_id
            ORDER BY r.empresa_id, r.palavra_chave
        """)
        
        regras = cursor.fetchall()
        
        if not regras:
            print("\n⚠️  Nenhuma regra cadastrada ainda.")
            return
        
        print(f"\n📊 Total: {len(regras)} regra(s)\n")
        
        empresa_atual = None
        
        for i, regra in enumerate(regras, 1):
            # Separador por empresa
            if regra['empresa_id'] != empresa_atual:
                empresa_atual = regra['empresa_id']
                print(f"\n{'='*80}")
                print(f"🏢 EMPRESA: {regra['empresa']} (ID: {regra['empresa_id']})")
                print(f"{'='*80}")
            
            status = "✅ ATIVA" if regra['ativo'] else "❌ INATIVA"
            
            print(f"\n[{i}] {status} | ID: {regra['id']}")
            print(f"    🔤 Palavra-chave: {regra['palavra_chave']}")
            
            if regra['categoria']:
                print(f"    📁 Categoria: {regra['categoria']}", end='')
                if regra['subcategoria']:
                    print(f" → {regra['subcategoria']}")
                else:
                    print()
            
            if regra['cliente_padrao']:
                print(f"    👤 Cliente/Fornecedor: {regra['cliente_padrao']}")
            
            if regra['descricao']:
                print(f"    📝 Descrição: {regra['descricao']}")
            
            print(f"    🕐 Criada em: {regra['created_at'].strftime('%d/%m/%Y %H:%M')}")
        
        print("\n" + "="*80)
        
        # Verificar duplicatas
        print("\n🔍 VERIFICANDO DUPLICATAS...")
        cursor.execute("""
            SELECT empresa_id, palavra_chave, COUNT(*) as total
            FROM regras_conciliacao
            GROUP BY empresa_id, palavra_chave
            HAVING COUNT(*) > 1
        """)
        
        duplicatas = cursor.fetchall()
        
        if duplicatas:
            print(f"\n⚠️  ATENÇÃO: {len(duplicatas)} palavra(s)-chave duplicada(s) encontrada(s)!\n")
            for dup in duplicatas:
                print(f"   • Empresa {dup['empresa_id']}: '{dup['palavra_chave']}' ({dup['total']}x)")
            print("\n💡 Execute o script de limpeza para remover duplicatas")
        else:
            print("\n✅ Nenhuma duplicata encontrada!")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("\n🔌 Conexão fechada.")

if __name__ == '__main__':
    listar_regras()

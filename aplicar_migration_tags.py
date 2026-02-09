"""
Aplicar Migration: Cadastro de Tags
Data: 2026-02-08
Descrição: Executa migration_tags.sql no banco de dados
"""

import os
from database_postgresql import get_db_connection, return_to_pool

def executar_migration():
    """Executa a migration de tags"""
    
    print("\n" + "="*80)
    print("🏷️  MIGRATION: Cadastro de Tags")
    print("="*80)
    print()
    
    # Ler arquivo SQL
    sql_file = 'migration_tags.sql'
    
    if not os.path.exists(sql_file):
        print(f"❌ Erro: Arquivo {sql_file} não encontrado!")
        return False
    
    print(f"📄 Lendo arquivo: {sql_file}")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"✅ Arquivo lido: {len(sql_content)} caracteres")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo SQL: {e}")
        return False
    
    # Conectar ao banco
    print("🔌 Conectando ao banco de dados...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Conexão estabelecida")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # Verificar se tabela já existe
    print("🔍 Verificando se tabela tags já existe...")
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'tags'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela tags já existe!")
            
            # Verificar quantos registros
            cursor.execute("SELECT COUNT(*) FROM tags")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros existentes: {count}")
            
            resposta = input("\n❓ Deseja recriar a tabela? (s/N): ").strip().lower()
            
            if resposta != 's':
                print("❌ Migration cancelada pelo usuário")
                cursor.close()
                return_to_pool(conn)
                return False
            
            print("⚠️  ATENÇÃO: Dropando tabelas existentes...")
            cursor.execute("DROP TABLE IF EXISTS sessao_tags CASCADE")
            cursor.execute("DROP TABLE IF EXISTS tags CASCADE")
            conn.commit()
            print("✅ Tabelas removidas")
        
        else:
            print("✅ Tabela não existe - prosseguindo com criação")
        
        print()
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabela: {e}")
        cursor.close()
        return_to_pool(conn)
        return False
    
    # Executar migration
    print("⚙️  Executando migration...")
    print()
    
    try:
        # Executar todo o script (contém blocos DO $$)
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ Migration executada com sucesso!")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        cursor.close()
        return_to_pool(conn)
        return False
    
    # Validar resultado
    print("🔍 Validando resultado...")
    
    try:
        # Contar tags por empresa
        cursor.execute("""
            SELECT 
                e.nome as empresa,
                COUNT(t.id) as total_tags,
                COUNT(CASE WHEN t.ativa THEN 1 END) as tags_ativas
            FROM empresas e
            LEFT JOIN tags t ON e.id = t.empresa_id
            WHERE t.id IS NOT NULL
            GROUP BY e.id, e.nome
            ORDER BY e.nome
        """)
        
        resultados = cursor.fetchall()
        
        if resultados:
            print(f"\n📊 Tags criadas por empresa:")
            print(f"{'Empresa':<30} {'Total':<10} {'Ativas':<10}")
            print("-" * 50)
            
            total_geral = 0
            for empresa, total, ativas in resultados:
                print(f"{empresa:<30} {total:<10} {ativas:<10}")
                total_geral += total
            
            print("-" * 50)
            print(f"{'TOTAL':<30} {total_geral:<10}")
            print()
        
        # Listar algumas tags exemplo
        cursor.execute("""
            SELECT t.nome, t.cor, t.icone, t.ativa
            FROM tags t
            INNER JOIN empresas e ON t.empresa_id = e.id
            ORDER BY t.nome
            LIMIT 20
        """)
        
        tags = cursor.fetchall()
        
        if tags:
            print(f"\n🏷️  Exemplo de tags cadastradas:")
            for nome, cor, icone, ativa in tags:
                status = "✅" if ativa else "❌"
                print(f"   {status} {icone} {nome} ({cor})")
            print()
        
        # Verificar tabela de relacionamento
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'sessao_tags'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("\n✅ Tabela sessao_tags criada com sucesso")
            
            # Verificar relacionamentos migrados
            cursor.execute("SELECT COUNT(*) FROM sessao_tags")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   📊 {count} relacionamentos sessão-tag migrados")
        
        cursor.close()
        return_to_pool(conn)
        
        print("\n" + "="*80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar: {e}")
        cursor.close()
        return_to_pool(conn)
        return False


if __name__ == '__main__':
    import sys
    
    resultado = executar_migration()
    
    if resultado:
        print("\n✅ Tudo pronto! O sistema de tags foi criado.")
        print("   - 15 tags padrão foram inseridas para cada empresa")
        print("   - Trigger criado para novas empresas")
        print("   - Tabela de relacionamento sessão-tags criada")
        print("   - Frontend pronto para usar seleção múltipla")
        sys.exit(0)
    else:
        print("\n❌ Falha na migration!")
        sys.exit(1)

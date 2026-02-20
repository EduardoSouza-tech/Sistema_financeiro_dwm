"""
Aplicar Migration: DRE - Mapeamento de Subcategorias
Data: 19/02/2026
"""

import os
import sys
from database_postgresql import DatabaseManager

def aplicar_migration_dre_mapeamento():
    """Aplica migration de criação da tabela dre_mapeamento_subcategoria"""
    
    print("=" * 80)
    print("🚀 MIGRATION: DRE - Mapeamento de Subcategorias para Plano de Contas")
    print("=" * 80)
    print()
    
    try:
        # Conectar ao banco
        print("📡 Conectando ao banco de dados Railway...")
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("   ✅ Conectado com sucesso!")
        print()
        
        # Ler o arquivo SQL
        print("📄 Lendo arquivo de migration...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, 'migration_dre_mapeamento.sql')
        
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"Arquivo SQL não encontrado: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print(f"   ✅ Arquivo lido: {os.path.basename(sql_file)}")
        print()
        
        # Executar o script SQL
        print("⚙️  Executando migration...")
        print()
        
        # Dividir por statement (ignora comentários SQL)
        statements = []
        current_statement = []
        
        for line in sql_script.split('\n'):
            stripped = line.strip()
            
            # Ignorar linhas vazias e comentários
            if not stripped or stripped.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # Se termina com ;, é fim de statement
            if stripped.endswith(';'):
                statement = '\n'.join(current_statement)
                statements.append(statement)
                current_statement = []
        
        # Executar cada statement
        for i, statement in enumerate(statements, 1):
            try:
                # Pular RAISE NOTICE pois cursor simples não suporta
                if 'RAISE NOTICE' in statement or 'DO $$' in statement:
                    continue
                
                cursor.execute(statement)
                conn.commit()
                
            except Exception as e:
                if "already exists" in str(e):
                    print(f"   ⚠️  Statement {i}: Já existe (pulando)")
                else:
                    print(f"   ❌ Erro no statement {i}: {e}")
                    conn.rollback()
        
        print("   ✅ Migration executada!")
        print()
        
        # Verificar resultado
        print("🔍 Verificando tabela criada...")
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'dre_mapeamento_subcategoria'
            );
        """)
        
        tabela_existe = cursor.fetchone()[0]
        
        if tabela_existe:
            print("   ✅ Tabela dre_mapeamento_subcategoria criada!")
            
            # Verificar colunas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'dre_mapeamento_subcategoria'
                ORDER BY ordinal_position;
            """)
            
            colunas = cursor.fetchall()
            print(f"\n   📋 Colunas ({len(colunas)}):")
            for col_name, col_type, nullable in colunas:
                print(f"      - {col_name:<25} {col_type:<20} (nullable: {nullable})")
            
            # Verificar índices
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'dre_mapeamento_subcategoria';
            """)
            
            indices = cursor.fetchall()
            print(f"\n   📊 Índices ({len(indices)}):")
            for (idx_name,) in indices:
                print(f"      - {idx_name}")
            
            # Verificar constraints
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'dre_mapeamento_subcategoria';
            """)
            
            constraints = cursor.fetchall()
            print(f"\n   🔒 Constraints ({len(constraints)}):")
            for const_name, const_type in constraints:
                tipo_map = {
                    'PRIMARY KEY': 'Primary Key',
                    'FOREIGN KEY': 'Foreign Key',
                    'UNIQUE': 'Unique',
                    'CHECK': 'Check'
                }
                tipo_legivel = tipo_map.get(const_type, const_type)
                print(f"      - {const_name:<40} ({tipo_legivel})")
        
        else:
            print("   ❌ Tabela NÃO foi criada!")
            sys.exit(1)
        
        print()
        print("=" * 80)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print()
        print("📌 Próximos passos:")
        print("   1. Criar APIs de mapeamento (CRUD)")
        print("   2. Criar interface de configuração no frontend")
        print("   3. Modificar função gerar_dre para usar mapeamentos")
        print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERRO NA MIGRATION")
        print("=" * 80)
        print(f"Erro: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    aplicar_migration_dre_mapeamento()

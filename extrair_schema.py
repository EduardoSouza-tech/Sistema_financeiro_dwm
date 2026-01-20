"""
Script para extrair o schema completo do banco PostgreSQL
Gera documentação detalhada de todas as tabelas, colunas, constraints e relacionamentos
"""
import os
import sys
import json
from datetime import datetime

# Configurar caminho para importar database_postgresql
sys.path.insert(0, os.path.dirname(__file__))

try:
    import database_postgresql as db
    print("✅ Módulo database_postgresql importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar database_postgresql: {e}")
    sys.exit(1)

def extrair_schema_completo():
    """Extrai schema completo do banco de dados"""
    
    print("\n" + "="*80)
    print("🔍 EXTRAÇÃO DO SCHEMA DO BANCO DE DADOS")
    print("="*80 + "\n")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        schema_info = {
            'data_extracao': datetime.now().isoformat(),
            'database': os.getenv('DATABASE_URL', 'railway_postgresql'),
            'tabelas': []
        }
        
        # 1. Obter lista de todas as tabelas
        print("📋 Listando tabelas...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tabelas = cursor.fetchall()
        print(f"   Encontradas {len(tabelas)} tabelas\n")
        
        for idx, tabela_row in enumerate(tabelas, 1):
            tabela_nome = tabela_row[0] if isinstance(tabela_row, tuple) else tabela_row['table_name']
            
            print(f"📊 [{idx}/{len(tabelas)}] Analisando tabela: {tabela_nome}")
            
            tabela_info = {
                'nome': tabela_nome,
                'colunas': [],
                'constraints': [],
                'indexes': [],
                'foreign_keys': []
            }
            
            # 2. Obter colunas da tabela
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (tabela_nome,))
            
            colunas = cursor.fetchall()
            print(f"   ├─ Colunas: {len(colunas)}")
            
            for coluna in colunas:
                if isinstance(coluna, dict):
                    col_info = {
                        'nome': coluna['column_name'],
                        'tipo': coluna['data_type'],
                        'tamanho': coluna.get('character_maximum_length'),
                        'nullable': coluna['is_nullable'] == 'YES',
                        'default': coluna.get('column_default')
                    }
                else:
                    col_info = {
                        'nome': coluna[0],
                        'tipo': coluna[1],
                        'tamanho': coluna[2],
                        'nullable': coluna[3] == 'YES',
                        'default': coluna[4]
                    }
                
                tabela_info['colunas'].append(col_info)
            
            # 3. Obter constraints (PK, UNIQUE, CHECK)
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s
                AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE', 'CHECK')
            """, (tabela_nome,))
            
            constraints = cursor.fetchall()
            print(f"   ├─ Constraints: {len(constraints)}")
            
            for constraint in constraints:
                if isinstance(constraint, dict):
                    const_info = {
                        'nome': constraint['constraint_name'],
                        'tipo': constraint['constraint_type'],
                        'coluna': constraint['column_name']
                    }
                else:
                    const_info = {
                        'nome': constraint[0],
                        'tipo': constraint[1],
                        'coluna': constraint[2]
                    }
                
                tabela_info['constraints'].append(const_info)
            
            # 4. Obter Foreign Keys
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (tabela_nome,))
            
            fks = cursor.fetchall()
            print(f"   ├─ Foreign Keys: {len(fks)}")
            
            for fk in fks:
                if isinstance(fk, dict):
                    fk_info = {
                        'coluna': fk['column_name'],
                        'referencia_tabela': fk['foreign_table_name'],
                        'referencia_coluna': fk['foreign_column_name']
                    }
                else:
                    fk_info = {
                        'coluna': fk[0],
                        'referencia_tabela': fk[1],
                        'referencia_coluna': fk[2]
                    }
                
                tabela_info['foreign_keys'].append(fk_info)
            
            # 5. Obter Indexes
            cursor.execute("""
                SELECT
                    i.relname AS index_name,
                    a.attname AS column_name,
                    ix.indisunique AS is_unique
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = %s
                AND t.relkind = 'r'
            """, (tabela_nome,))
            
            indexes = cursor.fetchall()
            print(f"   └─ Indexes: {len(indexes)}")
            
            for index in indexes:
                if isinstance(index, dict):
                    idx_info = {
                        'nome': index['index_name'],
                        'coluna': index['column_name'],
                        'unique': index['is_unique']
                    }
                else:
                    idx_info = {
                        'nome': index[0],
                        'coluna': index[1],
                        'unique': index[2]
                    }
                
                tabela_info['indexes'].append(idx_info)
            
            schema_info['tabelas'].append(tabela_info)
            print()
        
        cursor.close()
        conn.close()
        
        # Salvar em JSON
        output_file = 'schema_database.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema_info, f, indent=2, ensure_ascii=False)
        
        print("="*80)
        print(f"✅ Schema extraído com sucesso!")
        print(f"📄 Arquivo salvo: {output_file}")
        print(f"📊 Total de tabelas: {len(schema_info['tabelas'])}")
        print("="*80 + "\n")
        
        return schema_info
        
    except Exception as e:
        print(f"\n❌ Erro ao extrair schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def gerar_markdown(schema_info):
    """Gera documentação em Markdown do schema"""
    
    print("📝 Gerando documentação Markdown...")
    
    markdown = f"""# 📊 Schema do Banco de Dados - Sistema Financeiro

**Data de Extração**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  
**Database**: PostgreSQL (Railway)  
**Total de Tabelas**: {len(schema_info['tabelas'])}

---

## 📋 Índice

"""
    
    # Índice
    for idx, tabela in enumerate(schema_info['tabelas'], 1):
        markdown += f"{idx}. [{tabela['nome']}](#{tabela['nome'].replace('_', '-')})\n"
    
    markdown += "\n---\n\n"
    
    # Detalhes de cada tabela
    for tabela in schema_info['tabelas']:
        markdown += f"## 📦 Tabela: `{tabela['nome']}`\n\n"
        
        # Estatísticas
        total_colunas = len(tabela['colunas'])
        total_fks = len(tabela['foreign_keys'])
        total_indexes = len(tabela['indexes'])
        
        markdown += f"**Estatísticas**:\n"
        markdown += f"- 📊 Colunas: {total_colunas}\n"
        markdown += f"- 🔑 Foreign Keys: {total_fks}\n"
        markdown += f"- 📇 Indexes: {total_indexes}\n\n"
        
        # Colunas
        markdown += "### Colunas\n\n"
        markdown += "| Coluna | Tipo | Tamanho | Nullable | Default |\n"
        markdown += "|--------|------|---------|----------|----------|\n"
        
        for col in tabela['colunas']:
            nullable = "✅ Sim" if col['nullable'] else "❌ Não"
            tamanho = str(col['tamanho']) if col['tamanho'] else "-"
            default = col['default'] if col['default'] else "-"
            
            # Truncar default se for muito longo
            if len(str(default)) > 50:
                default = str(default)[:47] + "..."
            
            markdown += f"| `{col['nome']}` | `{col['tipo']}` | {tamanho} | {nullable} | `{default}` |\n"
        
        markdown += "\n"
        
        # Constraints
        if tabela['constraints']:
            markdown += "### Constraints\n\n"
            markdown += "| Nome | Tipo | Coluna |\n"
            markdown += "|------|------|--------|\n"
            
            for const in tabela['constraints']:
                markdown += f"| `{const['nome']}` | {const['tipo']} | `{const['coluna']}` |\n"
            
            markdown += "\n"
        
        # Foreign Keys
        if tabela['foreign_keys']:
            markdown += "### Foreign Keys (Relacionamentos)\n\n"
            markdown += "| Coluna | Referencia → Tabela | Referencia → Coluna |\n"
            markdown += "|--------|---------------------|---------------------|\n"
            
            for fk in tabela['foreign_keys']:
                markdown += f"| `{fk['coluna']}` | `{fk['referencia_tabela']}` | `{fk['referencia_coluna']}` |\n"
            
            markdown += "\n"
        
        # Indexes
        if tabela['indexes']:
            markdown += "### Indexes\n\n"
            markdown += "| Nome | Coluna | Unique |\n"
            markdown += "|------|--------|--------|\n"
            
            for idx in tabela['indexes']:
                unique = "✅ Sim" if idx['unique'] else "❌ Não"
                markdown += f"| `{idx['nome']}` | `{idx['coluna']}` | {unique} |\n"
            
            markdown += "\n"
        
        markdown += "---\n\n"
    
    # Diagrama de relacionamentos
    markdown += "## 🔗 Diagrama de Relacionamentos\n\n"
    markdown += "```mermaid\nerDiagram\n"
    
    for tabela in schema_info['tabelas']:
        if tabela['foreign_keys']:
            for fk in tabela['foreign_keys']:
                markdown += f"    {tabela['nome']} ||--o{{ {fk['referencia_tabela']} : \"{fk['coluna']}\"\n"
    
    markdown += "```\n\n"
    
    # Salvar arquivo
    output_file = 'SCHEMA_DATABASE.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Documentação Markdown gerada: {output_file}\n")
    
    return output_file

if __name__ == "__main__":
    schema_info = extrair_schema_completo()
    gerar_markdown(schema_info)
    print("🎉 Processo completo! Schema documentado com sucesso.")

"""
Migração: Adiciona proprietario_id em tabelas faltantes para completar multi-tenancy
"""
import os
import psycopg2
from urllib.parse import urlparse

def executar_migracao():
    """Adiciona proprietario_id em todas as tabelas que precisam"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL não configurada")
        return False
    
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Tabelas que precisam de proprietario_id
    tabelas = [
        'contratos',
        'sessoes',
        'comissoes',
        'contrato_comissoes',
        'estoque_produtos',
        'estoque_movimentacoes',
        'produtos',
        'kits',
        'kits_equipamentos',
        'templates_equipe',
        'tags',
        'tags_trabalho',
        'tipos_sessao',
        'agenda',
        'agenda_fotografia'
    ]
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("\n🔄 Iniciando migração de proprietario_id...")
        print(f"📋 Total de tabelas: {len(tabelas)}\n")
        
        for tabela in tabelas:
            try:
                # Verificar se a coluna já existe
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{tabela}' 
                    AND column_name = 'proprietario_id'
                """)
                
                existe = cursor.fetchone()
                
                if existe:
                    print(f"   ✓ {tabela.ljust(25)} - proprietario_id já existe")
                else:
                    # Adicionar coluna
                    cursor.execute(f"""
                        ALTER TABLE {tabela} 
                        ADD COLUMN IF NOT EXISTS proprietario_id INTEGER 
                        REFERENCES usuarios(id) ON DELETE CASCADE
                    """)
                    
                    # Criar índice
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{tabela}_proprietario 
                        ON {tabela}(proprietario_id)
                    """)
                    
                    conn.commit()
                    print(f"   ✅ {tabela.ljust(25)} - proprietario_id ADICIONADO")
                    
            except Exception as e:
                print(f"   ⚠️  {tabela.ljust(25)} - Erro: {str(e)[:50]}")
                conn.rollback()
                continue
        
        print("\n✅ Migração concluída!")
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_status():
    """Verifica quais tabelas têm proprietario_id"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL não configurada")
        return
    
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Buscar todas as tabelas do usuário
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        todas_tabelas = [row[0] for row in cursor.fetchall()]
        
        print("\n" + "="*70)
        print("📊 STATUS DO MULTI-TENANCY")
        print("="*70)
        
        com_proprietario = []
        sem_proprietario = []
        
        for tabela in todas_tabelas:
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{tabela}' 
                AND column_name = 'proprietario_id'
            """)
            
            tem_proprietario = cursor.fetchone() is not None
            
            if tem_proprietario:
                com_proprietario.append(tabela)
            else:
                sem_proprietario.append(tabela)
        
        print(f"\n✅ COM proprietario_id ({len(com_proprietario)} tabelas):")
        for tabela in com_proprietario:
            print(f"   • {tabela}")
        
        print(f"\n⚠️  SEM proprietario_id ({len(sem_proprietario)} tabelas):")
        for tabela in sem_proprietario:
            print(f"   • {tabela}")
        
        print("\n" + "="*70 + "\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--verificar':
        verificar_status()
    else:
        executar_migracao()
        verificar_status()

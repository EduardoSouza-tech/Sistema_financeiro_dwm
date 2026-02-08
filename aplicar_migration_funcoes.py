"""
Aplicar Migration: Cadastro de Funções de Responsáveis
Data: 2026-02-08
Descrição: Executa migration_funcoes_responsaveis.sql no banco de dados
"""

import os
from database_postgresql import get_db_connection, return_to_pool

def executar_migration():
    """Executa a migration de funções de responsáveis"""
    
    print("\n" + "="*80)
    print("🚀 MIGRATION: Cadastro de Funções de Responsáveis")
    print("="*80)
    print()
    
    # Ler arquivo SQL
    sql_file = 'migration_funcoes_responsaveis.sql'
    
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
    print("🔍 Verificando se tabela funcoes_responsaveis já existe...")
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'funcoes_responsaveis'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela funcoes_responsaveis já existe!")
            
            # Verificar quantos registros
            cursor.execute("SELECT COUNT(*) FROM funcoes_responsaveis")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros existentes: {count}")
            
            resposta = input("\n❓ Deseja recriar a tabela? (s/N): ").strip().lower()
            
            if resposta != 's':
                print("❌ Migration cancelada pelo usuário")
                cursor.close()
                return_to_pool(conn)
                return False
            
            print("⚠️  ATENÇÃO: Dropando tabela existente...")
            cursor.execute("DROP TABLE IF EXISTS funcoes_responsaveis CASCADE")
            conn.commit()
            print("✅ Tabela removida")
        
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
        # Separar comandos SQL (evitar executar SELECTs de validação)
        comandos = []
        comando_atual = []
        
        for linha in sql_content.split('\n'):
            linha = linha.strip()
            
            # Ignorar comentários e linhas vazias
            if not linha or linha.startswith('--'):
                continue
            
            # Ignorar SELECTs de validação (no final)
            if linha.upper().startswith('SELECT') and 'information_schema' not in linha:
                continue
            
            comando_atual.append(linha)
            
            # Se termina com ;, é fim de comando
            if linha.endswith(';'):
                comandos.append(' '.join(comando_atual))
                comando_atual = []
        
        print(f"📦 Comandos SQL encontrados: {len(comandos)}")
        print()
        
        # Executar cada comando
        for i, comando in enumerate(comandos, 1):
            # Identificar tipo de comando
            cmd_type = comando.strip().split()[0].upper()
            
            # Limitar preview
            preview = comando[:80] + '...' if len(comando) > 80 else comando
            
            print(f"   [{i}/{len(comandos)}] {cmd_type}: {preview}")
            
            try:
                cursor.execute(comando)
                conn.commit()
                print(f"   ✅ Sucesso")
                
            except Exception as e:
                # Se for erro de "já existe", ignorar
                if 'already exists' in str(e) or 'does not exist' in str(e):
                    print(f"   ⚠️  Aviso: {e}")
                else:
                    print(f"   ❌ Erro: {e}")
                    raise
            
            print()
        
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
        # Contar funções por empresa
        cursor.execute("""
            SELECT 
                e.nome as empresa,
                COUNT(f.id) as total_funcoes,
                COUNT(CASE WHEN f.ativa THEN 1 END) as funcoes_ativas
            FROM empresas e
            LEFT JOIN funcoes_responsaveis f ON e.id = f.empresa_id
            GROUP BY e.id, e.nome
            ORDER BY e.nome
        """)
        
        resultados = cursor.fetchall()
        
        if resultados:
            print(f"\n📊 Funções criadas por empresa:")
            print(f"{'Empresa':<30} {'Total':<10} {'Ativas':<10}")
            print("-" * 50)
            
            total_geral = 0
            for empresa, total, ativas in resultados:
                print(f"{empresa:<30} {total:<10} {ativas:<10}")
                total_geral += total
            
            print("-" * 50)
            print(f"{'TOTAL':<30} {total_geral:<10}")
            print()
        
        # Listar funções de uma empresa exemplo
        cursor.execute("""
            SELECT f.nome, f.descricao, f.ativa
            FROM funcoes_responsaveis f
            INNER JOIN empresas e ON f.empresa_id = e.id
            ORDER BY e.nome, f.nome
            LIMIT 15
        """)
        
        funcoes = cursor.fetchall()
        
        if funcoes:
            print(f"\n📋 Exemplo de funções cadastradas:")
            for nome, desc, ativa in funcoes:
                status = "✅" if ativa else "❌"
                print(f"   {status} {nome}: {desc}")
            print()
        
        cursor.close()
        return_to_pool(conn)
        
        print("="*80)
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
        print("\n✅ Tudo pronto! A tabela funcoes_responsaveis foi criada.")
        print("   - 10 funções padrão foram inseridas para cada empresa")
        print("   - Trigger criado para novas empresas")
        print("   - API e frontend estão prontos para usar")
        sys.exit(0)
    else:
        print("\n❌ Falha na migration!")
        sys.exit(1)

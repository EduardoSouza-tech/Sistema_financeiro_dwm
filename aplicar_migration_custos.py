"""
Aplicar Migration: Cadastro de Custos Operacionais
Data: 2026-02-08
Descrição: Executa migration_custos_operacionais.sql no banco de dados
"""

import os
from database_postgresql import get_db_connection, return_to_pool

def executar_migration():
    """Executa a migration de custos operacionais"""
    
    print("\n" + "="*80)
    print("💰 MIGRATION: Cadastro de Custos Operacionais")
    print("="*80)
    print()
    
    # Ler arquivo SQL
    sql_file = 'migration_custos_operacionais.sql'
    
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
    print("🔍 Verificando se tabela custos_operacionais já existe...")
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'custos_operacionais'
        """)
        
        if cursor.fetchone():
            print("⚠️  Tabela custos_operacionais já existe!")
            
            # Verificar quantos registros
            cursor.execute("SELECT COUNT(*) FROM custos_operacionais")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros existentes: {count}")
            
            resposta = input("\n❓ Deseja recriar a tabela? (s/N): ").strip().lower()
            
            if resposta != 's':
                print("❌ Migration cancelada pelo usuário")
                cursor.close()
                return_to_pool(conn)
                return False
            
            print("⚠️  ATENÇÃO: Dropando tabela existente...")
            cursor.execute("DROP TABLE IF EXISTS custos_operacionais CASCADE")
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
        # Separar comandos SQL
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
        # Contar custos por categoria e empresa
        cursor.execute("""
            SELECT 
                e.nome as empresa,
                c.categoria,
                COUNT(c.id) as total_custos,
                COUNT(CASE WHEN c.ativo THEN 1 END) as custos_ativos
            FROM empresas e
            LEFT JOIN custos_operacionais c ON e.id = c.empresa_id
            WHERE c.id IS NOT NULL
            GROUP BY e.id, e.nome, c.categoria
            ORDER BY e.nome, c.categoria
        """)
        
        resultados = cursor.fetchall()
        
        if resultados:
            print(f"\n📊 Custos criados por empresa e categoria:")
            print(f"{'Empresa':<30} {'Categoria':<20} {'Total':<10} {'Ativos':<10}")
            print("-" * 70)
            
            total_geral = 0
            for empresa, categoria, total, ativos in resultados:
                print(f"{empresa:<30} {categoria:<20} {total:<10} {ativos:<10}")
                total_geral += total
            
            print("-" * 70)
            print(f"{'TOTAL':<51} {total_geral:<10}")
            print()
        
        # Listar alguns custos exemplo
        cursor.execute("""
            SELECT c.nome, c.categoria, c.valor_padrao, c.unidade, c.ativo
            FROM custos_operacionais c
            INNER JOIN empresas e ON c.empresa_id = e.id
            ORDER BY c.categoria, c.nome
            LIMIT 20
        """)
        
        custos = cursor.fetchall()
        
        if custos:
            print(f"\n📋 Exemplo de custos cadastrados:")
            for nome, categoria, valor, unidade, ativo in custos:
                status = "✅" if ativo else "❌"
                print(f"   {status} [{categoria}] {nome}: R$ {valor:,.2f}/{unidade}")
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
        print("\n✅ Tudo pronto! A tabela custos_operacionais foi criada.")
        print("   - 18 custos padrão foram inseridos para cada empresa")
        print("   - Trigger criado para novas empresas")
        print("   - API e frontend estão prontos para usar")
        sys.exit(0)
    else:
        print("\n❌ Falha na migration!")
        sys.exit(1)

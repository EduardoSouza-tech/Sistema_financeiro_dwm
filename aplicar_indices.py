"""
Script para aplicar os índices de performance no PostgreSQL do Railway
Fase 7 - Performance Optimization
"""
import os
import sys
import database_postgresql

def aplicar_indices():
    """Aplica todos os índices de performance do arquivo SQL"""
    print("⚡ Aplicando índices de performance no PostgreSQL...")
    print("=" * 60)
    
    try:
        # Conectar ao banco usando context manager
        with database_postgresql.get_db_connection() as conn:
            cursor = conn.cursor()
            print("✅ Conexão estabelecida com sucesso!")
            print()
        
        # Ler o arquivo SQL
        script_path = os.path.join(os.path.dirname(__file__), 'create_performance_indexes.sql')
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Separar comandos SQL (ignora comentários e linhas vazias)
        comandos = []
        comando_atual = []
        
        for linha in sql_content.split('\n'):
            linha = linha.strip()
            # Ignora comentários e linhas vazias
            if not linha or linha.startswith('--'):
                continue
            
            comando_atual.append(linha)
            
            # Se termina com ponto e vírgula, é fim de comando
            if linha.endswith(';'):
                comandos.append(' '.join(comando_atual))
                comando_atual = []
        
        # Executar cada comando
        indices_criados = 0
        indices_existentes = 0
        erros = 0
        
        for i, comando in enumerate(comandos, 1):
            if not comando.strip():
                continue
                
            # Extrair nome do índice
            nome_indice = "desconhecido"
            if "CREATE INDEX" in comando:
                partes = comando.split("CREATE INDEX IF NOT EXISTS")
                if len(partes) > 1:
                    nome_indice = partes[1].split()[0].strip()
            
            try:
                print(f"[{i}/{len(comandos)}] Criando índice: {nome_indice}...", end=" ")
                cursor.execute(comando)
                conn.commit()
                print("✅")
                indices_criados += 1
                
            except Exception as e:
                erro_msg = str(e).lower()
                if "already exists" in erro_msg or "já existe" in erro_msg:
                    print("⚠️ (já existe)")
                    indices_existentes += 1
                else:
                    print(f"❌ ERRO: {e}")
                    erros += 1
        
        # Estatísticas finais
        print()
        print("=" * 60)
        print("📊 RESUMO DA APLICAÇÃO:")
        print(f"   ✅ Índices criados: {indices_criados}")
        print(f"   ⚠️  Índices já existentes: {indices_existentes}")
        print(f"   ❌ Erros: {erros}")
        print(f"   📈 Total processado: {len(comandos)} comandos")
        print()
        
        # Executar ANALYZE para atualizar estatísticas
        print("📊 Atualizando estatísticas do banco (ANALYZE)...")
        try:
            cursor.execute("ANALYZE;")
            conn.commit()
            print("✅ Estatísticas atualizadas!")
        except Exception as e:
            print(f"⚠️ Aviso ao atualizar estatísticas: {e}")
        
        # Listar índices criados
        print()
        print("📋 Verificando índices criados:")
        cursor.execute("""
            SELECT schemaname, tablename, indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' 
              AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname;
        """)
        
        indices = cursor.fetchall()
        tabela_atual = None
        
        for schema, tabela, nome, definicao in indices:
            if tabela != tabela_atual:
                print(f"\n📦 Tabela: {tabela}")
                tabela_atual = tabela
            print(f"   • {nome}")
        
        print()
        print(f"✅ Total de índices de performance: {len(indices)}")
        print()
        
        # Tamanho dos índices
        print("💾 Tamanho dos índices:")
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid::regclass)) as tamanho
            FROM pg_indexes
            JOIN pg_stat_user_indexes USING (schemaname, tablename, indexname)
            WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
            ORDER BY pg_relation_size(indexrelid::regclass) DESC
            LIMIT 10;
        """)
        
        for schema, tabela, nome, tamanho in cursor.fetchall():
            print(f"   {nome:40s} {tamanho:>10s}")
            
            cursor.close()
            
            print()
            print("=" * 60)
            print("🎉 Aplicação de índices concluída com sucesso!")
            print()
            print("📌 Próximos passos:")
            print("   1. Reiniciar a aplicação no Railway")
            print("   2. Testar performance em /api/performance/stats")
            print("   3. Monitorar queries lentas com /api/performance/slow-queries")
            print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = aplicar_indices()
    sys.exit(0 if sucesso else 1)

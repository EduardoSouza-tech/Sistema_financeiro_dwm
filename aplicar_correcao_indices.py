"""
Script para aplicar índices de correção no PostgreSQL
"""
import os
import sys
import database_postgresql

def aplicar_correcoes():
    """Aplica os 2 índices que falharam"""
    print("🔧 Aplicando correções dos índices...")
    
    try:
        with database_postgresql.get_db_connection() as conn:
            cursor = conn.cursor()
            print("✅ Conexão estabelecida!")
            
            # Índice 1: contratos ativos
            print("\n[1/2] Criando idx_contratos_ativo...", end=" ")
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contratos_ativo 
                    ON contratos(status, data_inicio DESC) 
                    WHERE status = 'ativo'
                """)
                conn.commit()
                print("✅")
            except Exception as e:
                print(f"❌ {e}")
            
            # Índice 2: transacoes_extrato filtros
            print("[2/2] Criando idx_transacoes_extrato_filtros...", end=" ")
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_filtros 
                    ON transacoes_extrato(empresa_id, conta_bancaria, data DESC, conciliado)
                """)
                conn.commit()
                print("✅")
            except Exception as e:
                print(f"❌ {e}")
            
            # Executar ANALYZE
            print("\n📊 Atualizando estatísticas (ANALYZE)...", end=" ")
            cursor.execute("ANALYZE;")
            conn.commit()
            print("✅")
            
            # Listar todos os índices de performance
            print("\n📋 Índices de performance instalados:")
            cursor.execute("""
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public' 
                  AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname
            """)
            
            indices = cursor.fetchall()
            tabela_atual = None
            
            for tabela, nome in indices:
                if tabela != tabela_atual:
                    print(f"\n📦 {tabela}:")
                    tabela_atual = tabela
                print(f"   • {nome}")
            
            print(f"\n✅ Total: {len(indices)} índices de performance")
            
            cursor.close()
            
        print("\n🎉 Correções aplicadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = aplicar_correcoes()
    sys.exit(0 if sucesso else 1)

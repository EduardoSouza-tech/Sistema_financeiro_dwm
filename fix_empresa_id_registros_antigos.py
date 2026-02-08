#!/usr/bin/env python3
"""
Script de correção: Adicionar empresa_id em registros antigos
Executa via DATABASE_URL do Railway
"""
import os
import sys

# Adicionar o diretório pai ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_postgresql import get_db_connection

def fix_empresa_id_registros_antigos():
    """Atualiza registros sem empresa_id"""
    
    print("\n" + "="*80)
    print("🔧 INICIANDO CORREÇÃO: Adicionar empresa_id em registros antigos")
    print("="*80 + "\n")
    
    # Conectar usando allow_global=True pois vamos fazer UPDATEs diretos
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # 1. Análise inicial
        print("📊 ANÁLISE INICIAL - Contando registros sem empresa_id...\n")
        
        tabelas = ['contratos', 'sessoes', 'lancamentos', 'clientes', 'fornecedores', 'categorias']
        
        for tabela in tabelas:
            try:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
                    FROM {tabela}
                """)
                result = cursor.fetchone()
                total = result['total']
                sem_id = result['sem_empresa_id']
                
                status = "✅" if sem_id == 0 else "⚠️"
                print(f"{status} {tabela:20} | Total: {total:3} | Sem empresa_id: {sem_id:3}")
            except Exception as e:
                print(f"❌ Erro ao verificar {tabela}: {e}")
        
        print("\n" + "="*80)
        print("🔧 APLICANDO CORREÇÕES...")
        print("="*80 + "\n")
        
        # 2. Corrigir contratos
        print("🔄 [1/6] Atualizando CONTRATOS...")
        try:
            cursor.execute("""
                UPDATE contratos
                SET empresa_id = COALESCE(
                    (SELECT empresa_id FROM clientes WHERE clientes.id = contratos.cliente_id LIMIT 1),
                    19
                )
                WHERE empresa_id IS NULL
            """)
            count = cursor.rowcount
            print(f"   ✅ {count} contrato(s) atualizado(s)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 3. Corrigir sessões
        print("🔄 [2/6] Atualizando SESSÕES...")
        try:
            cursor.execute("""
                UPDATE sessoes
                SET empresa_id = COALESCE(
                    (SELECT empresa_id FROM contratos WHERE contratos.id = sessoes.contrato_id LIMIT 1),
                    (SELECT empresa_id FROM clientes WHERE clientes.id = sessoes.cliente_id LIMIT 1),
                    19
                )
                WHERE empresa_id IS NULL
            """)
            count = cursor.rowcount
            print(f"   ✅ {count} sessão(ões) atualizada(s)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 4. Corrigir lançamentos
        print("🔄 [3/6] Atualizando LANÇAMENTOS...")
        try:
            cursor.execute("""
                UPDATE lancamentos
                SET empresa_id = 19
                WHERE empresa_id IS NULL
            """)
            count = cursor.rowcount
            print(f"   ✅ {count} lançamento(s) atualizado(s)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 5. Corrigir clientes
        print("🔄 [4/6] Atualizando CLIENTES...")
        try:
            cursor.execute("""
                UPDATE clientes
                SET empresa_id = 19
                WHERE empresa_id IS NULL
            """)
            count = cursor.rowcount
            print(f"   ✅ {count} cliente(s) atualizado(s)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 6. Corrigir fornecedores
        print("🔄 [5/6] Atualizando FORNECEDORES...")
        try:
            cursor.execute("""
                UPDATE fornecedores
                SET empresa_id = 19
                WHERE empresa_id IS NULL
            """)
            count = cursor.rowcount
            print(f"   ✅ {count} fornecedor(es) atualizado(s)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 7. Corrigir categorias
        print("🔄 [6/6] Atualizando CATEGORIAS...")
        try:
            cursor.execute("""
                UPDATE categorias
                SET empresa_id = 19
                WHERE empresa_id IS NULL
            """)
            count = cursor.rowcount
            print(f"   ✅ {count} categoria(s) atualizada(s)")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # Commit
        conn.commit()
        
        # 8. Verificação final
        print("\n" + "="*80)
        print("📊 VERIFICAÇÃO FINAL - Após correção")
        print("="*80 + "\n")
        
        for tabela in tabelas:
            try:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN empresa_id IS NULL THEN 1 END) as sem_empresa_id
                    FROM {tabela}
                """)
                result = cursor.fetchone()
                total = result['total']
                sem_id = result['sem_empresa_id']
                
                status = "✅" if sem_id == 0 else "❌"
                print(f"{status} {tabela:20} | Total: {total:3} | Sem empresa_id: {sem_id:3}")
            except Exception as e:
                print(f"❌ Erro ao verificar {tabela}: {e}")
        
        cursor.close()
        
        print("\n" + "="*80)
        print("✅ CORREÇÃO CONCLUÍDA!")
        print("="*80 + "\n")

if __name__ == "__main__":
    try:
        fix_empresa_id_registros_antigos()
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

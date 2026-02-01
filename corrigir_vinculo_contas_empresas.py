"""
Script para corrigir o vínculo de contas bancárias com empresas
Atualiza o campo proprietario_id das contas para vinculá-las às empresas corretas
"""

import psycopg2
from config import DATABASE_CONFIG

def corrigir_vinculo_contas():
    print("=" * 80)
    print("🔧 CORREÇÃO DE VÍNCULO: CONTAS BANCÁRIAS ↔ EMPRESAS")
    print("=" * 80)
    
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 1. Ver contas sem proprietario_id ou com proprietario_id incorreto
        print("\n📋 Verificando contas existentes...")
        cursor.execute("""
            SELECT id, nome, banco, proprietario_id 
            FROM contas_bancarias 
            ORDER BY nome
        """)
        contas = cursor.fetchall()
        
        print(f"✅ Total de contas encontradas: {len(contas)}")
        for conta in contas:
            print(f"   - ID: {conta[0]}, Nome: {conta[1]}, Banco: {conta[2]}, Proprietário: {conta[3]}")
        
        # 2. Ver empresas disponíveis
        print("\n🏢 Verificando empresas existentes...")
        cursor.execute("""
            SELECT id, razao_social 
            FROM empresas 
            ORDER BY id
        """)
        empresas = cursor.fetchall()
        
        print(f"✅ Total de empresas encontradas: {len(empresas)}")
        for empresa in empresas:
            print(f"   - ID: {empresa[0]}, Razão Social: {empresa[1]}")
        
        # 3. Atualizar contas para vinculá-las à empresa COOPSERVICOS (ID 20)
        # Assumindo que todas as contas atuais são da COOPSERVICOS
        print("\n🔄 Atualizando vínculo das contas...")
        
        empresa_padrao_id = 20  # COOPSERVICOS
        contas_atualizadas = 0
        
        for conta in contas:
            conta_id = conta[0]
            proprietario_atual = conta[3]
            
            if proprietario_atual != empresa_padrao_id:
                cursor.execute("""
                    UPDATE contas_bancarias 
                    SET proprietario_id = %s 
                    WHERE id = %s
                """, (empresa_padrao_id, conta_id))
                contas_atualizadas += 1
                print(f"   ✅ Conta '{conta[1]}' vinculada à empresa {empresa_padrao_id}")
        
        conn.commit()
        
        print(f"\n✅ {contas_atualizadas} conta(s) atualizada(s) com sucesso!")
        
        # 4. Verificar resultado
        print("\n📊 Verificando resultado final...")
        cursor.execute("""
            SELECT c.nome, c.banco, c.proprietario_id, e.razao_social
            FROM contas_bancarias c
            LEFT JOIN empresas e ON c.proprietario_id = e.id
            ORDER BY c.nome
        """)
        resultado = cursor.fetchall()
        
        print(f"✅ Contas após atualização:")
        for row in resultado:
            print(f"   - {row[0]} ({row[1]}) → Empresa: {row[3] or 'SEM VÍNCULO'} (ID: {row[2]})")
        
        print("\n" + "=" * 80)
        print("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    corrigir_vinculo_contas()

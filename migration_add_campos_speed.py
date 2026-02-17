"""
Migration: Adiciona campos para integração com Speed (Contábil, Fiscal, Contribuições)

Objetivo: Permitir mapeamento de contas internas com códigos Speed e Referencial RFB

Campos adicionados:
- codigo_speed: Código da conta no sistema Speed
- codigo_referencial: Código do Referencial Contábil da RFB
- natureza_sped: Natureza da conta para SPED (01 a 09)

Data: 17/02/2026
"""

import sys
import os
import psycopg2

# DATABASE_URL do Railway
DATABASE_URL = os.getenv('DATABASE_URL') or 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

def aplicar_migration():
    """Aplica migration para adicionar campos Speed"""
    print("🚀 Iniciando migration - Campos Speed/Referencial...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar se campos já existem
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'plano_contas' 
              AND column_name IN ('codigo_speed', 'codigo_referencial', 'natureza_sped')
        """)
        campos_existentes = [row[0] for row in cursor.fetchall()]
        
        if len(campos_existentes) == 3:
            print("⚠️  Campos já existem. Migration já foi aplicada.")
            cursor.close()
            conn.close()
            return
        
        print(f"📝 Campos existentes: {campos_existentes}")
        
        # Adicionar campo codigo_speed
        if 'codigo_speed' not in campos_existentes:
            print("   Adicionando campo codigo_speed...")
            cursor.execute("""
                ALTER TABLE plano_contas 
                ADD COLUMN codigo_speed VARCHAR(30)
            """)
            print("   ✅ Campo codigo_speed adicionado")
        
        # Adicionar campo codigo_referencial
        if 'codigo_referencial' not in campos_existentes:
            print("   Adicionando campo codigo_referencial...")
            cursor.execute("""
                ALTER TABLE plano_contas 
                ADD COLUMN codigo_referencial VARCHAR(50)
            """)
            print("   ✅ Campo codigo_referencial adicionado")
        
        # Adicionar campo natureza_sped
        if 'natureza_sped' not in campos_existentes:
            print("   Adicionando campo natureza_sped...")
            cursor.execute("""
                ALTER TABLE plano_contas 
                ADD COLUMN natureza_sped VARCHAR(2) DEFAULT '01'
            """)
            print("   ✅ Campo natureza_sped adicionado")
        
        # Criar índice para busca por codigo_speed
        print("   Criando índice idx_plano_contas_speed...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_plano_contas_speed 
            ON plano_contas(codigo_speed) 
            WHERE codigo_speed IS NOT NULL
        """)
        print("   ✅ Índice criado")
        
        # Adicionar comentários nos campos
        print("   Adicionando comentários...")
        cursor.execute("""
            COMMENT ON COLUMN plano_contas.codigo_speed IS 
            'Código da conta no sistema Speed (Contábil/Fiscal/Contribuições)';
            
            COMMENT ON COLUMN plano_contas.codigo_referencial IS 
            'Código do Plano de Contas Referencial da RFB (ex: 1.01.01.01.01)';
            
            COMMENT ON COLUMN plano_contas.natureza_sped IS 
            'Natureza da conta para SPED: 01=Contas de ativo, 02=Contas de passivo, 03=PL, 04=Contas de resultado credora, 05=Contas de resultado devedora, 09=Outras';
        """)
        print("   ✅ Comentários adicionados")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ Migration concluída com sucesso!")
        print("\n📊 Campos adicionados à tabela plano_contas:")
        print("   - codigo_speed VARCHAR(30)")
        print("   - codigo_referencial VARCHAR(50)")
        print("   - natureza_sped VARCHAR(2) DEFAULT '01'")
        print("\n🔍 Índice criado: idx_plano_contas_speed")
        
        # Mostrar exemplo de uso
        print("\n💡 Exemplo de uso:")
        print("   UPDATE plano_contas SET")
        print("      codigo_speed = '1.1.01.001',")
        print("      codigo_referencial = '1.01.01.01.01',")
        print("      natureza_sped = '01'")
        print("   WHERE codigo = '1.1.01.001';")
        
    except Exception as e:
        print(f"\n❌ Erro ao aplicar migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def reverter_migration():
    """Reverte a migration (remove campos)"""
    print("⚠️  Revertendo migration - Campos Speed/Referencial...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("   Removendo índice...")
        cursor.execute("DROP INDEX IF EXISTS idx_plano_contas_speed")
        
        print("   Removendo campos...")
        cursor.execute("""
            ALTER TABLE plano_contas 
            DROP COLUMN IF EXISTS codigo_speed,
            DROP COLUMN IF EXISTS codigo_referencial,
            DROP COLUMN IF EXISTS natureza_sped
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Migration revertida com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao reverter migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration - Campos Speed/Referencial')
    parser.add_argument('--revert', action='store_true', help='Reverte a migration')
    args = parser.parse_args()
    
    if args.revert:
        confirmar = input("⚠️  Tem certeza que deseja reverter? (sim/não): ")
        if confirmar.lower() == 'sim':
            reverter_migration()
        else:
            print("❌ Operação cancelada")
    else:
        aplicar_migration()

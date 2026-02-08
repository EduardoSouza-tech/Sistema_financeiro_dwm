"""
Script para aplicar Migration de Controle de Horas
===================================================

Aplica as alterações do migration_controle_horas.sql no banco de dados.

Executa:
- Adiciona colunas de controle de horas em contratos
- Adiciona colunas de status e horas em sessões
- Cria funções e triggers para dedução automática
- Ativa controle de horas em contratos existentes

Uso:
    python aplicar_migration_controle_horas.py

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

import sys
from database_postgresql import get_db_connection

def aplicar_migration():
    """Aplica o migration de controle de horas"""
    
    print("\n" + "="*70)
    print("🔧 MIGRATION: Controle de Horas em Contratos")
    print("="*70 + "\n")
    
    # Ler arquivo SQL
    try:
        with open('migration_controle_horas.sql', 'r', encoding='utf-8') as f:
            sql_completo = f.read()
    except FileNotFoundError:
        print("❌ Erro: Arquivo migration_controle_horas.sql não encontrado")
        return False
    
    # Conectar ao banco (sem empresa_id para operações DDL)
    try:
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            # Dividir SQL em comandos individuais
            comandos = sql_completo.split(';')
            
            sucesso = 0
            erro = 0
            
            for i, comando in enumerate(comandos, 1):
                # Limpar comando
                comando_limpo = comando.strip()
                
                # Pular comentários e comandos vazios
                if not comando_limpo or comando_limpo.startswith('--') or comando_limpo.startswith('/*'):
                    continue
                
                # Pular seções de análise (SELECTs finais)
                if 'Verificar contratos com controle de horas' in comando_limpo:
                    print(f"\n📊 Pulando seção de análise (será executada manualmente)")
                    break
                
                try:
                    print(f"\n[{i}/{len(comandos)}] Executando comando... ", end='')
                    
                    # Executar comando
                    cursor.execute(comando_limpo)
                    
                    # Verificar tipo de comando
                    if 'ALTER TABLE' in comando_limpo.upper():
                        print("✅ Colunas adicionadas")
                    elif 'CREATE INDEX' in comando_limpo.upper():
                        print("✅ Índice criado")
                    elif 'CREATE OR REPLACE FUNCTION' in comando_limpo.upper():
                        print("✅ Função criada")
                    elif 'CREATE TRIGGER' in comando_limpo.upper():
                        print("✅ Trigger criado")
                    elif 'UPDATE' in comando_limpo.upper():
                        rows = cursor.rowcount
                        print(f"✅ {rows} registros atualizados")
                    elif 'COMMENT ON' in comando_limpo.upper():
                        print("✅ Comentário adicionado")
                    else:
                        print("✅ OK")
                    
                    sucesso += 1
                    
                except Exception as e:
                    erro_str = str(e)
                    
                    # Ignorar erros de "já existe"
                    if 'already exists' in erro_str or 'já existe' in erro_str:
                        print("⚠️ Já existe (pulando)")
                    elif 'does not exist' in erro_str and 'column' in erro_str:
                        print("⚠️ Coluna não existe ainda (esperado)")
                    else:
                        print(f"❌ Erro: {erro_str}")
                        erro += 1
            
            # Commit
            conn.commit()
            
            print("\n" + "="*70)
            print(f"📊 RESUMO")
            print("="*70)
            print(f"✅ Comandos executados com sucesso: {sucesso}")
            print(f"❌ Comandos com erro: {erro}")
            
            if erro == 0:
                print("\n🎉 Migration aplicado com sucesso!")
                
                # Rodar análise
                print("\n" + "="*70)
                print("📊 ANÁLISE PÓS-MIGRATION")
                print("="*70 + "\n")
                
                # Verificar contratos com controle de horas
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN controle_horas_ativo THEN 1 ELSE 0 END) as com_controle
                    FROM contratos
                """)
                result = cursor.fetchone()
                print(f"📊 Contratos: {result['total']} total, {result['com_controle']} com controle de horas")
                
                # Verificar sessões com status
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        status,
                        COUNT(*) as quantidade
                    FROM sessoes
                    GROUP BY status
                    ORDER BY quantidade DESC
                """)
                print(f"\n📊 Sessões por status:")
                for row in cursor.fetchall():
                    status = row['status'] or 'sem_status'
                    qtd = row['quantidade']
                    print(f"   - {status}: {qtd}")
                
                return True
            else:
                print("\n⚠️ Migration aplicado com alguns erros")
                return False
            
    except Exception as e:
        print(f"\n❌ Erro ao aplicar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    sucesso = aplicar_migration()
    sys.exit(0 if sucesso else 1)

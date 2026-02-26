"""
Deleta importação específica que está causando conflito
"""

import psycopg2
import psycopg2.extras

# Credenciais Railway
DB_CONFIG = {
    'host': 'centerbeam.proxy.rlwy.net',
    'port': 12659,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT'
}

def log(msg, tipo='INFO'):
    simbolos = {'INFO': 'ℹ️', 'OK': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'CLEAN': '🧹'}
    print(f"{simbolos.get(tipo, 'ℹ️')} {msg}")

def separador(titulo=""):
    print("\n" + "="*80)
    if titulo:
        print(f"  {titulo}")
        print("="*80)

def main():
    importacao_id = "e47fc965-8659-4395-843c-34e00636d7e1"
    empresa_id = 20
    conta = "SICREDI COOPERATIVA - 0258/78895-2"
    
    separador("DELETAR IMPORTAÇÃO CONFLITANTE")
    
    log(f"Importação ID: {importacao_id}", 'INFO')
    log(f"Empresa: COOPSERVICOS (ID {empresa_id})", 'INFO')
    log(f"Conta: {conta}", 'INFO')
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        log("Conectado ao banco Railway", 'OK')
        
        separador("FASE 1: ANÁLISE")
        
        # Verificar detalhes da importação
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(data) as data_inicio,
                MAX(data) as data_fim,
                SUM(CASE WHEN tipo = 'CREDITO' THEN valor ELSE 0 END) as total_credito,
                SUM(CASE WHEN tipo = 'DEBITO' THEN ABS(valor) ELSE 0 END) as total_debito
            FROM transacoes_extrato
            WHERE importacao_id = %s
            AND empresa_id = %s
        """, (importacao_id, empresa_id))
        
        info = cursor.fetchone()
        
        if not info or info['total'] == 0:
            log("❌ Importação não encontrada ou já foi deletada", 'ERROR')
            cursor.close()
            conn.close()
            return
        
        log(f"Transações: {info['total']}", 'INFO')
        log(f"Período: {info['data_inicio']} até {info['data_fim']}", 'INFO')
        log(f"Créditos: R$ {float(info['total_credito'] or 0):,.2f}", 'INFO')
        log(f"Débitos: R$ {float(info['total_debito'] or 0):,.2f}", 'INFO')
        
        separador("CONFIRMAÇÃO")
        
        print(f"\n⚠️  ATENÇÃO: Esta ação irá DELETAR {info['total']} transação(ões)!")
        print(f"   Período: {info['data_inicio']} até {info['data_fim']}")
        print(f"   Um backup será criado antes da exclusão.")
        
        confirma = input(f"\n❓ Digite 'SIM' para confirmar a exclusão: ").strip().upper()
        
        if confirma != 'SIM':
            log("Operação cancelada pelo usuário", 'INFO')
            cursor.close()
            conn.close()
            return
        
        separador("FASE 2: BACKUP")
        
        # Criar backup
        try:
            cursor.execute("DROP TABLE IF EXISTS transacoes_extrato_backup_importacao CASCADE")
        except:
            pass
        
        cursor.execute("""
            CREATE TABLE transacoes_extrato_backup_importacao AS
            SELECT * FROM transacoes_extrato
            WHERE importacao_id = %s
            AND empresa_id = %s
        """, (importacao_id, empresa_id))
        
        cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato_backup_importacao")
        backup_count = cursor.fetchone()['total']
        
        log(f"Backup criado: {backup_count} transações salvas", 'OK')
        
        separador("FASE 3: EXCLUSÃO")
        
        # Deletar transações
        cursor.execute("""
            DELETE FROM transacoes_extrato
            WHERE importacao_id = %s
            AND empresa_id = %s
        """, (importacao_id, empresa_id))
        
        deletados = cursor.rowcount
        
        log(f"Transações deletadas: {deletados}", 'CLEAN')
        
        # Commit
        conn.commit()
        log("Transação confirmada no banco de dados", 'OK')
        
        cursor.close()
        conn.close()
        
        separador("RESULTADO FINAL")
        
        log(f"✅ Importação deletada com sucesso!", 'OK')
        log(f"   {deletados} transação(ões) removida(s)", 'CLEAN')
        log(f"   Backup: transacoes_extrato_backup_importacao", 'INFO')
        log(f"   Agora você pode importar o extrato OFX!", 'OK')
        
        print("\n" + "="*80)
        print("\n🎯 PRÓXIMO PASSO: Tente importar 'Sicredi Janeiro.ofx' novamente!")
        print("="*80 + "\n")
        
    except Exception as e:
        log(f"ERRO: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()
            log("Rollback executado - nenhuma alteração foi feita", 'INFO')

if __name__ == "__main__":
    main()

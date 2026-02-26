"""
Executa limpeza de transações órfãs diretamente no banco Railway
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
    separador("LIMPEZA DE TRANSAÇÕES ÓRFÃS - BANCO RAILWAY")
    
    try:
        # Conectar
        log("Conectando ao banco Railway...", 'INFO')
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        log("Conectado com sucesso!", 'OK')
        
        separador("FASE 1: ANÁLISE")
        
        # Verificar transações órfãs
        cursor.execute("""
            SELECT COUNT(*) as total,
                   MIN(data) as data_inicio,
                   MAX(data) as data_fim,
                   SUM(CASE WHEN tipo = 'CREDITO' THEN valor ELSE 0 END) as total_credito,
                   SUM(CASE WHEN tipo = 'DEBITO' THEN ABS(valor) ELSE 0 END) as total_debito,
                   COUNT(DISTINCT conta_bancaria) as total_contas,
                   COUNT(DISTINCT empresa_id) as total_empresas
            FROM transacoes_extrato
            WHERE (importacao_id IS NULL OR importacao_id = '')
        """)
        
        info = cursor.fetchone()
        total_orfas = info['total'] if info else 0
        
        if total_orfas == 0:
            log("Nenhuma transação órfã encontrada! Sistema está limpo.", 'OK')
            cursor.close()
            conn.close()
            return
        
        # Exibir estatísticas
        log(f"Transações órfãs detectadas: {total_orfas}", 'WARNING')
        log(f"Período: {info['data_inicio']} até {info['data_fim']}", 'INFO')
        log(f"Créditos: R$ {float(info['total_credito'] or 0):,.2f}", 'INFO')
        log(f"Débitos: R$ {float(info['total_debito'] or 0):,.2f}", 'INFO')
        log(f"Empresas afetadas: {info['total_empresas']}", 'INFO')
        log(f"Contas afetadas: {info['total_contas']}", 'INFO')
        
        # Detalhamento por conta
        separador("DETALHAMENTO POR CONTA")
        
        cursor.execute("""
            SELECT 
                conta_bancaria,
                empresa_id,
                COUNT(*) as qtd,
                MIN(data) as data_inicio,
                MAX(data) as data_fim
            FROM transacoes_extrato
            WHERE (importacao_id IS NULL OR importacao_id = '')
            GROUP BY conta_bancaria, empresa_id
            ORDER BY qtd DESC
        """)
        
        detalhes = cursor.fetchall()
        
        for i, det in enumerate(detalhes, 1):
            log(f"[{i}] Empresa {det['empresa_id']} | {det['conta_bancaria']}: {det['qtd']} transações ({det['data_inicio']} a {det['data_fim']})", 'INFO')
        
        # Confirmação
        separador("CONFIRMAÇÃO")
        
        print(f"\n⚠️  ATENÇÃO: Esta ação irá DELETAR {total_orfas} transação(ões) órfã(s)!")
        print(f"   As transações serão PERMANENTEMENTE removidas do banco de dados Railway.")
        print(f"   Um backup será criado na tabela 'transacoes_extrato_backup_orfas'.")
        
        confirma1 = input(f"\n❓ Digite 'SIM' para confirmar a exclusão: ").strip().upper()
        
        if confirma1 != 'SIM':
            log("Operação cancelada pelo usuário.", 'INFO')
            cursor.close()
            conn.close()
            return
        
        confirma2 = input(f"❓ Tem CERTEZA? Digite 'CONFIRMO': ").strip().upper()
        
        if confirma2 != 'CONFIRMO':
            log("Operação cancelada pelo usuário.", 'INFO')
            cursor.close()
            conn.close()
            return
        
        separador("FASE 2: BACKUP")
        
        # Criar backup
        try:
            cursor.execute("DROP TABLE IF EXISTS transacoes_extrato_backup_orfas CASCADE")
            log("Tabela de backup antiga removida (se existia)", 'INFO')
        except:
            pass
        
        cursor.execute("""
            CREATE TABLE transacoes_extrato_backup_orfas AS
            SELECT * FROM transacoes_extrato
            WHERE (importacao_id IS NULL OR importacao_id = '')
        """)
        
        cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato_backup_orfas")
        backup_count = cursor.fetchone()['total']
        
        log(f"Backup criado: {backup_count} transações salvas", 'OK')
        
        separador("FASE 3: EXCLUSÃO")
        
        # Deletar transações órfãs
        cursor.execute("""
            DELETE FROM transacoes_extrato
            WHERE (importacao_id IS NULL OR importacao_id = '')
        """)
        
        deletados = cursor.rowcount
        
        log(f"Transações deletadas: {deletados}", 'CLEAN')
        
        # Commit
        conn.commit()
        log("Transação confirmada no banco de dados Railway", 'OK')
        
        cursor.close()
        conn.close()
        
        separador("RESULTADO FINAL")
        
        log(f"✅ Limpeza concluída com sucesso!", 'OK')
        log(f"   {deletados} transação(ões) órfã(s) removida(s)", 'CLEAN')
        log(f"   Backup disponível em: transacoes_extrato_backup_orfas", 'INFO')
        log(f"   Agora você pode reimportar o extrato OFX!", 'OK')
        
        print("\n" + "="*80)
        print("\n🎯 PRÓXIMO PASSO: Tente importar o arquivo 'Sicredi Janeiro.ofx' novamente!")
        print("="*80 + "\n")
        
    except psycopg2.Error as e:
        log(f"ERRO NO BANCO DE DADOS: {e}", 'ERROR')
        if conn:
            conn.rollback()
            log("Rollback executado - nenhuma alteração foi feita", 'INFO')
        return
        
    except Exception as e:
        log(f"ERRO: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()
            log("Rollback executado - nenhuma alteração foi feita", 'INFO')
        return

if __name__ == "__main__":
    main()

"""
Script para Limpar Transações Órfãs (sem importacao_id)

PROBLEMA: Transações antigas sem importacao_id impedem reimportação de extratos
SOLUÇÃO: Este script deleta transações órfãs para permitir nova importação

Uso: 
    python limpar_transacoes_orfas.py

SEGURANÇA: Cria backup antes de deletar
"""

import sys
from database_postgresql import DatabaseManager
import psycopg2.extras

def log(msg, tipo='INFO'):
    simbolos = {'INFO': 'ℹ️', 'OK': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'CLEAN': '🧹'}
    print(f"{simbolos.get(tipo, 'ℹ️')} {msg}")

def separador(titulo=""):
    print("\n" + "="*80)
    if titulo:
        print(f"  {titulo}")
        print("="*80)

def main():
    separador("LIMPEZA DE TRANSAÇÕES ÓRFÃS - EXTRATO BANCÁRIO")
    
    # Solicitar empresa_id
    try:
        empresa_id = int(input("\n📊 Digite o ID da empresa (padrão: 1): ") or "1")
    except ValueError:
        log("ID inválido. Usando empresa_id = 1", 'WARNING')
        empresa_id = 1
    
    # Solicitar conta (opcional)
    conta_bancaria = input("🏦 Digite o nome da conta bancária (Enter para TODAS): ").strip()
    
    log(f"Empresa ID: {empresa_id}", 'INFO')
    if conta_bancaria:
        log(f"Conta: {conta_bancaria}", 'INFO')
    else:
        log("Conta: TODAS", 'INFO')
    
    # Conectar ao banco
    db = DatabaseManager()
    
    try:
        conn = db.get_connection()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        separador("FASE 1: ANÁLISE")
        
        # Contar transações órfãs
        if conta_bancaria:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       MIN(data) as data_inicio,
                       MAX(data) as data_fim,
                       SUM(CASE WHEN tipo = 'CREDITO' THEN valor ELSE 0 END) as total_credito,
                       SUM(CASE WHEN tipo = 'DEBITO' THEN ABS(valor) ELSE 0 END) as total_debito
                FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND conta_bancaria = %s
                AND (importacao_id IS NULL OR importacao_id = '')
            """, (empresa_id, conta_bancaria))
        else:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       MIN(data) as data_inicio,
                       MAX(data) as data_fim,
                       SUM(CASE WHEN tipo = 'CREDITO' THEN valor ELSE 0 END) as total_credito,
                       SUM(CASE WHEN tipo = 'DEBITO' THEN ABS(valor) ELSE 0 END) as total_debito,
                       COUNT(DISTINCT conta_bancaria) as total_contas
                FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND (importacao_id IS NULL OR importacao_id = '')
            """, (empresa_id,))
        
        info = cursor.fetchone()
        total_orfas = info['total'] if info else 0
        
        if total_orfas == 0:
            log("Nenhuma transação órfã encontrada! Sistema está limpo.", 'OK')
            cursor.close()
            conn.close()
            return 0
        
        # Exibir estatísticas
        log(f"Transações órfãs detectadas: {total_orfas}", 'WARNING')
        log(f"Período: {info['data_inicio']} até {info['data_fim']}", 'INFO')
        log(f"Créditos: R$ {float(info['total_credito'] or 0):,.2f}", 'INFO')
        log(f"Débitos: R$ {float(info['total_debito'] or 0):,.2f}", 'INFO')
        
        if not conta_bancaria:
            log(f"Contas afetadas: {info['total_contas']}", 'INFO')
        
        # Listar detalhes
        separador("DETALHAMENTO POR CONTA")
        
        if conta_bancaria:
            query_detalhes = """
                SELECT 
                    conta_bancaria,
                    COUNT(*) as qtd,
                    MIN(data) as data_inicio,
                    MAX(data) as data_fim
                FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND conta_bancaria = %s
                AND (importacao_id IS NULL OR importacao_id = '')
                GROUP BY conta_bancaria
            """
            cursor.execute(query_detalhes, (empresa_id, conta_bancaria))
        else:
            query_detalhes = """
                SELECT 
                    conta_bancaria,
                    COUNT(*) as qtd,
                    MIN(data) as data_inicio,
                    MAX(data) as data_fim
                FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND (importacao_id IS NULL OR importacao_id = '')
                GROUP BY conta_bancaria
                ORDER BY qtd DESC
            """
            cursor.execute(query_detalhes, (empresa_id,))
        
        detalhes = cursor.fetchall()
        
        for i, det in enumerate(detalhes, 1):
            log(f"[{i}] {det['conta_bancaria']}: {det['qtd']} transações ({det['data_inicio']} a {det['data_fim']})", 'INFO')
        
        # Confirmar exclusão
        separador("CONFIRMAÇÃO")
        
        print(f"\n⚠️  ATENÇÃO: Esta ação irá DELETAR {total_orfas} transação(ões) órfã(s)!")
        print(f"   As transações serão PERMANENTEMENTE removidas do banco de dados.")
        print(f"   Um backup será criado na tabela 'transacoes_extrato_backup_orfas'.")
        
        confirma1 = input(f"\n❓ Digite 'SIM' para confirmar a exclusão: ").strip().upper()
        
        if confirma1 != 'SIM':
            log("Operação cancelada pelo usuário.", 'INFO')
            cursor.close()
            conn.close()
            return 0
        
        confirma2 = input(f"❓ Tem CERTEZA? Digite 'CONFIRMO': ").strip().upper()
        
        if confirma2 != 'CONFIRMO':
            log("Operação cancelada pelo usuário.", 'INFO')
            cursor.close()
            conn.close()
            return 0
        
        separador("FASE 2: BACKUP")
        
        # Criar backup
        try:
            cursor.execute("DROP TABLE IF EXISTS transacoes_extrato_backup_orfas CASCADE")
            log("Tabela de backup antiga removida (se existia)", 'INFO')
        except:
            pass
        
        if conta_bancaria:
            cursor.execute("""
                CREATE TABLE transacoes_extrato_backup_orfas AS
                SELECT * FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND conta_bancaria = %s
                AND (importacao_id IS NULL OR importacao_id = '')
            """, (empresa_id, conta_bancaria))
        else:
            cursor.execute("""
                CREATE TABLE transacoes_extrato_backup_orfas AS
                SELECT * FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND (importacao_id IS NULL OR importacao_id = '')
            """, (empresa_id,))
        
        cursor.execute("SELECT COUNT(*) as total FROM transacoes_extrato_backup_orfas")
        backup_count = cursor.fetchone()['total']
        
        log(f"Backup criado: {backup_count} transações salvas em 'transacoes_extrato_backup_orfas'", 'OK')
        
        separador("FASE 3: EXCLUSÃO")
        
        # Deletar transações órfãs
        if conta_bancaria:
            cursor.execute("""
                DELETE FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND conta_bancaria = %s
                AND (importacao_id IS NULL OR importacao_id = '')
            """, (empresa_id, conta_bancaria))
        else:
            cursor.execute("""
                DELETE FROM transacoes_extrato
                WHERE empresa_id = %s 
                AND (importacao_id IS NULL OR importacao_id = '')
            """, (empresa_id,))
        
        deletados = cursor.rowcount
        
        log(f"Transações deletadas: {deletados}", 'CLEAN')
        
        # Commit
        conn.commit()
        log("Transação confirmada no banco de dados", 'OK')
        
        cursor.close()
        conn.close()
        
        separador("RESULTADO FINAL")
        
        log(f"✅ Limpeza concluída com sucesso!", 'OK')
        log(f"   {deletados} transação(ões) órfã(s) removida(s)", 'CLEAN')
        log(f"   Backup disponível em: transacoes_extrato_backup_orfas", 'INFO')
        log(f"   Agora você pode reimportar o extrato OFX!", 'OK')
        
        print("\n" + "="*80)
        
        return 0
    
    except Exception as e:
        log(f"ERRO: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()
            log("Rollback executado - nenhuma alteração foi feita", 'INFO')
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Script de Validação de Integridade do Sistema Financeiro

Verifica:
1. Lançamentos [EXTRATO] órfãos
2. Transações sem FITID
3. Conciliações antigas com lancamento_id
4. Saldos progressivos consistentes
5. Duplicatas em extrato
6. Contas sem movimento

Uso: python validar_integridade_sistema.py
"""

import sys
from database_postgresql import DatabaseManager
import psycopg2.extras
from decimal import Decimal

def log(msg, tipo='INFO'):
    simbolos = {'INFO': 'ℹ️', 'OK': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
    print(f"{simbolos.get(tipo, 'ℹ️')} {msg}")

def criar_separador(titulo):
    print("\n" + "="*80)
    print(f"  {titulo}")
    print("="*80)

def validar_orfaos_extrato(cursor, empresa_id):
    """Verifica se existem lançamentos [EXTRATO] órfãos"""
    criar_separador("1. VALIDANDO LANÇAMENTOS [EXTRATO] ÓRFÃOS")
    
    cursor.execute("""
        SELECT COUNT(*) as total, SUM(valor) as valor_total
        FROM lancamentos
        WHERE descricao LIKE '[EXTRATO]%'
        AND empresa_id = %s
    """, (empresa_id,))
    
    resultado = cursor.fetchone()
    total = resultado['total'] or 0
    valor_total = resultado['valor_total'] or 0
    
    if total == 0:
        log(f"Nenhum lançamento [EXTRATO] órfão encontrado", 'OK')
        return True
    else:
        log(f"ATENÇÃO: {total} lançamentos [EXTRATO] órfãos detectados!", 'ERROR')
        log(f"Valor total: R$ {float(valor_total):,.2f}", 'WARNING')
        log(f"Execute: python deletar_lancamentos_orfaos.py", 'WARNING')
        return False

def validar_transacoes_sem_fitid(cursor, empresa_id):
    """Verifica transações sem FITID (pode ser normal)"""
    criar_separador("2. VALIDANDO TRANSAÇÕES SEM FITID")
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT conta_bancaria) as contas_afetadas
        FROM transacoes_extrato
        WHERE fitid IS NULL
        AND empresa_id = %s
    """, (empresa_id,))
    
    resultado = cursor.fetchone()
    total = resultado['total'] or 0
    contas = resultado['contas_afetadas'] or 0
    
    if total == 0:
        log(f"Todas as transações possuem FITID", 'OK')
    else:
        log(f"{total} transações sem FITID em {contas} conta(s)", 'WARNING')
        log(f"Nota: Alguns bancos não fornecem FITID - isso é aceitável", 'INFO')
    
    return True

def validar_conciliacoes_antigas(cursor, empresa_id):
    """Verifica se ainda existem conciliações com lancamento_id (antigo)"""
    criar_separador("3. VALIDANDO CONCILIAÇÕES ANTIGAS")
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM transacoes_extrato
            WHERE lancamento_id IS NOT NULL
            AND empresa_id = %s
        """, (empresa_id,))
        
        resultado = cursor.fetchone()
        total = resultado['total'] or 0
        
        if total == 0:
            log(f"Nenhuma conciliação antiga (com lancamento_id) encontrada", 'OK')
            return True
        else:
            log(f"ATENÇÃO: {total} conciliações ainda usam lancamento_id!", 'ERROR')
            log(f"Execute a migration: python aplicar_migration_conciliacao.py", 'WARNING')
            return False
    except psycopg2.errors.UndefinedColumn:
        log(f"Coluna lancamento_id não existe mais - Migration aplicada!", 'OK')
        return True

def validar_saldo_progressivo(cursor, empresa_id, conta_bancaria=None):
    """Verifica se os saldos progressivos estão consistentes"""
    criar_separador("4. VALIDANDO SALDOS PROGRESSIVOS")
    
    # Buscar todas as contas ou apenas uma específica
    if conta_bancaria:
        contas_query = "SELECT DISTINCT conta_bancaria FROM transacoes_extrato WHERE empresa_id = %s AND conta_bancaria = %s"
        cursor.execute(contas_query, (empresa_id, conta_bancaria))
    else:
        contas_query = "SELECT DISTINCT conta_bancaria FROM transacoes_extrato WHERE empresa_id = %s"
        cursor.execute(contas_query, (empresa_id,))
    
    contas = cursor.fetchall()
    
    if not contas:
        log(f"Nenhuma transação encontrada para validar", 'WARNING')
        return True
    
    total_inconsistencias = 0
    
    for conta in contas:
        conta_nome = conta['conta_bancaria']
        log(f"Verificando conta: {conta_nome}", 'INFO')
        
        # Buscar saldo inicial da conta
        cursor.execute("""
            SELECT saldo_inicial, data_inicio
            FROM contas_bancarias
            WHERE nome = %s
        """, (conta_nome,))
        
        info_conta = cursor.fetchone()
        saldo_inicial = float(info_conta['saldo_inicial']) if info_conta else 0.0
        
        # Buscar transações ordenadas
        cursor.execute("""
            SELECT id, data, descricao, valor, tipo, saldo
            FROM transacoes_extrato
            WHERE empresa_id = %s AND conta_bancaria = %s
            ORDER BY data ASC, id ASC
        """, (empresa_id, conta_nome))
        
        transacoes = cursor.fetchall()
        saldo_esperado = saldo_inicial
        inconsistencias = 0
        
        for trans in transacoes:
            saldo_esperado += float(trans['valor'])
            saldo_registrado = float(trans['saldo']) if trans['saldo'] else None
            
            if saldo_registrado is not None:
                diferenca = abs(saldo_esperado - saldo_registrado)
                
                if diferenca > 0.01:  # Tolerância de 1 centavo
                    inconsistencias += 1
                    if inconsistencias <= 3:  # Mostrar apenas primeiras 3
                        log(f"  ❌ ID {trans['id']} | {trans['data']} | Esperado: R$ {saldo_esperado:.2f} | Registrado: R$ {saldo_registrado:.2f}", 'ERROR')
        
        if inconsistencias == 0:
            log(f"  ✅ Conta {conta_nome}: {len(transacoes)} transações - Saldos consistentes!", 'OK')
        else:
            log(f"  ⚠️ Conta {conta_nome}: {inconsistencias} inconsistências detectadas", 'WARNING')
            total_inconsistencias += inconsistencias
    
    if total_inconsistencias == 0:
        log(f"Todos os saldos estão consistentes!", 'OK')
        return True
    else:
        log(f"Total de inconsistências: {total_inconsistencias}", 'ERROR')
        return False

def validar_duplicatas(cursor, empresa_id):
    """Verifica duplicatas por FITID ou data+valor+descrição"""
    criar_separador("5. VALIDANDO DUPLICATAS")
    
    # Duplicatas por FITID
    cursor.execute("""
        SELECT fitid, COUNT(*) as qtd, STRING_AGG(CAST(id AS TEXT), ', ') as ids
        FROM transacoes_extrato
        WHERE empresa_id = %s AND fitid IS NOT NULL
        GROUP BY fitid
        HAVING COUNT(*) > 1
    """, (empresa_id,))
    
    duplicatas_fitid = cursor.fetchall()
    
    if duplicatas_fitid:
        log(f"{len(duplicatas_fitid)} grupo(s) de duplicatas por FITID", 'ERROR')
        for dup in duplicatas_fitid[:5]:
            log(f"  FITID: {dup['fitid']} | IDs: {dup['ids']}", 'WARNING')
    else:
        log(f"Nenhuma duplicata por FITID", 'OK')
    
    # Duplicatas por conteúdo
    cursor.execute("""
        SELECT data, descricao, valor, conta_bancaria, COUNT(*) as qtd
        FROM transacoes_extrato
        WHERE empresa_id = %s
        GROUP BY data, descricao, valor, conta_bancaria
        HAVING COUNT(*) > 1
        LIMIT 10
    """, (empresa_id,))
    
    duplicatas_conteudo = cursor.fetchall()
    
    if duplicatas_conteudo:
        log(f"{len(duplicatas_conteudo)} grupo(s) de duplicatas por conteúdo", 'WARNING')
        log(f"Nota: Isso pode ser normal (mesma transação em dias iguais)", 'INFO')
    else:
        log(f"Nenhuma duplicata por conteúdo", 'OK')
    
    return len(duplicatas_fitid) == 0

def validar_contas_sem_movimento(cursor, empresa_id):
    """Verifica contas cadastradas sem nenhuma transação"""
    criar_separador("6. VALIDANDO CONTAS SEM MOVIMENTO")
    
    cursor.execute("""
        SELECT c.nome, c.saldo_inicial, c.ativa,
               (SELECT COUNT(*) FROM transacoes_extrato 
                WHERE conta_bancaria = c.nome AND empresa_id = %s) as qtd_transacoes
        FROM contas_bancarias c
        WHERE c.nome IN (
            SELECT DISTINCT nome FROM contas_bancariasempresa WHERE empresa_id = %s
        )
    """, (empresa_id, empresa_id))
    
    contas = cursor.fetchall()
    sem_movimento = []
    
    for conta in contas:
        if conta['qtd_transacoes'] == 0:
            sem_movimento.append(conta)
            status = "INATIVA" if not conta['ativa'] else "ATIVA"
            log(f"  ⚠️ {conta['nome']} ({status}): Nenhuma transação importada", 'WARNING')
    
    if not sem_movimento:
        log(f"Todas as {len(contas)} contas possuem movimentação", 'OK')
    else:
        log(f"{len(sem_movimento)} de {len(contas)} contas sem movimento", 'WARNING')
        log(f"Dica: Importe o extrato OFX ou considere inativar essas contas", 'INFO')
    
    return True

def gerar_resumo_final(resultados):
    """Gera resumo final da validação"""
    criar_separador("RESUMO FINAL")
    
    total_testes = len(resultados)
    total_ok = sum(1 for r in resultados.values() if r)
    total_falhas = total_testes - total_ok
    
    print(f"\n📊 Resultados:")
    print(f"   Total de testes: {total_testes}")
    print(f"   ✅ Passaram: {total_ok}")
    print(f"   ❌ Falharam: {total_falhas}")
    
    print(f"\n📋 Detalhamento:")
    for nome, passou in resultados.items():
        status = "✅ OK" if passou else "❌ FALHA"
        print(f"   {status} - {nome}")
    
    if total_falhas == 0:
        print(f"\n🎉 PARABÉNS! Sistema está íntegro e funcionando corretamente!")
        return True
    else:
        print(f"\n⚠️ ATENÇÃO: {total_falhas} problema(s) detectado(s). Resolva antes de continuar.")
        return False

def main():
    """Função principal"""
    print("\n" + "🔍 " * 20)
    print("    VALIDAÇÃO DE INTEGRIDADE DO SISTEMA FINANCEIRO")
    print("🔍 " * 20)
    
    # Solicitar empresa_id
    try:
        empresa_id = int(input("\n📊 Digite o ID da empresa para validar (padrão: 1): ") or "1")
    except ValueError:
        print("❌ ID inválido. Usando empresa_id = 1")
        empresa_id = 1
    
    log(f"Validando empresa ID: {empresa_id}", 'INFO')
    
    # Conectar ao banco
    db = DatabaseManager()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Executar validações
            resultados = {
                "Lançamentos [EXTRATO] órfãos": validar_orfaos_extrato(cursor, empresa_id),
                "Transações sem FITID": validar_transacoes_sem_fitid(cursor, empresa_id),
                "Conciliações antigas": validar_conciliacoes_antigas(cursor, empresa_id),
                "Saldos progressivos": validar_saldo_progressivo(cursor, empresa_id),
                "Duplicatas": validar_duplicatas(cursor, empresa_id),
                "Contas sem movimento": validar_contas_sem_movimento(cursor, empresa_id)
            }
            
            cursor.close()
            
            # Gerar resumo
            sucesso = gerar_resumo_final(resultados)
            
            print("\n" + "="*80)
            return 0 if sucesso else 1
    
    except Exception as e:
        log(f"ERRO FATAL: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

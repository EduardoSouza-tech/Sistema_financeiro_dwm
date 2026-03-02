"""
Migração: Criar lançamentos para conciliações antigas
══════════════════════════════════════════════════════════════════════════════

PROBLEMA:
- Conciliações feitas antes de 2026-02-26 apenas marcavam conciliado=TRUE
- NÃO criavam lançamentos em tabela lancamentos
- Transações conciliadas não aparecem em Contas a Pagar/Receber

SOLUÇÃO:
- Buscar todas as transações com conciliado=TRUE
- Verificar se existe lançamento em conciliacoes
- Se NÃO existir, criar lançamento automaticamente

EXECUTAR:
    python migrar_conciliacoes_antigas.py
"""

import os
import sys
from datetime import datetime

# Configurar DATABASE_URL
if 'DATABASE_URL' not in os.environ:
    # Railway PostgreSQL URL
    os.environ['DATABASE_URL'] = input("Digite a DATABASE_URL do PostgreSQL: ").strip()

from database_postgresql import DatabaseManager
from extrato_functions import conciliar_transacao

def log(msg):
    """Log com timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()


def migrar_conciliacoes_antigas():
    """
    Migra conciliações antigas criando lançamentos faltantes
    """
    log("🚀 INICIANDO MIGRAÇÃO DE CONCILIAÇÕES ANTIGAS")
    log("="*80)
    
    db = DatabaseManager()
    
    try:
        # 1. Buscar todas as transações conciliadas (de todas as empresas)
        with db.get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    te.id as transacao_id,
                    te.empresa_id,
                    te.data,
                    te.tipo,
                    te.valor,
                    te.descricao,
                    te.conta_bancaria,
                    te.categoria,
                    te.subcategoria,
                    te.pessoa,
                    c.lancamento_id as lancamento_existente
                FROM transacoes_extrato te
                LEFT JOIN conciliacoes c ON c.transacao_extrato_id = te.id
                WHERE te.conciliado = TRUE
                ORDER BY te.empresa_id, te.data
            """)
            
            transacoes = cursor.fetchall()
            cursor.close()
        
        log(f"📊 Total de transações conciliadas encontradas: {len(transacoes)}")
        
        if not transacoes:
            log("✅ Nenhuma transação conciliada encontrada. Migração não necessária.")
            return
        
        # 2. Separar transações por situação
        com_lancamento = []
        sem_lancamento = []
        
        for t in transacoes:
            if t['lancamento_existente'] is not None:
                com_lancamento.append(t)
            else:
                sem_lancamento.append(t)
        
        log(f"✅ Transações com lançamento: {len(com_lancamento)}")
        log(f"❌ Transações SEM lançamento (precisam migração): {len(sem_lancamento)}")
        log("")
        
        if not sem_lancamento:
            log("✅ Todas as transações conciliadas já têm lançamentos!")
            log("✅ Migração não necessária.")
            return
        
        # 3. Agrupar por empresa para organizar
        from collections import defaultdict
        por_empresa = defaultdict(list)
        
        for t in sem_lancamento:
            por_empresa[t['empresa_id']].append(t)
        
        log(f"📋 Empresas afetadas: {len(por_empresa)}")
        for empresa_id, transacoes_empresa in por_empresa.items():
            log(f"   - Empresa {empresa_id}: {len(transacoes_empresa)} transação(ões)")
        log("")
        
        # 4. Confirmar antes de migrar (aceita --auto-confirm via linha de comando)
        auto_confirm = '--auto-confirm' in sys.argv or '-y' in sys.argv
        
        if auto_confirm:
            log(f"✅ Auto-confirmação ativada. Criando {len(sem_lancamento)} lançamento(s)...")
        else:
            resposta = input(f"⚠️  Deseja criar {len(sem_lancamento)} lançamento(s)? (sim/não): ").strip().lower()
            
            if resposta not in ['sim', 's', 'yes', 'y']:
                log("❌ Migração cancelada pelo usuário.")
                return
        
        log("")
        log("🔄 INICIANDO CRIAÇÃO DE LANÇAMENTOS...")
        log("="*80)
        
        # 5. Criar lançamentos para transações sem lançamento
        criados = 0
        erros = []
        
        for i, transacao in enumerate(sem_lancamento, 1):
            transacao_id = transacao['transacao_id']
            empresa_id = transacao['empresa_id']
            
            try:
                log(f"[{i}/{len(sem_lancamento)}] Criando lançamento para transação {transacao_id} (empresa {empresa_id})...")
                
                # Chamar função de conciliação que cria lançamento automaticamente
                resultado = conciliar_transacao(
                    database=db,
                    empresa_id=empresa_id,
                    transacao_id=transacao_id,
                    lancamento_id='auto'  # Cria novo lançamento
                )
                
                if resultado.get('success'):
                    lancamento_id = resultado.get('lancamento_id')
                    tipo = transacao['tipo']
                    valor = transacao['valor']
                    data = transacao['data']
                    
                    log(f"   ✅ Lançamento #{lancamento_id} criado: {tipo} R$ {abs(valor):.2f} em {data}")
                    criados += 1
                else:
                    erro = resultado.get('error', 'Erro desconhecido')
                    log(f"   ❌ ERRO: {erro}")
                    erros.append({
                        'transacao_id': transacao_id,
                        'empresa_id': empresa_id,
                        'erro': erro
                    })
                
            except Exception as e:
                log(f"   ❌ EXCEÇÃO: {e}")
                erros.append({
                    'transacao_id': transacao_id,
                    'empresa_id': empresa_id,
                    'erro': str(e)
                })
                import traceback
                traceback.print_exc()
        
        # 6. Relatório final
        log("")
        log("="*80)
        log("📊 RELATÓRIO FINAL DA MIGRAÇÃO")
        log("="*80)
        log(f"✅ Lançamentos criados: {criados}")
        log(f"❌ Erros: {len(erros)}")
        log(f"📈 Taxa de sucesso: {(criados/len(sem_lancamento)*100):.1f}%")
        
        if erros:
            log("")
            log("❌ ERROS DETALHADOS:")
            for erro in erros:
                log(f"   - Transação {erro['transacao_id']} (empresa {erro['empresa_id']}): {erro['erro']}")
        
        log("")
        log("✅ MIGRAÇÃO CONCLUÍDA!")
        log("")
        log("🎯 PRÓXIMOS PASSOS:")
        log("   1. Verifique em Contas a Pagar/Receber se os lançamentos aparecem")
        log("   2. Todos os lançamentos criados têm status='PAGO'")
        log("   3. Se estiver tudo OK, pode deletar este script")
        
    except Exception as e:
        log(f"❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        migrar_conciliacoes_antigas()
    except KeyboardInterrupt:
        print("\n\n❌ Migração interrompida pelo usuário (Ctrl+C)")
        sys.exit(1)

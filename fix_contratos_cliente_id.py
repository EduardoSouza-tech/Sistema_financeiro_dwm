"""
Fix: Atualiza cliente_id dos contratos baseado nas sessões vinculadas
Problema: Contratos com cliente_id NULL mas sessões com cliente_id correto
"""
import sys
import database_postgresql as db

def log(msg):
    """Print com flush imediato"""
    print(msg, flush=True)

def fix_contratos_cliente_id():
    """
    Atualiza cliente_id dos contratos baseado nas sessões
    """
    try:
        log("\n" + "="*80)
        log("🔧 INICIANDO CORREÇÃO DE CLIENTE_ID NOS CONTRATOS")
        log("="*80)
        
        # Buscar todos os contratos
        query_contratos = """
            SELECT id, numero, nome, cliente_id, cliente_nome, empresa_id
            FROM contratos
            ORDER BY id
        """
        
        contratos = db.execute_query(query_contratos)
        log(f"\n📋 Total de contratos encontrados: {len(contratos)}")
        
        contratos_corrigidos = 0
        contratos_com_problemas = []
        
        for contrato in contratos:
            contrato_id = contrato['id']
            numero = contrato['numero']
            cliente_id_atual = contrato['cliente_id']
            cliente_nome = contrato['cliente_nome']
            
            log(f"\n{'='*80}")
            log(f"📋 Contrato ID {contrato_id} - {numero}")
            log(f"   Nome contrato: {contrato['nome']}")
            log(f"   Cliente ID atual: {cliente_id_atual}")
            log(f"   Cliente Nome: {cliente_nome}")
            
            # Se já tem cliente_id, pular
            if cliente_id_atual:
                log(f"   ✅ Já tem cliente_id, pulando...")
                continue
            
            # Buscar sessões deste contrato
            query_sessoes = """
                SELECT DISTINCT cliente_id, cliente_nome
                FROM sessoes
                WHERE contrato_id = %s AND cliente_id IS NOT NULL
            """
            
            sessoes = db.execute_query(query_sessoes, (contrato_id,))
            
            if not sessoes:
                log(f"   ⚠️ Sem sessões com cliente_id para este contrato")
                
                # Se tem cliente_nome, tentar buscar pelo nome
                if cliente_nome:
                    query_cliente = """
                        SELECT id, razao_social
                        FROM clientes
                        WHERE razao_social ILIKE %s
                        LIMIT 1
                    """
                    clientes = db.execute_query(query_cliente, (cliente_nome,))
                    
                    if clientes:
                        novo_cliente_id = clientes[0]['id']
                        log(f"   🔍 Cliente encontrado pelo nome: ID {novo_cliente_id}")
                        
                        # Atualizar contrato
                        update_query = """
                            UPDATE contratos
                            SET cliente_id = %s
                            WHERE id = %s
                        """
                        db.execute_update(update_query, (novo_cliente_id, contrato_id))
                        log(f"   ✅ Contrato atualizado com cliente_id {novo_cliente_id}")
                        contratos_corrigidos += 1
                    else:
                        log(f"   ❌ Cliente não encontrado com nome '{cliente_nome}'")
                        contratos_com_problemas.append({
                            'contrato_id': contrato_id,
                            'numero': numero,
                            'cliente_nome': cliente_nome,
                            'motivo': 'Cliente não encontrado'
                        })
                else:
                    log(f"   ❌ Contrato sem cliente_nome para buscar")
                    contratos_com_problemas.append({
                        'contrato_id': contrato_id,
                        'numero': numero,
                        'cliente_nome': None,
                        'motivo': 'Sem cliente_nome'
                    })
                continue
            
            # Se tem múltiplos clientes nas sessões, é um problema
            if len(sessoes) > 1:
                log(f"   ⚠️ ATENÇÃO: Contrato tem sessões de {len(sessoes)} clientes diferentes!")
                for sessao in sessoes:
                    log(f"      - Cliente ID {sessao['cliente_id']}: {sessao['cliente_nome']}")
                contratos_com_problemas.append({
                    'contrato_id': contrato_id,
                    'numero': numero,
                    'cliente_nome': cliente_nome,
                    'motivo': f'Múltiplos clientes ({len(sessoes)})'
                })
                continue
            
            # Atualizar com o cliente_id da sessão
            novo_cliente_id = sessoes[0]['cliente_id']
            novo_cliente_nome = sessoes[0]['cliente_nome']
            
            log(f"   🎯 Atualizando com cliente_id {novo_cliente_id} ({novo_cliente_nome})")
            
            update_query = """
                UPDATE contratos
                SET cliente_id = %s
                WHERE id = %s
            """
            
            db.execute_update(update_query, (novo_cliente_id, contrato_id))
            log(f"   ✅ Contrato atualizado com sucesso!")
            contratos_corrigidos += 1
        
        # Resumo final
        log(f"\n{'='*80}")
        log(f"📊 RESUMO DA CORREÇÃO")
        log(f"{'='*80}")
        log(f"✅ Contratos corrigidos: {contratos_corrigidos}")
        log(f"⚠️ Contratos com problemas: {len(contratos_com_problemas)}")
        
        if contratos_com_problemas:
            log(f"\n⚠️ CONTRATOS QUE PRECISAM DE ATENÇÃO MANUAL:")
            for problema in contratos_com_problemas:
                log(f"\n   📋 Contrato ID {problema['contrato_id']} - {problema['numero']}")
                log(f"      Cliente: {problema['cliente_nome']}")
                log(f"      Motivo: {problema['motivo']}")
        
        log(f"\n{'='*80}")
        log(f"✅ CORREÇÃO CONCLUÍDA!")
        log(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        log(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fix_contratos_cliente_id()

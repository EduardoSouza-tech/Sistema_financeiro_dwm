"""
🔧 CORREÇÃO DO BUG CRÍTICO - CONCILIAÇÃO DE EXTRATO
=====================================================

BUG IDENTIFICADO:
- Endpoint /api/extratos/conciliacao-geral cria lançamentos DUPLICADOS
- Transações já existem em transacoes_extrato (importadas do OFX)
- Sistema cria NOVOS lançamentos em 'lancamentos' com tag [EXTRATO]
- Resultado: dados contados DUAS VEZES

LOCALIZAÇÃO:
- Arquivo: web_server.py
- Endpoint: POST /api/extratos/conciliacao-geral
- Linhas: 4632-4648

SOLUÇÃO:
1. REMOVER a criação de lançamentos durante conciliação
2. Conciliação deve apenas:
   - Marcar transação como conciliada (conciliado=TRUE)
   - Atualizar categoria/subcategoria na transacao_extrato
   - NÃO criar lançamento duplicado

CÓDIGO ATUAL (BUGADO):
```python
lancamento = Lancamento(
    descricao=f"[EXTRATO] {descricao_final}",
    valor=abs(float(transacao['valor'])),
    tipo=tipo,
    categoria=categoria,
    subcategoria=subcategoria,
    data_vencimento=data_transacao,
    data_pagamento=data_transacao,
    conta_bancaria=transacao['conta_bancaria'],
    pessoa=razao_social,
    observacoes=f"Conciliado do extrato bancário. ID Extrato: {transacao_id}",
    status=StatusLancamento.PAGO
)
lancamento_id = db.adicionar_lancamento(lancamento, empresa_id=empresa_id)  # ❌ BUG AQUI

cursor_update.execute(
    "UPDATE transacoes_extrato SET conciliado = TRUE, lancamento_id = %s WHERE id = %s",
    (lancamento_id, transacao_id)  # ❌ lancamento_id não é necessá rio
)
```

CÓDIGO CORRIGIDO:
```python
# 🔧 FIX: Conciliar atualizando APENAS a transação do extrato
# NÃO criar lançamento duplicado - transação já existe em transacoes_extrato
conn_update = db.get_connection()
cursor_update = conn_update.cursor()

cursor_update.execute("""
    UPDATE transacoes_extrato 
    SET 
        conciliado = TRUE,
        categoria = %s,
        subcategoria = %s,
        pessoa = %s,
        observacoes = %s
    WHERE id = %s AND empresa_id = %s
""", (
    categoria,
    subcategoria,
    razao_social,
    f"Conciliado automaticamente em {datetime.now()}",
    transacao_id,
    empresa_id
))

affected_rows = cursor_update.rowcount
conn_update.commit()
cursor_update.close()
conn_update.close()

if affected_rows > 0:
    criados += 1
    print(f"✅ Transação {transacao_id} conciliada")
    logger.info(f"✅ Transação {transacao_id} conciliada")
else:
    erros.append(f"Transação {transacao_id} não pôde ser atualizada")
```

ALTERAÇÕES NECESSÁRIAS NA TABELA transacoes_extrato:
```sql
-- Adicionar colunas para armazenar dados de conciliação
ALTER TABLE transacoes_extrato 
ADD COLUMN IF NOT EXISTS categoria VARCHAR(255),
ADD COLUMN IF NOT EXISTS subcategoria VARCHAR(255),
ADD COLUMN IF NOT EXISTS pessoa VARCHAR(255),
ADD COLUMN IF NOT EXISTS observacoes TEXT;

-- Remover coluna lancamento_id (não é mais necessária)
ALTER TABLE transacoes_extrato 
DROP COLUMN IF EXISTS lancamento_id;
```

IMPACTO:
- ✅ Elimina duplicação de dados
- ✅ Saldo calculado corretamente
- ✅ Extrato é a fonte única de verdade
- ✅ Lançamentos manuais separados de extrato
- ✅ Sem lançamentos órfãos após deletar extrato

TESTE APÓS CORREÇÃO:
1. Importar arquivo OFX → Deve criar apenas em transacoes_extrato
2. Conciliar transações → Deve apenas atualizar transacoes_extrato
3. Verificar lancamentos → Deve ter 0 com [EXTRATO]
4. Deletar extrato → Deve limpar tudo sem deixar órfãos

"""

print(__doc__)

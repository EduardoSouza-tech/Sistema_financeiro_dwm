-- =====================================================
-- CORREÇÃO CRÍTICA - BUG DE DUPLICAÇÃO DE LANÇAMENTOS
-- =====================================================
-- Data: 25/02/2026
-- Bug: Conciliação criava lançamentos duplicados
-- Solução: Armazenar dados de conciliação na própria transacoes_extrato
-- =====================================================

-- 1. Adicionar colunas para armazenar dados de conciliação
ALTER TABLE transacoes_extrato 
ADD COLUMN IF NOT EXISTS categoria VARCHAR(255),
ADD COLUMN IF NOT EXISTS subcategoria VARCHAR(255),
ADD COLUMN IF NOT EXISTS pessoa VARCHAR(255),
ADD COLUMN IF NOT EXISTS observacoes TEXT;

-- 2. Remover coluna lancamento_id (não é mais necessária)
-- Transações do extrato não devem referenciar lançamentos
ALTER TABLE transacoes_extrato 
DROP COLUMN IF EXISTS lancamento_id;

-- 3. Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_conciliado 
ON transacoes_extrato(conciliado, empresa_id);

CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_categoria 
ON transacoes_extrato(categoria, empresa_id) 
WHERE categoria IS NOT NULL;

-- 4. Comentários explicativos
COMMENT ON COLUMN transacoes_extrato.categoria IS 'Categoria atribuída durante conciliação (ex: Folha de Pagamento)';
COMMENT ON COLUMN transacoes_extrato.subcategoria IS 'Subcategoria atribuída durante conciliação (ex: Salários)';
COMMENT ON COLUMN transacoes_extrato.pessoa IS 'Nome do cliente/fornecedor identificado durante conciliação';
COMMENT ON COLUMN transacoes_extrato.observacoes IS 'Observações adicionadas durante conciliação';

-- 5. Verificação
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'transacoes_extrato'
  AND column_name IN ('categoria', 'subcategoria', 'pessoa', 'observacoes', 'conciliado')
ORDER BY column_name;

-- ✅ Após executar esta migration:
-- - Conciliação apenas atualiza transacoes_extrato
-- - Não cria lançamentos duplicados
-- - Extrato é a fonte única de verdade
-- - Sem lançamentos órfãos ao deletar extrato

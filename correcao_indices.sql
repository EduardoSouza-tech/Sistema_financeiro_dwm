-- Índices de correção para as tabelas que falharam

-- 7. Índice parcial para contratos ativos (CORRIGIDO: status = 'ativo')
CREATE INDEX IF NOT EXISTS idx_contratos_ativo 
ON contratos(status, data_inicio DESC) 
WHERE status = 'ativo';

-- 15. Índice para transacoes_extrato (CORRIGIDO: conta_bancaria é VARCHAR)
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_filtros 
ON transacoes_extrato(empresa_id, conta_bancaria, data DESC, conciliado);

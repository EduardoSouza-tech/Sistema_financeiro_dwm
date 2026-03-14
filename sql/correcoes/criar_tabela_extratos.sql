-- Criação da tabela de transações de extrato bancário (OFX)
-- Execute este script no banco de dados PostgreSQL

CREATE TABLE IF NOT EXISTS transacoes_extrato (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    conta_bancaria VARCHAR(255) NOT NULL,
    data DATE NOT NULL,
    descricao TEXT,
    valor DECIMAL(15, 2) NOT NULL,
    tipo VARCHAR(20) NOT NULL, -- 'credito' ou 'debito'
    saldo DECIMAL(15, 2),
    fitid VARCHAR(255), -- ID único da transação no OFX
    memo TEXT,
    checknum VARCHAR(50),
    importacao_id VARCHAR(100), -- UUID da importação
    conciliado BOOLEAN DEFAULT FALSE,
    lancamento_id INTEGER, -- Referência ao lançamento conciliado
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para melhorar performance
    CONSTRAINT uk_fitid_empresa UNIQUE (fitid, empresa_id)
);

-- Índices adicionais
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_empresa ON transacoes_extrato(empresa_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_conta ON transacoes_extrato(conta_bancaria);
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_data ON transacoes_extrato(data);
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_importacao ON transacoes_extrato(importacao_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_extrato_conciliado ON transacoes_extrato(conciliado);

-- Comentários
COMMENT ON TABLE transacoes_extrato IS 'Transações bancárias importadas de arquivos OFX';
COMMENT ON COLUMN transacoes_extrato.fitid IS 'ID único da transação fornecido pelo banco (Financial Transaction ID)';
COMMENT ON COLUMN transacoes_extrato.importacao_id IS 'UUID que agrupa transações da mesma importação';
COMMENT ON COLUMN transacoes_extrato.conciliado IS 'Indica se a transação foi conciliada com um lançamento';
COMMENT ON COLUMN transacoes_extrato.lancamento_id IS 'ID do lançamento associado após conciliação';

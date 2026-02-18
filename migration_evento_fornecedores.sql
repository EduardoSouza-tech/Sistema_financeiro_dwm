-- Migration: Adicionar tabela de fornecedores por evento
-- Permite vincular fornecedores aos eventos com categoria, subcategoria e valor

CREATE TABLE IF NOT EXISTS evento_fornecedores (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE CASCADE,
    categoria_id INTEGER REFERENCES categorias(id),
    subcategoria_id INTEGER REFERENCES subcategorias(id),
    valor NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    observacao TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES usuarios(id),
    
    -- Evitar duplicatas: mesmo fornecedor não pode ser adicionado duas vezes ao mesmo evento
    UNIQUE(evento_id, fornecedor_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_evento ON evento_fornecedores(evento_id);
CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_fornecedor ON evento_fornecedores(fornecedor_id);

-- Comentários
COMMENT ON TABLE evento_fornecedores IS 'Relaciona fornecedores com eventos, incluindo custos e categorização';
COMMENT ON COLUMN evento_fornecedores.evento_id IS 'ID do evento';
COMMENT ON COLUMN evento_fornecedores.fornecedor_id IS 'ID do fornecedor contratado';
COMMENT ON COLUMN evento_fornecedores.categoria_id IS 'Categoria do custo (ex: Alimentação, Transporte)';
COMMENT ON COLUMN evento_fornecedores.subcategoria_id IS 'Subcategoria do custo';
COMMENT ON COLUMN evento_fornecedores.valor IS 'Valor cobrado pelo fornecedor';
COMMENT ON COLUMN evento_fornecedores.observacao IS 'Observações adicionais sobre o serviço';

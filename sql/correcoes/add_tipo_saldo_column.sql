-- Adicionar coluna tipo_saldo_inicial na tabela contas_bancarias
ALTER TABLE contas_bancarias 
ADD COLUMN IF NOT EXISTS tipo_saldo_inicial VARCHAR(10) DEFAULT 'credor' 
CHECK (tipo_saldo_inicial IN ('credor', 'devedor'));

-- Verificar se a coluna foi adicionada
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'contas_bancarias' AND column_name = 'tipo_saldo_inicial';

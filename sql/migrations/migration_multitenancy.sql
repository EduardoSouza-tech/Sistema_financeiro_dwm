-- ================================================================
-- MIGRAÇÃO MULTI-TENANCY - Sistema Financeiro DWM
-- ================================================================
-- Este script adiciona suporte a multi-tenancy isolando dados por cliente
-- Cada cliente verá apenas seus próprios dados
-- Administradores terão acesso total a todos os dados
-- ================================================================

-- ================================================================
-- PASSO 1: Adicionar coluna proprietario_id nas tabelas principais
-- ================================================================

-- Tabela: clientes
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

ALTER TABLE clientes
ADD CONSTRAINT fk_clientes_proprietario 
FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_clientes_proprietario 
ON clientes(proprietario_id);

COMMENT ON COLUMN clientes.proprietario_id IS 'ID do usuário proprietário (cliente) deste registro. NULL = admin criou';

-- Tabela: fornecedores
ALTER TABLE fornecedores 
ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

ALTER TABLE fornecedores
ADD CONSTRAINT fk_fornecedores_proprietario 
FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_fornecedores_proprietario 
ON fornecedores(proprietario_id);

COMMENT ON COLUMN fornecedores.proprietario_id IS 'ID do usuário proprietário (cliente) deste registro. NULL = admin criou';

-- Tabela: lancamentos
ALTER TABLE lancamentos 
ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

ALTER TABLE lancamentos
ADD CONSTRAINT fk_lancamentos_proprietario 
FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_lancamentos_proprietario 
ON lancamentos(proprietario_id);

COMMENT ON COLUMN lancamentos.proprietario_id IS 'ID do usuário proprietário (cliente) deste registro. NULL = admin criou';

-- Tabela: contas_bancarias
ALTER TABLE contas_bancarias 
ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

ALTER TABLE contas_bancarias
ADD CONSTRAINT fk_contas_bancarias_proprietario 
FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_contas_bancarias_proprietario 
ON contas_bancarias(proprietario_id);

COMMENT ON COLUMN contas_bancarias.proprietario_id IS 'ID do usuário proprietário (cliente) deste registro. NULL = admin criou';

-- Tabela: categorias
ALTER TABLE categorias 
ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

ALTER TABLE categorias
ADD CONSTRAINT fk_categorias_proprietario 
FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_categorias_proprietario 
ON categorias(proprietario_id);

COMMENT ON COLUMN categorias.proprietario_id IS 'ID do usuário proprietário (cliente) deste registro. NULL = categoria global (admin)';

-- Tabela: subcategorias
ALTER TABLE subcategorias 
ADD COLUMN IF NOT EXISTS proprietario_id INTEGER;

ALTER TABLE subcategorias
ADD CONSTRAINT fk_subcategorias_proprietario 
FOREIGN KEY (proprietario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_subcategorias_proprietario 
ON subcategorias(proprietario_id);

COMMENT ON COLUMN subcategorias.proprietario_id IS 'ID do usuário proprietário (cliente) deste registro. NULL = subcategoria global (admin)';

-- ================================================================
-- PASSO 2: Migrar dados existentes (OPCIONAL)
-- ================================================================
-- Por padrão, dados existentes ficam com proprietario_id = NULL (admin)
-- Se quiser atribuir a um usuário específico, descomentar e ajustar:

-- UPDATE clientes SET proprietario_id = 1 WHERE proprietario_id IS NULL;
-- UPDATE fornecedores SET proprietario_id = 1 WHERE proprietario_id IS NULL;
-- UPDATE lancamentos SET proprietario_id = 1 WHERE proprietario_id IS NULL;
-- UPDATE contas_bancarias SET proprietario_id = 1 WHERE proprietario_id IS NULL;

-- ================================================================
-- PASSO 3: Criar view auxiliar para debug/admin
-- ================================================================

CREATE OR REPLACE VIEW vw_dados_multi_tenancy AS
SELECT 
    'clientes' as tabela,
    id,
    nome,
    proprietario_id,
    u.nome_completo as proprietario_nome,
    u.tipo as proprietario_tipo
FROM clientes c
LEFT JOIN usuarios u ON c.proprietario_id = u.id

UNION ALL

SELECT 
    'fornecedores' as tabela,
    id,
    nome,
    proprietario_id,
    u.nome_completo as proprietario_nome,
    u.tipo as proprietario_tipo
FROM fornecedores f
LEFT JOIN usuarios u ON f.proprietario_id = u.id

UNION ALL

SELECT 
    'lancamentos' as tabela,
    id,
    descricao::text as nome,
    proprietario_id,
    u.nome_completo as proprietario_nome,
    u.tipo as proprietario_tipo
FROM lancamentos l
LEFT JOIN usuarios u ON l.proprietario_id = u.id

UNION ALL

SELECT 
    'contas_bancarias' as tabela,
    id,
    nome,
    proprietario_id,
    u.nome_completo as proprietario_nome,
    u.tipo as proprietario_tipo
FROM contas_bancarias cb
LEFT JOIN usuarios u ON cb.proprietario_id = u.id;

-- ================================================================
-- PASSO 4: Verificação e estatísticas
-- ================================================================

-- Verificar distribuição de dados por proprietário
CREATE OR REPLACE VIEW vw_estatisticas_multi_tenancy AS
SELECT 
    u.id as usuario_id,
    u.nome_completo,
    u.tipo,
    COUNT(DISTINCT c.id) as total_clientes,
    COUNT(DISTINCT f.id) as total_fornecedores,
    COUNT(DISTINCT l.id) as total_lancamentos,
    COUNT(DISTINCT cb.id) as total_contas
FROM usuarios u
LEFT JOIN clientes c ON c.proprietario_id = u.id
LEFT JOIN fornecedores f ON f.proprietario_id = u.id
LEFT JOIN lancamentos l ON l.proprietario_id = u.id
LEFT JOIN contas_bancarias cb ON cb.proprietario_id = u.id
WHERE u.tipo = 'cliente'
GROUP BY u.id, u.nome_completo, u.tipo

UNION ALL

SELECT 
    NULL as usuario_id,
    'Admin (Dados Globais)' as nome_completo,
    'admin' as tipo,
    COUNT(DISTINCT c.id) as total_clientes,
    COUNT(DISTINCT f.id) as total_fornecedores,
    COUNT(DISTINCT l.id) as total_lancamentos,
    COUNT(DISTINCT cb.id) as total_contas
FROM clientes c
FULL OUTER JOIN fornecedores f ON f.proprietario_id IS NULL
FULL OUTER JOIN lancamentos l ON l.proprietario_id IS NULL
FULL OUTER JOIN contas_bancarias cb ON cb.proprietario_id IS NULL
WHERE c.proprietario_id IS NULL 
   OR f.proprietario_id IS NULL 
   OR l.proprietario_id IS NULL 
   OR cb.proprietario_id IS NULL;

-- ================================================================
-- QUERIES ÚTEIS PARA DEBUG
-- ================================================================

-- Ver todos os dados com seus proprietários
-- SELECT * FROM vw_dados_multi_tenancy ORDER BY tabela, proprietario_id;

-- Ver estatísticas por usuário
-- SELECT * FROM vw_estatisticas_multi_tenancy ORDER BY tipo, nome_completo;

-- Contar registros sem proprietário (dados globais/admin)
-- SELECT 
--     'clientes' as tabela, COUNT(*) as sem_proprietario 
-- FROM clientes WHERE proprietario_id IS NULL
-- UNION ALL
-- SELECT 'fornecedores', COUNT(*) FROM fornecedores WHERE proprietario_id IS NULL
-- UNION ALL
-- SELECT 'lancamentos', COUNT(*) FROM lancamentos WHERE proprietario_id IS NULL
-- UNION ALL
-- SELECT 'contas_bancarias', COUNT(*) FROM contas_bancarias WHERE proprietario_id IS NULL;

-- ================================================================
-- ROLLBACK (Caso necessário)
-- ================================================================
-- ATENÇÃO: Só execute se quiser reverter as mudanças!
-- 
-- DROP VIEW IF EXISTS vw_dados_multi_tenancy;
-- DROP VIEW IF EXISTS vw_estatisticas_multi_tenancy;
-- 
-- ALTER TABLE clientes DROP CONSTRAINT IF EXISTS fk_clientes_proprietario;
-- ALTER TABLE fornecedores DROP CONSTRAINT IF EXISTS fk_fornecedores_proprietario;
-- ALTER TABLE lancamentos DROP CONSTRAINT IF EXISTS fk_lancamentos_proprietario;
-- ALTER TABLE contas_bancarias DROP CONSTRAINT IF EXISTS fk_contas_bancarias_proprietario;
-- ALTER TABLE categorias DROP CONSTRAINT IF EXISTS fk_categorias_proprietario;
-- ALTER TABLE subcategorias DROP CONSTRAINT IF EXISTS fk_subcategorias_proprietario;
-- 
-- ALTER TABLE clientes DROP COLUMN IF EXISTS proprietario_id;
-- ALTER TABLE fornecedores DROP COLUMN IF EXISTS proprietario_id;
-- ALTER TABLE lancamentos DROP COLUMN IF EXISTS proprietario_id;
-- ALTER TABLE contas_bancarias DROP COLUMN IF EXISTS proprietario_id;
-- ALTER TABLE categorias DROP COLUMN IF EXISTS proprietario_id;
-- ALTER TABLE subcategorias DROP COLUMN IF EXISTS proprietario_id;

-- ================================================================
-- FIM DA MIGRAÇÃO
-- ================================================================

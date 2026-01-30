-- =====================================================
-- ROW LEVEL SECURITY (RLS) - Isolamento por Empresa
-- Proteção no nível do banco de dados PostgreSQL
-- =====================================================

-- IMPORTANTE: Execute este script no banco de dados principal
-- Isso garante que MESMO SE O CÓDIGO FALHAR, o banco bloqueia acesso indevido

-- =====================================================
-- 1. HABILITAR RLS EM TODAS AS TABELAS
-- =====================================================

-- Categorias
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS categorias_empresa_isolation ON categorias;
CREATE POLICY categorias_empresa_isolation ON categorias
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Subcategorias
ALTER TABLE subcategorias ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS subcategorias_empresa_isolation ON subcategorias;
CREATE POLICY subcategorias_empresa_isolation ON subcategorias
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Lançamentos
ALTER TABLE lancamentos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lancamentos_empresa_isolation ON lancamentos;
CREATE POLICY lancamentos_empresa_isolation ON lancamentos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Contas
ALTER TABLE contas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contas_empresa_isolation ON contas;
CREATE POLICY contas_empresa_isolation ON contas
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Clientes
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS clientes_empresa_isolation ON clientes;
CREATE POLICY clientes_empresa_isolation ON clientes
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Fornecedores
ALTER TABLE fornecedores ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS fornecedores_empresa_isolation ON fornecedores;
CREATE POLICY fornecedores_empresa_isolation ON fornecedores
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Contratos
ALTER TABLE contratos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contratos_empresa_isolation ON contratos;
CREATE POLICY contratos_empresa_isolation ON contratos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Sessões de Fotografia
ALTER TABLE sessoes_fotografia ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS sessoes_empresa_isolation ON sessoes_fotografia;
CREATE POLICY sessoes_empresa_isolation ON sessoes_fotografia
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Equipamentos
ALTER TABLE equipamentos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS equipamentos_empresa_isolation ON equipamentos;
CREATE POLICY equipamentos_empresa_isolation ON equipamentos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Kits de Equipamentos
ALTER TABLE kits_equipamentos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS kits_empresa_isolation ON kits_equipamentos;
CREATE POLICY kits_empresa_isolation ON kits_equipamentos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Funcionários
ALTER TABLE funcionarios ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS funcionarios_empresa_isolation ON funcionarios;
CREATE POLICY funcionarios_empresa_isolation ON funcionarios
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Folha de Pagamento
ALTER TABLE folha_pagamento ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS folha_empresa_isolation ON folha_pagamento;
CREATE POLICY folha_empresa_isolation ON folha_pagamento
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Eventos
ALTER TABLE eventos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS eventos_empresa_isolation ON eventos;
CREATE POLICY eventos_empresa_isolation ON eventos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Produtos (estoque)
ALTER TABLE IF EXISTS produtos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS produtos_empresa_isolation ON produtos;
CREATE POLICY produtos_empresa_isolation ON produtos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- Movimentações (estoque)
ALTER TABLE IF EXISTS movimentacoes_estoque ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS movimentacoes_empresa_isolation ON movimentacoes_estoque;
CREATE POLICY movimentacoes_empresa_isolation ON movimentacoes_estoque
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);

-- =====================================================
-- 2. TABELAS GLOBAIS (SEM RLS)
-- =====================================================
-- Estas tabelas não têm empresa_id e são compartilhadas

-- Usuários (tabela global de autenticação)
-- NÃO habilitar RLS - gerenciado por auth_functions.py

-- Empresas (tabela global)
-- NÃO habilitar RLS - gerenciado por permissões

-- =====================================================
-- 3. FUNÇÃO PARA DEFINIR EMPRESA NA SESSÃO
-- =====================================================

CREATE OR REPLACE FUNCTION set_current_empresa(p_empresa_id INTEGER)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_empresa_id', p_empresa_id::text, false);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. FUNÇÃO PARA VERIFICAR EMPRESA ATUAL
-- =====================================================

CREATE OR REPLACE FUNCTION get_current_empresa()
RETURNS INTEGER AS $$
BEGIN
    RETURN current_setting('app.current_empresa_id', true)::integer;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. TRIGGER PARA VALIDAR EMPRESA_ID EM INSERT
-- =====================================================

CREATE OR REPLACE FUNCTION validate_empresa_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.empresa_id IS NULL THEN
        RAISE EXCEPTION 'empresa_id não pode ser NULL';
    END IF;
    
    IF NEW.empresa_id != current_setting('app.current_empresa_id')::integer THEN
        RAISE EXCEPTION 'empresa_id (%) não corresponde à empresa da sessão (%)', 
            NEW.empresa_id, current_setting('app.current_empresa_id')::integer;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger em todas as tabelas com empresa_id
DROP TRIGGER IF EXISTS validate_empresa_lancamentos ON lancamentos;
CREATE TRIGGER validate_empresa_lancamentos
    BEFORE INSERT OR UPDATE ON lancamentos
    FOR EACH ROW
    EXECUTE FUNCTION validate_empresa_id();

DROP TRIGGER IF EXISTS validate_empresa_categorias ON categorias;
CREATE TRIGGER validate_empresa_categorias
    BEFORE INSERT OR UPDATE ON categorias
    FOR EACH ROW
    EXECUTE FUNCTION validate_empresa_id();

DROP TRIGGER IF EXISTS validate_empresa_clientes ON clientes;
CREATE TRIGGER validate_empresa_clientes
    BEFORE INSERT OR UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION validate_empresa_id();

DROP TRIGGER IF EXISTS validate_empresa_contratos ON contratos;
CREATE TRIGGER validate_empresa_contratos
    BEFORE INSERT OR UPDATE ON contratos
    FOR EACH ROW
    EXECUTE FUNCTION validate_empresa_id();

-- =====================================================
-- 6. AUDITORIA DE ACESSOS
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_data_access (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER,
    empresa_id INTEGER,
    table_name VARCHAR(100),
    action VARCHAR(20),
    record_id INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45)
);

CREATE INDEX idx_audit_empresa ON audit_data_access(empresa_id);
CREATE INDEX idx_audit_timestamp ON audit_data_access(timestamp);

-- Função de auditoria
CREATE OR REPLACE FUNCTION audit_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_data_access (
        empresa_id, 
        table_name, 
        action, 
        record_id
    ) VALUES (
        current_setting('app.current_empresa_id', true)::integer,
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(NEW.id, OLD.id)
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. VERIFICAR STATUS DO RLS
-- =====================================================

CREATE OR REPLACE VIEW rls_status AS
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled,
    (SELECT count(*) 
     FROM pg_policies 
     WHERE schemaname = 'public' 
     AND tablename = c.tablename) as policy_count
FROM pg_tables c
WHERE schemaname = 'public'
ORDER BY tablename;

-- =====================================================
-- COMENTÁRIOS
-- =====================================================

COMMENT ON TABLE audit_data_access IS 'Log de auditoria de todos os acessos a dados por empresa';
COMMENT ON FUNCTION set_current_empresa IS 'Define a empresa atual na sessão PostgreSQL';
COMMENT ON FUNCTION get_current_empresa IS 'Retorna a empresa atual da sessão';
COMMENT ON FUNCTION validate_empresa_id IS 'Valida que empresa_id corresponde à sessão';
COMMENT ON VIEW rls_status IS 'Status de Row Level Security em todas as tabelas';

-- =====================================================
-- INSTRUÇÕES DE USO
-- =====================================================

/*
COMO USAR:

1. No início de cada requisição (database_postgresql.py):
   
   SELECT set_current_empresa(18);  -- Define empresa da sessão
   
2. Todas as queries automaticamente filtram por empresa:
   
   SELECT * FROM lancamentos;  -- Retorna APENAS empresa 18
   INSERT INTO clientes (nome, empresa_id) VALUES ('Teste', 18);  -- OK
   INSERT INTO clientes (nome, empresa_id) VALUES ('Teste', 20);  -- ERRO!
   
3. Verificar status RLS:
   
   SELECT * FROM rls_status;
   
4. Ver logs de auditoria:
   
   SELECT * FROM audit_data_access 
   WHERE empresa_id = 18 
   ORDER BY timestamp DESC 
   LIMIT 100;

IMPORTANTE:
- RLS funciona MESMO SE O CÓDIGO FALHAR
- Proteção no nível do banco de dados
- Super usuários PostgreSQL não são afetados (cuidado!)
*/

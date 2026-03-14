-- =====================================================
-- ROW LEVEL SECURITY (RLS) - Isolamento por Empresa
-- Versão SEGURA - Ignora tabelas que não existem
-- =====================================================

DO $$ 
BEGIN
    -- Categorias
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'categorias') THEN
        ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS categorias_empresa_isolation ON categorias;
        CREATE POLICY categorias_empresa_isolation ON categorias
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em categorias';
    END IF;

    -- Subcategorias
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'subcategorias') THEN
        ALTER TABLE subcategorias ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS subcategorias_empresa_isolation ON subcategorias;
        CREATE POLICY subcategorias_empresa_isolation ON subcategorias
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em subcategorias';
    END IF;

    -- Lançamentos
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'lancamentos') THEN
        ALTER TABLE lancamentos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS lancamentos_empresa_isolation ON lancamentos;
        CREATE POLICY lancamentos_empresa_isolation ON lancamentos
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em lancamentos';
    END IF;

    -- Contas
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contas') THEN
        ALTER TABLE contas ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS contas_empresa_isolation ON contas;
        CREATE POLICY contas_empresa_isolation ON contas
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em contas';
    END IF;

    -- Clientes
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'clientes') THEN
        ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS clientes_empresa_isolation ON clientes;
        CREATE POLICY clientes_empresa_isolation ON clientes
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em clientes';
    END IF;

    -- Fornecedores
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'fornecedores') THEN
        ALTER TABLE fornecedores ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS fornecedores_empresa_isolation ON fornecedores;
        CREATE POLICY fornecedores_empresa_isolation ON fornecedores
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em fornecedores';
    END IF;

    -- Contratos
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contratos') THEN
        ALTER TABLE contratos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS contratos_empresa_isolation ON contratos;
        CREATE POLICY contratos_empresa_isolation ON contratos
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em contratos';
    END IF;

    -- Sessões de Fotografia
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'sessoes_fotografia') THEN
        ALTER TABLE sessoes_fotografia ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS sessoes_empresa_isolation ON sessoes_fotografia;
        CREATE POLICY sessoes_empresa_isolation ON sessoes_fotografia
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em sessoes_fotografia';
    END IF;

    -- Equipamentos
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'equipamentos') THEN
        ALTER TABLE equipamentos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS equipamentos_empresa_isolation ON equipamentos;
        CREATE POLICY equipamentos_empresa_isolation ON equipamentos
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em equipamentos';
    END IF;

    -- Kits de Equipamentos
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'kits_equipamentos') THEN
        ALTER TABLE kits_equipamentos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS kits_empresa_isolation ON kits_equipamentos;
        CREATE POLICY kits_empresa_isolation ON kits_equipamentos
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em kits_equipamentos';
    END IF;

    -- Funcionários
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'funcionarios') THEN
        ALTER TABLE funcionarios ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS funcionarios_empresa_isolation ON funcionarios;
        CREATE POLICY funcionarios_empresa_isolation ON funcionarios
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em funcionarios';
    END IF;

    -- Folha de Pagamento
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'folha_pagamento') THEN
        ALTER TABLE folha_pagamento ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS folha_empresa_isolation ON folha_pagamento;
        CREATE POLICY folha_empresa_isolation ON folha_pagamento
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em folha_pagamento';
    END IF;

    -- Eventos
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'eventos') THEN
        ALTER TABLE eventos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS eventos_empresa_isolation ON eventos;
        CREATE POLICY eventos_empresa_isolation ON eventos
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em eventos';
    END IF;

    -- Produtos
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'produtos') THEN
        ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS produtos_empresa_isolation ON produtos;
        CREATE POLICY produtos_empresa_isolation ON produtos
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em produtos';
    END IF;

    -- Movimentações de Estoque
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'movimentacoes_estoque') THEN
        ALTER TABLE movimentacoes_estoque ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS movimentacoes_empresa_isolation ON movimentacoes_estoque;
        CREATE POLICY movimentacoes_empresa_isolation ON movimentacoes_estoque
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em movimentacoes_estoque';
    END IF;

    -- Transações de Extrato
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'transacoes_extrato') THEN
        ALTER TABLE transacoes_extrato ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS transacoes_extrato_empresa_isolation ON transacoes_extrato;
        CREATE POLICY transacoes_extrato_empresa_isolation ON transacoes_extrato
            USING (empresa_id = current_setting('app.current_empresa_id')::integer);
        RAISE NOTICE '✅ RLS aplicado em transacoes_extrato';
    END IF;

    RAISE NOTICE '✅ RLS aplicado em todas as tabelas existentes';
END $$;

-- =====================================================
-- FUNÇÕES AUXILIARES
-- =====================================================

CREATE OR REPLACE FUNCTION set_current_empresa(p_empresa_id INTEGER)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_empresa_id', p_empresa_id::text, false);
END;
$$ LANGUAGE plpgsql;

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
-- TRIGGER DE VALIDAÇÃO
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

-- =====================================================
-- AUDITORIA
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

CREATE INDEX IF NOT EXISTS idx_audit_empresa ON audit_data_access(empresa_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_data_access(timestamp);

-- =====================================================
-- VIEW DE STATUS
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

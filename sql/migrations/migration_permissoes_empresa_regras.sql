-- Migration: Adicionar permissões de regras de conciliação no sistema multi-empresa
-- Data: 2025-01-XX
-- Objetivo: Atualizar campo JSONB permissoes_empresa na tabela usuario_empresas

DO $$
DECLARE
    vinculo RECORD;
    permissoes_json TEXT;
    permissoes_array JSONB;
    nova_permissao TEXT;
    contador INTEGER := 0;
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'MIGRATION: Adicionar Permissões de Regras';
    RAISE NOTICE '================================================';
    
    -- Iterar por todos os vínculos usuario-empresa ativos
    FOR vinculo IN 
        SELECT usuario_id, empresa_id, permissoes_empresa
        FROM usuario_empresas
        WHERE ativo = TRUE
    LOOP
        RAISE NOTICE '';
        RAISE NOTICE 'Processando Usuário % - Empresa %', vinculo.usuario_id, vinculo.empresa_id;
        
        -- Converter permissoes_empresa para JSONB array
        IF vinculo.permissoes_empresa IS NULL THEN
            permissoes_array := '[]'::jsonb;
        ELSE
            permissoes_array := vinculo.permissoes_empresa;
        END IF;
        
        RAISE NOTICE '  Permissões atuais: % itens', jsonb_array_length(permissoes_array);
        
        -- Adicionar cada permissão se não existir
        FOREACH nova_permissao IN ARRAY ARRAY[
            'regras_conciliacao_view',
            'regras_conciliacao_create',
            'regras_conciliacao_edit',
            'regras_conciliacao_delete'
        ]
        LOOP
            -- Verificar se permissão já existe
            IF NOT permissoes_array ? nova_permissao THEN
                -- Adicionar permissão ao array
                permissoes_array := permissoes_array || jsonb_build_array(nova_permissao);
                RAISE NOTICE '    ✓ Adicionada: %', nova_permissao;
            ELSE
                RAISE NOTICE '    - Já existe: %', nova_permissao;
            END IF;
        END LOOP;
        
        -- Atualizar no banco
        UPDATE usuario_empresas
        SET permissoes_empresa = permissoes_array
        WHERE usuario_id = vinculo.usuario_id 
        AND empresa_id = vinculo.empresa_id;
        
        contador := contador + 1;
        RAISE NOTICE '  Total agora: % permissões', jsonb_array_length(permissoes_array);
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'CONCLUÍDO: % vínculo(s) atualizado(s)', contador;
    RAISE NOTICE '================================================';
END $$;

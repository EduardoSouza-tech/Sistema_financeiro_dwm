-- ================================================================================
-- 🧹 LIMPEZA DE LANÇAMENTOS DUPLICADOS [EXTRATO]
-- ================================================================================
-- Este script remove lançamentos duplicados importados do extrato OFX
-- Mantém apenas 1 registro de cada duplicata (o mais recente)
-- ================================================================================

-- 📊 ANÁLISE ANTES DA LIMPEZA
-- --------------------------------------------------------------------------------
SELECT 'ANÁLISE ANTES DA LIMPEZA' as etapa;
SELECT '========================' as separador;

-- Total de lançamentos
SELECT COUNT(*) as total_lancamentos FROM lancamentos;

-- Lançamentos com [EXTRATO]
SELECT COUNT(*) as total_com_extrato 
FROM lancamentos 
WHERE descricao LIKE '[EXTRATO]%';

-- Duplicatas por descrição + valor + data
SELECT 
    descricao,
    valor,
    data_vencimento,
    tipo,
    COUNT(*) as quantidade,
    MIN(id) as id_mais_antigo,
    MAX(id) as id_mais_recente
FROM lancamentos
WHERE descricao LIKE '[EXTRATO]%'
GROUP BY descricao, valor, data_vencimento, tipo
HAVING COUNT(*) > 1
ORDER BY quantidade DESC
LIMIT 20;

-- ================================================================================
-- ⚠️ BACKUP ANTES DE DELETAR
-- ================================================================================
-- Cria tabela de backup com os registros que serão deletados
-- --------------------------------------------------------------------------------

DROP TABLE IF EXISTS lancamentos_backup_duplicatas;

CREATE TABLE lancamentos_backup_duplicatas AS
SELECT l.*
FROM lancamentos l
WHERE l.descricao LIKE '[EXTRATO]%'
  AND l.id NOT IN (
    -- Mantém apenas o registro mais RECENTE de cada duplicata
    SELECT MAX(id) 
    FROM lancamentos
    WHERE descricao LIKE '[EXTRATO]%'
    GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
  );

-- Verifica quantos registros foram salvos no backup
SELECT COUNT(*) as registros_no_backup FROM lancamentos_backup_duplicatas;

-- ================================================================================
-- 🗑️ DELETAR DUPLICATAS
-- ================================================================================
-- Remove todos exceto o mais recente de cada grupo
-- --------------------------------------------------------------------------------

-- DESCOMENTE A LINHA ABAIXO PARA EXECUTAR A DELEÇÃO:
-- DELETE FROM lancamentos
-- WHERE descricao LIKE '[EXTRATO]%'
--   AND id NOT IN (
--     -- Mantém apenas o registro mais RECENTE de cada duplicata
--     SELECT MAX(id) 
--     FROM lancamentos
--     WHERE descricao LIKE '[EXTRATO]%'
--     GROUP BY descricao, valor, data_vencimento, tipo, empresa_id
--   );

-- ================================================================================
-- 📊 ANÁLISE APÓS A LIMPEZA
-- ================================================================================

-- Total de lançamentos restantes
SELECT COUNT(*) as total_lancamentos_apos FROM lancamentos;

-- Lançamentos com [EXTRATO] restantes
SELECT COUNT(*) as total_com_extrato_apos 
FROM lancamentos 
WHERE descricao LIKE '[EXTRATO]%';

-- Verificar se ainda há duplicatas
SELECT 
    descricao,
    valor,
    data_vencimento,
    tipo,
    COUNT(*) as quantidade
FROM lancamentos
WHERE descricao LIKE '[EXTRATO]%'
GROUP BY descricao, valor, data_vencimento, tipo
HAVING COUNT(*) > 1;

-- ================================================================================
-- 🎯 SALDO FINAL ESPERADO
-- ================================================================================
-- Verifica o saldo da conta bancária após limpeza
-- --------------------------------------------------------------------------------

SELECT 
    banco,
    agencia,
    conta,
    saldo_inicial,
    saldo_atual,
    FORMAT('R$ %s', saldo_atual) as saldo_formatado
FROM contas_bancarias
WHERE id = 6;  -- Sua conta SICREDI

-- ================================================================================
-- 📋 INSTRUÇÕES DE USO
-- ================================================================================
-- 
-- 1. Execute as queries de ANÁLISE primeiro (linhas 7-34)
--    - Anote quantos registros serão deletados
--    - Revise os 20 principais duplicatas
--
-- 2. Execute a criação do BACKUP (linhas 39-53)
--    - Verifica que o backup foi criado corretamente
--    - Anote quantos registros foram salvos
--
-- 3. DESCOMENTE e execute a query de DELEÇÃO (linhas 58-66)
--    - Remove as duplicatas mantendo apenas a mais recente
--
-- 4. Execute as queries de ANÁLISE APÓS (linhas 71-92)
--    - Confirme que não há mais duplicatas
--    - Verifique o novo saldo
--
-- 5. Se o saldo estiver CORRETO (-R$ 40.810,10):
--    - DROP TABLE lancamentos_backup_duplicatas; (opcional)
--
-- 6. Se algo der ERRADO:
--    - INSERT INTO lancamentos SELECT * FROM lancamentos_backup_duplicatas;
--    - (restaura os registros deletados)
--
-- ================================================================================

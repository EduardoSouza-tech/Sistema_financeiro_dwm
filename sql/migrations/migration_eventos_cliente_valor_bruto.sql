-- ================================================================================
-- MIGRATION: Adicionar cliente e valor_bruto_nf em eventos
-- ================================================================================
-- Data de Criação: 2026-08-05
-- Versão: 1.0
--
-- DESCRIÇÃO:
--   Adiciona o nome do cliente associado ao evento e o valor bruto da NF
--   (antes de deduções), complementando o valor líquido já existente.
--
-- ROLLBACK:
--   ALTER TABLE eventos DROP COLUMN IF EXISTS cliente;
--   ALTER TABLE eventos DROP COLUMN IF EXISTS valor_bruto_nf;
-- ================================================================================

ALTER TABLE eventos ADD COLUMN IF NOT EXISTS cliente VARCHAR(255);
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS valor_bruto_nf DECIMAL(15, 2);

COMMENT ON COLUMN eventos.cliente IS 'Nome do cliente associado ao evento';
COMMENT ON COLUMN eventos.valor_bruto_nf IS 'Valor bruto da NF, antes de deduções (complementa valor_liquido_nf)';

CREATE INDEX IF NOT EXISTS idx_eventos_cliente ON eventos(cliente);

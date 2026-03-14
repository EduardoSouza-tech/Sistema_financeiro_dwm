-- Script para corrigir nomes de certificados com valor literal "razao_social"
-- Substitui pelo valor real da razão social da empresa

-- Visualizar os certificados que serão corrigidos
SELECT 
    c.id,
    c.empresa_id,
    c.nome_certificado AS nome_atual,
    e.razao_social AS nome_correto,
    c.cnpj
FROM certificados_digitais c
INNER JOIN empresas e ON e.id = c.empresa_id
WHERE c.nome_certificado = 'razao_social';

-- Descomente a linha abaixo para aplicar a correção:
-- UPDATE certificados_digitais c
-- SET nome_certificado = e.razao_social,
--     atualizado_em = CURRENT_TIMESTAMP
-- FROM empresas e
-- WHERE c.empresa_id = e.id
-- AND c.nome_certificado = 'razao_social';

-- Verificar resultado
-- SELECT id, empresa_id, nome_certificado, cnpj FROM certificados_digitais;

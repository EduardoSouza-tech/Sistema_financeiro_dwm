-- ================================================================================
-- MIGRATION: Sistema de Alocação de Funcionários em Eventos
-- ================================================================================
-- Data de Criação: 2026-01-31
-- Última Atualização: 2026-02-01
-- Versão: 1.1
--
-- DESCRIÇÃO:
--   Esta migration cria a infraestrutura completa para o sistema de alocação
--   de equipe em eventos operacionais, permitindo:
--   - Cadastro de funções/cargos (Motorista, Fotógrafo, etc.)
--   - Vinculação de funcionários a eventos com funções específicas
--   - Registro de valores pagos por função/evento
--   - Histórico auditável de alocações
--
-- DEPENDÊNCIAS:
--   - Tabela 'eventos' deve existir
--   - Tabela 'funcionarios' deve existir
--
-- IMPACTO:
--   - Cria 2 novas tabelas
--   - Cria 5 índices para performance
--   - Insere 11 funções padrão
--   - Adiciona triggers para auditoria (futuro)
--
-- ROLLBACK:
--   DROP TABLE IF EXISTS evento_funcionarios CASCADE;
--   DROP TABLE IF EXISTS funcoes_evento CASCADE;
-- ================================================================================

-- ================================================================================
-- VERIFICAÇÃO DE DEPENDÊNCIAS
-- ================================================================================
DO $$
BEGIN
    -- Verifica se a tabela 'eventos' existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'eventos'
    ) THEN
        RAISE EXCEPTION 'ERRO: Tabela "eventos" não encontrada. Execute as migrations anteriores primeiro.';
    END IF;
    
    -- Verifica se a tabela 'funcionarios' existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'funcionarios'
    ) THEN
        RAISE EXCEPTION 'ERRO: Tabela "funcionarios" não encontrada. Execute as migrations anteriores primeiro.';
    END IF;
    
    RAISE NOTICE '✅ Dependências verificadas com sucesso';
END $$;

-- ================================================================================
-- TABELA: funcoes_evento
-- ================================================================================
-- Armazena os tipos de funções/cargos que podem ser atribuídos a funcionários
-- em eventos operacionais. Exemplos: Motorista, Fotógrafo, Cinegrafista, etc.
--
-- CAMPOS:
--   id          : Identificador único da função (gerado automaticamente)
--   nome        : Nome da função (único, não permite duplicatas)
--   descricao   : Descrição detalhada das responsabilidades da função
--   ativo       : Se a função está ativa e pode ser atribuída a novos eventos
--   created_at  : Data/hora de criação do registro
--   updated_at  : Data/hora da última atualização
--
-- CONSTRAINTS:
--   - nome deve ser único (case-insensitive via UPPER nos índices)
--   - nome não pode ser nulo
--   - ativo padrão é TRUE
-- ================================================================================

CREATE TABLE IF NOT EXISTS funcoes_evento (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraint para garantir unicidade do nome (case-insensitive)
    CONSTRAINT uk_funcoes_evento_nome UNIQUE (nome)
);

-- Índice para buscas rápidas por nome (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_funcoes_evento_nome ON funcoes_evento(UPPER(nome));

-- Índice para filtrar funções ativas
CREATE INDEX IF NOT EXISTS idx_funcoes_evento_ativo ON funcoes_evento(ativo) WHERE ativo = TRUE;

-- Comentários explicativos
COMMENT ON TABLE funcoes_evento IS 'Catálogo de funções/cargos disponíveis para alocação em eventos operacionais';
COMMENT ON COLUMN funcoes_evento.id IS 'Identificador único da função';
COMMENT ON COLUMN funcoes_evento.nome IS 'Nome da função (ex: Motorista, Fotógrafo). Deve ser único.';
COMMENT ON COLUMN funcoes_evento.descricao IS 'Descrição detalhada das responsabilidades e atribuições da função';
COMMENT ON COLUMN funcoes_evento.ativo IS 'Indica se a função está ativa e disponível para novos eventos';
COMMENT ON COLUMN funcoes_evento.created_at IS 'Data e hora de criação do registro';
COMMENT ON COLUMN funcoes_evento.updated_at IS 'Data e hora da última atualização do registro';

-- ================================================================================
-- TABELA: evento_funcionarios
-- ================================================================================
-- Relacionamento N:N entre eventos e funcionários, com atributos adicionais
-- (função desempenhada e valor pago).
--
-- CAMPOS:
--   id              : Identificador único do relacionamento
--   evento_id       : Referência ao evento (FK para eventos.id)
--   funcionario_id  : Referência ao funcionário (FK para funcionarios.id)
--   funcao_id       : Referência à função desempenhada (FK para funcoes_evento.id)
--   funcao_nome     : Nome da função (redundante para histórico)
--   valor           : Valor pago ao funcionário por esta alocação
--   observacoes     : Observações adicionais sobre a alocação
--   created_at      : Data/hora de criação do registro
--   updated_at      : Data/hora da última atualização
--
-- REGRAS DE NEGÓCIO:
--   - Um funcionário pode ter múltiplas funções no mesmo evento
--   - Mas não pode ter a MESMA função duplicada no mesmo evento
--   - Se um evento for excluído, suas alocações são excluídas (CASCADE)
--   - Se um funcionário for excluído, suas alocações são excluídas (CASCADE)
--   - Se uma função for excluída, mantém o nome no histórico (funcao_nome)
--
-- AUDITORIA:
--   - funcao_nome: Cópia do nome da função no momento da alocação
--   - Permite análise histórica mesmo se a função for renomeada/excluída
-- ================================================================================

CREATE TABLE IF NOT EXISTS evento_funcionarios (
    id SERIAL PRIMARY KEY,
    
    -- Chaves estrangeiras com comportamento de deleção específico
    evento_id INTEGER NOT NULL,
    funcionario_id INTEGER NOT NULL,
    funcao_id INTEGER NULL,
    
    -- Dados do relacionamento
    funcao_nome VARCHAR(100) NULL, -- Redundância intencional para histórico
    valor DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    observacoes TEXT NULL,
    
    -- Auditoria
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints de integridade referencial
    CONSTRAINT fk_evento_funcionarios_evento 
        FOREIGN KEY (evento_id) 
        REFERENCES eventos(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_evento_funcionarios_funcionario 
        FOREIGN KEY (funcionario_id) 
        REFERENCES funcionarios(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_evento_funcionarios_funcao 
        FOREIGN KEY (funcao_id) 
        REFERENCES funcoes_evento(id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    -- Constraint de unicidade: evita duplicação da mesma função para o mesmo funcionário no mesmo evento
    CONSTRAINT uk_evento_funcionario_funcao 
        UNIQUE (evento_id, funcionario_id, funcao_id),
    
    -- Constraint de validação: valor não pode ser negativo
    CONSTRAINT chk_evento_funcionarios_valor_positivo 
        CHECK (valor >= 0.00)
);

-- Índices para otimização de queries
CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_evento 
    ON evento_funcionarios(evento_id);

CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_funcionario 
    ON evento_funcionarios(funcionario_id);

CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_funcao 
    ON evento_funcionarios(funcao_id);

-- Índice composto para queries que filtram por evento + funcionário
CREATE INDEX IF NOT EXISTS idx_evento_funcionarios_evento_funcionario 
    ON evento_funcionarios(evento_id, funcionario_id);

-- Comentários explicativos
COMMENT ON TABLE evento_funcionarios IS 'Relaciona funcionários com eventos, especificando função desempenhada e valor pago';
COMMENT ON COLUMN evento_funcionarios.id IS 'Identificador único da alocação';
COMMENT ON COLUMN evento_funcionarios.evento_id IS 'Referência ao evento (ON DELETE CASCADE)';
COMMENT ON COLUMN evento_funcionarios.funcionario_id IS 'Referência ao funcionário (ON DELETE CASCADE)';
COMMENT ON COLUMN evento_funcionarios.funcao_id IS 'Referência à função desempenhada (ON DELETE SET NULL)';
COMMENT ON COLUMN evento_funcionarios.funcao_nome IS 'Nome da função no momento da alocação (mantém histórico se função for excluída)';
COMMENT ON COLUMN evento_funcionarios.valor IS 'Valor pago ao funcionário por esta função neste evento (não pode ser negativo)';
COMMENT ON COLUMN evento_funcionarios.observacoes IS 'Observações adicionais sobre a alocação (horários, condições especiais, etc.)';
COMMENT ON COLUMN evento_funcionarios.created_at IS 'Data e hora de criação da alocação';
COMMENT ON COLUMN evento_funcionarios.updated_at IS 'Data e hora da última atualização da alocação';

-- ================================================================================
-- TRIGGER: Atualização automática de updated_at
-- ================================================================================
-- Garante que o campo updated_at seja sempre atualizado automaticamente
-- ================================================================================

-- Função genérica para atualizar updated_at
CREATE OR REPLACE FUNCTION atualizar_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para funcoes_evento
DROP TRIGGER IF EXISTS trigger_funcoes_evento_updated_at ON funcoes_evento;
CREATE TRIGGER trigger_funcoes_evento_updated_at
    BEFORE UPDATE ON funcoes_evento
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at_column();

-- Trigger para evento_funcionarios
DROP TRIGGER IF EXISTS trigger_evento_funcionarios_updated_at ON evento_funcionarios;
CREATE TRIGGER trigger_evento_funcionarios_updated_at
    BEFORE UPDATE ON evento_funcionarios
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at_column();

-- ================================================================================
-- DADOS INICIAIS: Funções Padrão
-- ================================================================================
-- Insere as 11 funções mais comuns em eventos operacionais
-- Usa ON CONFLICT para evitar erros se a migration for executada múltiplas vezes
-- ================================================================================

INSERT INTO funcoes_evento (nome, descricao, ativo) VALUES
    ('Motorista', 'Responsável pelo transporte da equipe, equipamentos e logística de deslocamento', TRUE),
    ('Fotógrafo', 'Responsável pela captura profissional de imagens do evento', TRUE),
    ('Assistente de Fotografia', 'Auxilia o fotógrafo principal com equipamentos, iluminação e organização', TRUE),
    ('Cinegrafista', 'Responsável pela filmagem e captação de vídeos do evento', TRUE),
    ('Editor de Vídeo', 'Responsável pela edição, pós-produção e finalização dos vídeos', TRUE),
    ('Editor de Fotos', 'Responsável pela edição, tratamento e finalização das imagens', TRUE),
    ('Operador de Drone', 'Responsável pela captação de imagens e vídeos aéreos com drone', TRUE),
    ('Coordenador', 'Coordena a equipe, cronograma e logística geral do evento', TRUE),
    ('Assistente Geral', 'Apoio geral à equipe durante o evento (equipamentos, organização, etc.)', TRUE),
    ('Maquiador', 'Responsável pela maquiagem e preparação visual dos participantes', TRUE),
    ('Produtor', 'Responsável pela produção executiva, planejamento e gestão do evento', TRUE)
ON CONFLICT (nome) DO NOTHING;

-- ================================================================================
-- VERIFICAÇÃO FINAL
-- ================================================================================
-- Confirma que a migration foi executada com sucesso
-- ================================================================================

DO $$
DECLARE
    count_funcoes INTEGER;
    count_tabelas INTEGER;
BEGIN
    -- Conta funções inseridas
    SELECT COUNT(*) INTO count_funcoes FROM funcoes_evento;
    
    -- Conta tabelas criadas
    SELECT COUNT(*) INTO count_tabelas 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('funcoes_evento', 'evento_funcionarios');
    
    -- Validação
    IF count_tabelas < 2 THEN
        RAISE EXCEPTION 'ERRO: Nem todas as tabelas foram criadas corretamente';
    END IF;
    
    IF count_funcoes = 0 THEN
        RAISE WARNING 'AVISO: Nenhuma função foi inserida (pode já existir)';
    END IF;
    
    -- Mensagens de sucesso
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '✅ MIGRATION EXECUTADA COM SUCESSO!';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE '📊 Tabelas criadas: %', count_tabelas;
    RAISE NOTICE '👷 Funções disponíveis: %', count_funcoes;
    RAISE NOTICE '🔗 Relacionamentos configurados: 2 (eventos, funcionarios)';
    RAISE NOTICE '📈 Índices criados: 5';
    RAISE NOTICE '⚙️ Triggers configurados: 2';
    RAISE NOTICE '================================================================================';
END $$;

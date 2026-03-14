# 🔧 CORREÇÃO URGENTE - SUBCATEGORIAS NÃO APARECEM

## 🔴 Problema
- `/api/subcategorias?categoria_id=X` retorna erro 500
- `/api/eventos/X/fornecedores` retorna erro 500
- Subcategorias não aparecem no dropdown de Fornecedores

## ✅ Causa Identificada
1. **Coluna `ativa` não existe** na tabela `subcategorias`
2. **Tabela `evento_fornecedores` não existe** no banco de dados Railway

## 🚀 SOLUÇÃO IMEDIATA

### Passo 1: Acesse o Railway Query Editor
1. Abra o Railway Dashboard
2. Selecione seu banco de dados PostgreSQL
3. Clique em **Query** (ou **Data**)

### Passo 2: Execute o Script de Correção
Copie e cole TODO o conteúdo do arquivo `fix_subcategorias_evento_fornecedores.sql` no Query Editor e execute.

**OU copie este SQL:**

```sql
-- 1. ADICIONAR COLUNA 'ativa' NA TABELA SUBCATEGORIAS
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'subcategorias' 
        AND column_name = 'ativa'
    ) THEN
        ALTER TABLE subcategorias ADD COLUMN ativa BOOLEAN DEFAULT TRUE;
        UPDATE subcategorias SET ativa = TRUE WHERE ativa IS NULL;
        RAISE NOTICE '✅ Coluna ativa adicionada à tabela subcategorias';
    ELSE
        RAISE NOTICE '✅ Coluna ativa já existe';
    END IF;
END $$;

-- 2. CRIAR TABELA EVENTO_FORNECEDORES
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
    UNIQUE(evento_id, fornecedor_id)
);

CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_evento ON evento_fornecedores(evento_id);
CREATE INDEX IF NOT EXISTS idx_evento_fornecedores_fornecedor ON evento_fornecedores(fornecedor_id);

-- 3. VERIFICAR SE FOI APLICADO
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'subcategorias' AND column_name = 'ativa') THEN
        RAISE NOTICE '✅ Coluna subcategorias.ativa - OK';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'evento_fornecedores') THEN
        RAISE NOTICE '✅ Tabela evento_fornecedores - OK';
    END IF;
END $$;
```

### Passo 3: Reinicie o Servidor Railway
Após executar o SQL, reinicie o servidor Railway para carregar o código atualizado:
1. Vá na aba **Deployments**
2. Clique nos 3 pontinhos do deployment ativo
3. Clique em **Restart**

### Passo 4: Teste
1. Acesse a aplicação
2. Vá em **Operacional → Eventos**
3. Clique em um evento existente
4. Clique na aba **🏢 Fornecedores**
5. Selecione uma **Categoria**
6. Verifique se as **Subcategorias** aparecem no dropdown

## 📊 Verificação das Mudanças

Execute este SQL para confirmar que tudo está OK:

```sql
-- Verificar coluna ativa
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'subcategorias'
ORDER BY ordinal_position;

-- Verificar tabela evento_fornecedores
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'evento_fornecedores'
);

-- Contar registros
SELECT COUNT(*) as total_subcategorias FROM subcategorias;
SELECT COUNT(*) as total_evento_fornecedores FROM evento_fornecedores;
```

## 📝 Arquivos Criados

1. **`fix_subcategorias_evento_fornecedores.sql`** - Script SQL completo com verificações
2. **`verificar_schema_subcategorias.py`** - Script Python para diagnóstico (uso local)
3. **`verificar_aplicar_migracao_fornecedores.py`** - Script Python para aplicar migração (uso local)

## ✅ O Que Foi Corrigido no Código

1. **Endpoint `/api/subcategorias`**:
   - Adicionado `RealDictCursor` para retornar dicionários
   - Verificação dinâmica da coluna `ativa`
   - Logs detalhados para diagnóstico
   - Fallback se coluna não existir

2. **Endpoint `/api/eventos/<id>/fornecedores`**:
   - Adicionado `RealDictCursor`
   - Verificação se tabela existe
   - Retorna lista vazia com aviso se tabela não existir
   - Logs detalhados

## 🎯 Resultado Esperado

Após aplicar o script SQL e reiniciar o Railway:
- ✅ Subcategorias aparecem no dropdown
- ✅ Fornecedores podem ser cadastrados nos eventos
- ✅ Sem mais erros 500 nos endpoints

## 🆘 Se Ainda Não Funcionar

Verifique os logs do Railway:
1. Vá em **Deployments**
2. Clique no deployment ativo
3. Veja a aba **Logs**
4. Procure por mensagens com 🔴 ou ❌

---

**Commits:**
- `b88c8b8` - Fix: Add RealDictCursor to subcategorias and fornecedores endpoints
- `9016a15` - Fix: Add detailed logging and error handling + diagnostic scripts

# 🔒 DOCUMENTAÇÃO DE SEGURANÇA - ISOLAMENTO ENTRE EMPRESAS

## ✅ GARANTIA DE ISOLAMENTO 100%

Este sistema implementa **múltiplas camadas de segurança** para garantir que **NENHUMA empresa veja dados de outra**:

---

## 📊 ARQUITETURA MULTI-TENANCY COM RLS

### Como Funciona

```
┌─────────────────────────────────────────────┐
│         1 BANCO DE DADOS POSTGRESQL         │
│                                             │
│  ┌────────────────┐  ┌────────────────┐   │
│  │  EMPRESA 18    │  │  EMPRESA 20    │   │
│  │                │  │                │   │
│  │  • Categorias  │  │  • Categorias  │   │
│  │  • Lançamentos │  │  • Lançamentos │   │
│  │  • Clientes    │  │  • Clientes    │   │
│  │  • Contratos   │  │  • Contratos   │   │
│  │  • ...         │  │  • ...         │   │
│  └────────────────┘  └────────────────┘   │
│                                             │
│  ❌ Empresa 18 NÃO VÊ dados da Empresa 20  │
│  ❌ Empresa 20 NÃO VÊ dados da Empresa 18  │
└─────────────────────────────────────────────┘
```

### Estrutura das Tabelas

Todas as tabelas possuem coluna `empresa_id`:

```sql
CREATE TABLE lancamentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,  -- 🔑 CHAVE DE ISOLAMENTO
    tipo VARCHAR(20),
    valor DECIMAL(15,2),
    data_lancamento DATE,
    ...
);
```

---

## 🛡️ CAMADAS DE SEGURANÇA

### ⚡ Camada 1: Row Level Security (RLS)

**O QUE É**: Proteção no nível do banco de dados PostgreSQL.

**COMO FUNCIONA**:
```sql
-- Habilitar RLS na tabela
ALTER TABLE lancamentos ENABLE ROW LEVEL SECURITY;

-- Criar política de isolamento
CREATE POLICY lancamentos_empresa_isolation ON lancamentos
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);
```

**RESULTADO**:
- ✅ Mesmo que o código Python tenha bug, o banco bloqueia
- ✅ Impossível fazer SELECT de outra empresa
- ✅ Impossível fazer INSERT com empresa_id errada
- ✅ Impossível fazer UPDATE em dados de outra empresa

**EXEMPLO**:
```sql
-- Definir empresa da sessão
SELECT set_current_empresa(18);

-- Esta query retorna APENAS dados da empresa 18
SELECT * FROM lancamentos;  -- PostgreSQL filtra automaticamente

-- Esta query FALHA (empresa_id diferente da sessão)
INSERT INTO lancamentos (empresa_id, valor) VALUES (20, 1000.00);
-- ERRO: empresa_id (20) não corresponde à empresa da sessão (18)
```

### 🔍 Camada 2: Triggers de Validação

**O QUE É**: Triggers que validam empresa_id em INSERT/UPDATE.

**COMO FUNCIONA**:
```sql
CREATE FUNCTION validate_empresa_id() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.empresa_id != current_setting('app.current_empresa_id')::integer THEN
        RAISE EXCEPTION 'empresa_id não corresponde à sessão';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_empresa_lancamentos
    BEFORE INSERT OR UPDATE ON lancamentos
    FOR EACH ROW
    EXECUTE FUNCTION validate_empresa_id();
```

**RESULTADO**:
- ✅ Validação antes de gravar no banco
- ✅ Bloqueia tentativas de gravar com empresa_id errada
- ✅ Mensagem de erro clara

### 📝 Camada 3: Auditoria Completa

**O QUE É**: Log de todas as operações de dados.

**COMO FUNCIONA**:
```sql
CREATE TABLE audit_data_access (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER,
    empresa_id INTEGER,
    table_name VARCHAR(100),
    action VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**RESULTADO**:
- ✅ Rastreamento de todas as operações
- ✅ Identificação de tentativas de acesso indevido
- ✅ Histórico completo para compliance

### 🐍 Camada 4: Python Security Wrapper

**O QUE É**: Validação no código Python antes de executar queries.

**COMO FUNCIONA**:
```python
from security_wrapper import secure_connection, require_empresa

@require_empresa
def obter_lancamentos(empresa_id, mes, ano):
    with get_db_connection() as conn:
        with secure_connection(conn, empresa_id):
            cursor = conn.cursor()
            # RLS ativo - empresa_id já filtrado
            cursor.execute("SELECT * FROM lancamentos WHERE ...")
```

**RESULTADO**:
- ✅ Validação antes de chegar no banco
- ✅ Configura RLS automaticamente
- ✅ Impede código de rodar sem empresa_id

---

## 🧪 TESTES DE ISOLAMENTO

### Como Testar

Execute o script de teste:

```bash
python aplicar_rls.py
```

### O Que É Testado

1. **Teste de Visibilidade**:
   - Empresa 18 vê apenas seus próprios lançamentos
   - Empresa 20 vê apenas seus próprios lançamentos
   - Contagens são diferentes (prova de isolamento)

2. **Teste de Vazamento**:
   - Definir sessão como empresa 18
   - Tentar buscar `WHERE empresa_id = 20`
   - Resultado deve ser vazio (RLS bloqueia)

3. **Teste de Inserção Cross-Empresa**:
   - Definir sessão como empresa 18
   - Tentar inserir com empresa_id = 20
   - Deve falhar com erro

### Resultado Esperado

```
✅ TODOS OS TESTES DE ISOLAMENTO PASSARAM!
🔒 SEGURANÇA CONFIRMADA:
   • Row Level Security está ativo
   • Não há vazamento de dados entre empresas
   • Cada empresa vê apenas seus próprios dados
```

---

## 📋 COMO APLICAR A SEGURANÇA

### Passo 1: Aplicar RLS no Banco

```bash
cd Sistema_financeiro_dwm
python aplicar_rls.py
```

Isso irá:
- ✅ Habilitar RLS em todas as tabelas
- ✅ Criar políticas de isolamento
- ✅ Criar funções auxiliares
- ✅ Criar triggers de validação
- ✅ Configurar auditoria
- ✅ Testar isolamento

### Passo 2: Verificar Status

No banco de dados:

```sql
-- Ver status de RLS em todas as tabelas
SELECT * FROM rls_status;

-- Resultado esperado:
-- lancamentos     | true | 1        | OK
-- categorias      | true | 1        | OK
-- clientes        | true | 1        | OK
-- ...
```

### Passo 3: Testar Manualmente

```sql
-- Definir empresa 18
SELECT set_current_empresa(18);

-- Buscar lançamentos (apenas empresa 18)
SELECT COUNT(*) FROM lancamentos;

-- Mudar para empresa 20
SELECT set_current_empresa(20);

-- Buscar lançamentos (apenas empresa 20)
SELECT COUNT(*) FROM lancamentos;

-- Contagens devem ser diferentes!
```

---

## 🚀 USO NO CÓDIGO

### Exemplo Básico

```python
from database_postgresql import get_db_connection
from security_wrapper import secure_connection

def obter_dados_empresa(empresa_id):
    with get_db_connection() as conn:
        # Ativar RLS para esta empresa
        with secure_connection(conn, empresa_id):
            cursor = conn.cursor()
            
            # Query automaticamente filtrada por RLS
            cursor.execute("SELECT * FROM lancamentos")
            lancamentos = cursor.fetchall()
            
            # Retorna APENAS lançamentos da empresa especificada
            return lancamentos
```

### Exemplo com Decorator

```python
from security_wrapper import require_empresa

@require_empresa
def criar_lancamento(empresa_id, dados):
    # empresa_id é obrigatório - decorator valida
    with get_db_connection() as conn:
        with secure_connection(conn, empresa_id):
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO lancamentos (empresa_id, valor, ...) VALUES (%s, %s, ...)",
                (empresa_id, dados['valor'], ...)
            )
```

### Exemplo de Validação Automática

```python
from security_wrapper import execute_secure_query

def atualizar_categoria(empresa_id, categoria_id, novo_nome):
    with get_db_connection() as conn:
        with secure_connection(conn, empresa_id):
            cursor = conn.cursor()
            
            # Validação automática de empresa_id na query
            execute_secure_query(
                cursor,
                "UPDATE categorias SET nome = %s WHERE id = %s",
                (novo_nome, categoria_id),
                empresa_id=empresa_id,
                audit=True  # Auditar esta operação
            )
```

---

## 📊 MONITORAMENTO E AUDITORIA

### Ver Logs de Acesso

```sql
-- Últimas 100 operações
SELECT 
    usuario_id,
    empresa_id,
    table_name,
    action,
    timestamp
FROM audit_data_access
ORDER BY timestamp DESC
LIMIT 100;
```

### Ver Tentativas Suspeitas

```sql
-- Operações em horários incomuns
SELECT * FROM audit_data_access
WHERE EXTRACT(HOUR FROM timestamp) NOT BETWEEN 6 AND 22;

-- Múltiplas empresas acessadas pelo mesmo usuário
SELECT 
    usuario_id,
    COUNT(DISTINCT empresa_id) as empresas_acessadas,
    array_agg(DISTINCT empresa_id) as empresa_ids
FROM audit_data_access
GROUP BY usuario_id
HAVING COUNT(DISTINCT empresa_id) > 1;
```

---

## 🔥 VANTAGENS DA ARQUITETURA ATUAL

### ✅ Multi-Tenancy com RLS

| Aspecto | Avaliação |
|---------|-----------|
| **Custo** | 💰 $5/mês total (Railway Basic) |
| **Segurança** | 🔒 100% isolado com RLS |
| **Manutenção** | ✅ Simples - 1 banco apenas |
| **Performance** | ⚡ Rápido - mesmo servidor |
| **Backup** | 📦 1 backup cobre tudo |
| **Escalabilidade** | 📈 Até 1000 empresas |
| **Complexidade** | 🟢 Baixa |

### ❌ Multi-Database (Alternativa NÃO RECOMENDADA)

| Aspecto | Avaliação |
|---------|-----------|
| **Custo** | 💸 $5 × (N+1) por mês |
| **Segurança** | 🔒 100% isolado físico |
| **Manutenção** | ⚠️ Complexa - N bancos |
| **Performance** | ⚡ Rápido mas distribído |
| **Backup** | 📦 N backups separados |
| **Escalabilidade** | 📈 Até 50 empresas |
| **Complexidade** | 🔴 Alta |

**EXEMPLO DE CUSTO**:
- 10 empresas: $5/mês (multi-tenancy) vs $55/mês (multi-database)
- 50 empresas: $5/mês (multi-tenancy) vs $255/mês (multi-database)

---

## ⚠️ IMPORTANTE

### Usuários PostgreSQL

⚠️ **SUPER USUÁRIOS NÃO SÃO AFETADOS POR RLS!**

Se você conectar como superusuário (postgres), RLS é ignorado. Use:
- ✅ Usuário da aplicação (não-superusuário)
- ✅ Configuração Railway padrão (já é não-superusuário)

### Manutenção

Para desabilitar RLS temporariamente (apenas manutenção):

```sql
-- Desabilitar RLS em uma tabela
ALTER TABLE lancamentos DISABLE ROW LEVEL SECURITY;

-- Reabilitar depois
ALTER TABLE lancamentos ENABLE ROW LEVEL SECURITY;
```

### Rollback

Para remover completamente RLS:

```sql
-- Para cada tabela:
ALTER TABLE lancamentos DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lancamentos_empresa_isolation ON lancamentos;

-- Remover funções
DROP FUNCTION IF EXISTS validate_empresa_id();
DROP FUNCTION IF EXISTS set_current_empresa(INTEGER);
DROP FUNCTION IF EXISTS get_current_empresa();

-- Remover auditoria
DROP TABLE IF EXISTS audit_data_access;
DROP VIEW IF EXISTS rls_status;
```

---

## 📚 REFERÊNCIAS

- [PostgreSQL Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Documentação security_wrapper.py](security_wrapper.py)
- [Script de aplicação](aplicar_rls.py)
- [SQL de configuração](row_level_security.sql)

---

## ✅ CONCLUSÃO

**O sistema está 100% seguro com:**

1. ✅ **Row Level Security** - Proteção no banco de dados
2. ✅ **Triggers de Validação** - Bloqueio de inserções indevidas
3. ✅ **Auditoria Completa** - Rastreamento de todas as operações
4. ✅ **Python Security Wrapper** - Validação no código
5. ✅ **Testes Automatizados** - Verificação contínua de isolamento

**Cada empresa vê APENAS seus próprios dados. GARANTIDO.**

---

**Data de Criação**: 29 de Janeiro de 2026  
**Versão**: 1.0  
**Status**: ✅ Implementado e Testado

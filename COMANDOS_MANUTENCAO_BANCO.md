# 🔧 COMANDOS DE MANUTENÇÃO - BANCO DE DADOS RAILWAY

## 📋 CONEXÃO DIRETA COM O BANCO

### 1️⃣ Obter Credenciais do Railway

1. Acesse https://railway.app
2. Abra seu projeto
3. Clique no plugin **PostgreSQL**
4. Clique em **"Connect"**
5. Copie as credenciais

**Exemplo das credenciais:**
```
Connection URL:
postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway

Raw psql command:
PGPASSWORD=JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT psql -h centerbeam.proxy.rlwy.net -U postgres -p 12659 -d railway

Railway CLI:
railway connect Postgres
```

---

## 🐍 EXECUTAR SCRIPTS PYTHON NO BANCO RAILWAY

### Aplicar Row Level Security (RLS)

```powershell
# Comando completo (substitua a URL pelas suas credenciais)
cd "Sistema_financeiro_dwm"
C:\Users\Nasci\AppData\Local\Programs\Python\Python312\python.exe aplicar_rls_direto.py "postgresql://postgres:SENHA@host.railway.app:PORTA/railway"
```

**Exemplo real usado:**
```powershell
cd "C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\Sistema_financeiro_dwm"

echo s | C:\Users\Nasci\AppData\Local\Programs\Python\Python312\python.exe aplicar_rls_direto.py "postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway"
```

### Outros Scripts Python

```powershell
# Template genérico
python NOME_DO_SCRIPT.py "postgresql://postgres:SENHA@host:porta/railway"

# Exemplo: Executar migração
python migration_script.py "postgresql://postgres:SENHA@host:porta/railway"

# Exemplo: Verificar dados
python verificar_dados.py "postgresql://postgres:SENHA@host:porta/railway"
```

---

## 🗄️ COMANDOS SQL DIRETOS

### Via psql (PostgreSQL CLI)

```bash
# Conectar ao banco
PGPASSWORD=JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT psql -h centerbeam.proxy.rlwy.net -U postgres -p 12659 -d railway

# Dentro do psql, executar comandos:
\dt                           # Listar todas as tabelas
\d+ nome_tabela              # Descrever estrutura da tabela
SELECT * FROM rls_status;    # Ver status de RLS
\q                           # Sair
```

### Via Railway CLI

```bash
# Instalar Railway CLI (apenas uma vez)
npm i -g @railway/cli

# Login
railway login

# Listar projetos
railway list

# Conectar ao projeto
railway link

# Conectar ao PostgreSQL
railway connect Postgres

# Executar comando SQL
railway run psql -c "SELECT * FROM rls_status;"
```

### Via Python (psycopg2)

```python
import psycopg2

# Conectar
conn = psycopg2.connect("postgresql://postgres:SENHA@host:porta/railway")
cursor = conn.cursor()

# Executar query
cursor.execute("SELECT * FROM rls_status")
results = cursor.fetchall()

for row in results:
    print(row)

cursor.close()
conn.close()
```

---

## 🔒 COMANDOS DE SEGURANÇA (RLS)

### Verificar Status do RLS

```sql
-- Ver quais tabelas têm RLS ativo
SELECT * FROM rls_status ORDER BY tablename;
```

### Habilitar RLS em Nova Tabela

```sql
-- Template
ALTER TABLE nome_tabela ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS nome_tabela_empresa_isolation ON nome_tabela;
CREATE POLICY nome_tabela_empresa_isolation ON nome_tabela
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);
```

**Exemplo prático:**
```sql
-- Habilitar RLS na tabela 'contas_bancarias'
ALTER TABLE contas_bancarias ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contas_empresa_isolation ON contas_bancarias;
CREATE POLICY contas_empresa_isolation ON contas_bancarias
    USING (empresa_id = current_setting('app.current_empresa_id')::integer);
```

### Desabilitar RLS (Apenas para Manutenção)

```sql
-- Desabilitar temporariamente
ALTER TABLE nome_tabela DISABLE ROW LEVEL SECURITY;

-- Reabilitar depois
ALTER TABLE nome_tabela ENABLE ROW LEVEL SECURITY;
```

### Testar Isolamento Entre Empresas

```sql
-- Definir empresa 1
SELECT set_current_empresa(1);
SELECT COUNT(*) FROM lancamentos;

-- Definir empresa 18
SELECT set_current_empresa(18);
SELECT COUNT(*) FROM lancamentos;

-- Tentar acessar outra empresa (deve retornar 0)
SELECT set_current_empresa(1);
SELECT COUNT(*) FROM lancamentos WHERE empresa_id = 18;
```

---

## 📊 COMANDOS DE DIAGNÓSTICO

### Ver Todas as Tabelas

```sql
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

### Ver Estrutura de Tabela

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'nome_tabela'
ORDER BY ordinal_position;
```

### Ver Índices

```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'nome_tabela';
```

### Ver Políticas RLS Ativas

```sql
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

### Verificar Conexões Ativas

```sql
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change
FROM pg_stat_activity
WHERE datname = 'railway'
ORDER BY query_start DESC;
```

### Ver Tamanho das Tabelas

```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;
```

---

## 🔍 COMANDOS DE AUDITORIA

### Ver Últimos Acessos

```sql
SELECT 
    usuario_id,
    empresa_id,
    table_name,
    action,
    timestamp
FROM audit_data_access
ORDER BY timestamp DESC
LIMIT 50;
```

### Ver Acessos de uma Empresa Específica

```sql
SELECT 
    table_name,
    action,
    COUNT(*) as total,
    MAX(timestamp) as ultimo_acesso
FROM audit_data_access
WHERE empresa_id = 18
GROUP BY table_name, action
ORDER BY ultimo_acesso DESC;
```

### Ver Tentativas Suspeitas

```sql
-- Operações em horários incomuns (fora do horário comercial)
SELECT * 
FROM audit_data_access
WHERE EXTRACT(HOUR FROM timestamp) NOT BETWEEN 6 AND 22
ORDER BY timestamp DESC;
```

---

## 🗂️ COMANDOS DE BACKUP

### Backup Via psql

```bash
# Backup completo
PGPASSWORD=senha pg_dump -h host -U postgres -p porta -d railway > backup_$(date +%Y%m%d).sql

# Backup apenas estrutura
PGPASSWORD=senha pg_dump -h host -U postgres -p porta -d railway --schema-only > schema_backup.sql

# Backup apenas dados
PGPASSWORD=senha pg_dump -h host -U postgres -p porta -d railway --data-only > data_backup.sql

# Backup de uma tabela específica
PGPASSWORD=senha pg_dump -h host -U postgres -p porta -d railway -t lancamentos > lancamentos_backup.sql
```

### Restaurar Backup

```bash
# Restaurar backup completo
PGPASSWORD=senha psql -h host -U postgres -p porta -d railway < backup_20260130.sql

# Restaurar tabela específica
PGPASSWORD=senha psql -h host -U postgres -p porta -d railway < lancamentos_backup.sql
```

---

## 🛠️ COMANDOS DE MANUTENÇÃO

### Reindexar Tabelas

```sql
-- Reindexar tabela específica
REINDEX TABLE lancamentos;

-- Reindexar todas as tabelas
REINDEX DATABASE railway;
```

### Atualizar Estatísticas

```sql
-- Atualizar estatísticas de uma tabela
ANALYZE lancamentos;

-- Atualizar estatísticas de todas as tabelas
ANALYZE;
```

### Vacuum (Limpeza)

```sql
-- Vacuum básico
VACUUM lancamentos;

-- Vacuum completo (mais lento mas mais eficaz)
VACUUM FULL lancamentos;

-- Vacuum com análise
VACUUM ANALYZE lancamentos;
```

### Ver Consultas Lentas

```sql
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## 📝 SCRIPTS ÚTEIS DE MANUTENÇÃO

### Script 1: Verificar Integridade dos Dados

```python
# verificar_integridade.py
import psycopg2
import sys

def verificar_integridade(database_url):
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Verificar lançamentos sem empresa_id
    cursor.execute("SELECT COUNT(*) FROM lancamentos WHERE empresa_id IS NULL")
    sem_empresa = cursor.fetchone()[0]
    print(f"Lançamentos sem empresa_id: {sem_empresa}")
    
    # Verificar clientes sem empresa_id
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE empresa_id IS NULL")
    sem_empresa = cursor.fetchone()[0]
    print(f"Clientes sem empresa_id: {sem_empresa}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    verificar_integridade(sys.argv[1])
```

**Uso:**
```powershell
python verificar_integridade.py "postgresql://postgres:senha@host:porta/railway"
```

### Script 2: Adicionar RLS em Tabela Nova

```python
# adicionar_rls_tabela.py
import psycopg2
import sys

def adicionar_rls(database_url, table_name):
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    sql = f"""
    ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS {table_name}_empresa_isolation ON {table_name};
    CREATE POLICY {table_name}_empresa_isolation ON {table_name}
        USING (empresa_id = current_setting('app.current_empresa_id')::integer);
    """
    
    cursor.execute(sql)
    conn.commit()
    print(f"✅ RLS aplicado em {table_name}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    adicionar_rls(sys.argv[1], sys.argv[2])
```

**Uso:**
```powershell
python adicionar_rls_tabela.py "postgresql://postgres:senha@host:porta/railway" "nome_tabela"
```

---

## ⚠️ COMANDOS PERIGOSOS (USE COM CUIDADO)

### Deletar Todos os Dados de uma Tabela

```sql
-- ⚠️ CUIDADO! Isso deleta TUDO
TRUNCATE TABLE nome_tabela CASCADE;
```

### Dropar Tabela

```sql
-- ⚠️ CUIDADO! Isso remove a tabela completamente
DROP TABLE IF EXISTS nome_tabela CASCADE;
```

### Resetar Sequências

```sql
-- Resetar ID de uma tabela
ALTER SEQUENCE nome_tabela_id_seq RESTART WITH 1;
```

---

## 🎯 CHECKLIST DE MANUTENÇÃO REGULAR

### Semanal
- [ ] Verificar logs de auditoria
- [ ] Verificar tamanho das tabelas
- [ ] Verificar consultas lentas

### Mensal
- [ ] Executar VACUUM ANALYZE em todas as tabelas
- [ ] Backup completo do banco
- [ ] Verificar índices não utilizados
- [ ] Revisar políticas RLS

### Semestral
- [ ] VACUUM FULL em tabelas grandes
- [ ] Reorganizar índices
- [ ] Limpar dados antigos de auditoria

---

## 📚 REFERÊNCIAS RÁPIDAS

### Atalhos psql

```
\dt          # Listar tabelas
\dt+         # Listar tabelas com detalhes
\d tabela    # Descrever tabela
\di          # Listar índices
\df          # Listar funções
\dv          # Listar views
\du          # Listar usuários
\l           # Listar databases
\q           # Sair
\?           # Ajuda
```

### Variáveis de Ambiente Úteis

```powershell
# Definir DATABASE_URL temporariamente
$env:DATABASE_URL="postgresql://postgres:senha@host:porta/railway"

# Verificar se está definida
echo $env:DATABASE_URL

# Limpar
$env:DATABASE_URL=""
```

---

## 🔐 SEGURANÇA

### ⚠️ NUNCA COMMITE CREDENCIAIS!

```bash
# Adicionar ao .gitignore
echo ".env" >> .gitignore
echo "*.sql.backup" >> .gitignore
echo "*_credentials.txt" >> .gitignore
```

### Usar Variáveis de Ambiente

```python
import os

# Ler da variável de ambiente
DATABASE_URL = os.getenv('DATABASE_URL')

# Ou de arquivo .env
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
```

---

## 📞 CONTATOS E RECURSOS

- **Railway Dashboard**: https://railway.app
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Railway Docs**: https://docs.railway.app/

---

**Última Atualização**: 30 de Janeiro de 2026  
**Versão**: 1.0  
**Banco**: PostgreSQL 15+ no Railway

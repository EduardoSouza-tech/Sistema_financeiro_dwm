# 🏗️ Arquitetura Multi-Database - Banco Separado por Empresa

## 📋 Visão Geral

Cada empresa terá seu próprio banco de dados PostgreSQL isolado:

```
┌─────────────────────────────────────────────────────────────┐
│                    POSTGRESQL ADMIN                          │
│  (Controle Central - Autenticação e Metadados)              │
├──────────────────────────────────────────────────────────────┤
│  Tabelas:                                                    │
│  • usuarios (login, senha, tipo)                            │
│  • empresas (id, razao_social, db_config)                   │
│  • usuario_empresa (relacionamento e permissões)            │
│  • logs_acesso                                               │
│  • sessoes                                                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ Roteamento por empresa_id
                            ↓
    ┌───────────────┬───────────────┬───────────────┐
    │               │               │               │
┌───▼────┐    ┌────▼─────┐   ┌────▼─────┐   ┌──────────┐
│ DB     │    │ DB       │   │ DB       │   │ DB       │
│Empresa1│    │Empresa 18│   │Empresa 20│   │Empresa N │
└────────┘    └──────────┘   └──────────┘   └──────────┘
  │              │              │              │
  │ Dados        │ Dados        │ Dados        │ Dados
  │ Isolados     │ Isolados     │ Isolados     │ Isolados
  │              │              │              │
  ├ categorias   ├ categorias   ├ categorias   ├ categorias
  ├ lancamentos  ├ lancamentos  ├ lancamentos  ├ lancamentos
  ├ contas       ├ contas       ├ contas       ├ contas
  ├ clientes     ├ clientes     ├ clientes     ├ clientes
  ├ fornecedores ├ fornecedores ├ fornecedores ├ fornecedores
  ├ contratos    ├ contratos    ├ contratos    ├ contratos
  └ ...          └ ...          └ ...          └ ...
```

## 🔑 Componentes Principais

### 1. Database Manager (`database_manager.py`)
```python
class DatabaseManager:
    - get_admin_connection()      # Conexão ao banco admin
    - get_empresa_connection(id)  # Conexão ao banco da empresa
    - create_empresa_database(id) # Criar novo banco
    - migrate_empresa_schema(id)  # Aplicar schema
```

### 2. Configuração por Empresa (`empresas` table)
```sql
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(255),
    cnpj VARCHAR(18),
    
    -- Configuração do banco separado
    db_host VARCHAR(255),
    db_port INTEGER,
    db_name VARCHAR(100),
    db_user VARCHAR(100),
    db_password_encrypted TEXT,
    
    -- Status
    db_ready BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Pool de Conexões Dinâmico
```python
# Cache de pools por empresa
empresa_pools = {}

def get_pool(empresa_id):
    if empresa_id not in empresa_pools:
        config = load_empresa_db_config(empresa_id)
        empresa_pools[empresa_id] = create_pool(config)
    return empresa_pools[empresa_id]
```

## 📦 Implementação

### Fase 1: Estrutura de Controle ✅
- [x] Criar `database_manager.py`
- [x] Adicionar campos `db_*` na tabela `empresas`
- [x] Criar função `get_empresa_connection()`

### Fase 2: Migração de Schema
- [ ] Script para criar banco novo
- [ ] Script para aplicar schema completo
- [ ] Validação de schema

### Fase 3: Roteamento de Conexões
- [ ] Modificar `database_postgresql.py` para usar manager
- [ ] Atualizar todas as funções para receber `empresa_id`
- [ ] Cache de pools de conexão

### Fase 4: Migração de Dados
- [ ] Script para migrar dados existentes
- [ ] Separar dados por empresa_id
- [ ] Validação pós-migração

### Fase 5: Testes
- [ ] Testar criação de empresa nova
- [ ] Testar switch entre empresas
- [ ] Testar isolamento de dados

## ⚙️ Configuração Railway

### Opção 1: PostgreSQL Plugin por Empresa (Recomendado)
```
Railway Dashboard:
├── PostgreSQL Admin (plugin)
├── PostgreSQL Empresa 1 (plugin)
├── PostgreSQL Empresa 18 (plugin)
└── PostgreSQL Empresa 20 (plugin)

Variáveis de Ambiente:
DATABASE_ADMIN_URL=postgresql://...
DATABASE_EMPRESA_1_URL=postgresql://...
DATABASE_EMPRESA_18_URL=postgresql://...
```

### Opção 2: PostgreSQL Único com Databases Separados
```
1 PostgreSQL com múltiplos databases:
├── database: admin
├── database: empresa_1
├── database: empresa_18
└── database: empresa_20

URL Pattern:
postgresql://user:pass@host:5432/admin
postgresql://user:pass@host:5432/empresa_1
postgresql://user:pass@host:5432/empresa_18
```

## 🔐 Segurança

1. **Credenciais Criptografadas**: Senhas de banco no admin são criptografadas
2. **Isolamento Total**: Cada empresa não pode acessar dados de outra
3. **Permissões**: Usuário do banco tem acesso apenas ao seu database
4. **Audit**: Logs centralizados no banco admin

## 💰 Custos Railway

### Opção 1: Plugins Separados
- Admin: $5/mês
- Cada empresa: $5/mês
- **Total**: $5 + ($5 × N empresas)
- **Exemplo**: 10 empresas = $55/mês

### Opção 2: Database Único
- 1 PostgreSQL: $5/mês (+ uso extra por dados)
- **Mais econômico** mas menos isolamento físico

## 🚀 Vantagens

✅ **Isolamento Total**: Dados de uma empresa não podem vazar para outra
✅ **Performance**: Queries não competem entre empresas
✅ **Backup Seletivo**: Backup/restore por empresa
✅ **Escalabilidade**: Mover empresas grandes para servidores dedicados
✅ **Compliance**: Facilita LGPD/GDPR (dados geograficamente separados)

## ⚠️ Desvantagens

❌ **Complexidade**: Código mais complexo
❌ **Custo**: Múltiplos bancos = custo maior
❌ **Manutenção**: Migrações devem rodar em todos os bancos
❌ **Monitoring**: Precisa monitorar N bancos

## 📝 Checklist de Deploy

- [ ] Criar banco admin no Railway
- [ ] Criar bancos por empresa no Railway
- [ ] Atualizar variáveis de ambiente
- [ ] Rodar migrações no admin
- [ ] Rodar migrações em cada empresa
- [ ] Migrar dados existentes
- [ ] Testar switch de empresas
- [ ] Validar isolamento
- [ ] Deploy em produção

## 🧪 Como Testar

```bash
# 1. Criar nova empresa
POST /api/admin/empresas
{
    "razao_social": "Empresa Teste",
    "criar_database": true
}

# 2. Sistema automaticamente:
# - Cria database no PostgreSQL
# - Aplica schema completo
# - Cria usuário de banco
# - Registra configuração

# 3. Login com usuário dessa empresa
# - Sistema roteia para o banco correto
# - Dados completamente isolados
```

## 📚 Referências

- Railway Multi-Database: https://docs.railway.app/databases/postgresql
- PostgreSQL Multiple Databases: https://www.postgresql.org/docs/current/manage-ag-createdb.html
- Connection Pooling: https://www.psycopg.org/docs/pool.html

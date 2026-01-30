# 🚀 GUIA RÁPIDO: Deploy Multi-Database

## ✅ FASE 1: Preparar Banco Admin (5 minutos)

### 1.1 Rodar Migração no Banco Atual
```bash
python migration_add_db_fields.py
```

Isso adiciona os campos `db_*` na tabela `empresas`.

### 1.2 Verificar no Railway
```sql
-- Conecte no banco admin e verifique:
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'empresas' AND column_name LIKE 'db_%';

-- Deve mostrar:
-- db_host
-- db_port
-- db_name
-- db_user
-- db_password_encrypted
-- db_ready
```

## 📦 FASE 2: Criar Databases no Railway (10 minutos)

### Opção A: PostgreSQL Plugin por Empresa (Recomendado)

1. **Railway Dashboard** → Seu Projeto
2. **New** → **Database** → **Add PostgreSQL**
3. Renomeie para: `PostgreSQL - Empresa 18`
4. Copie as credenciais:
   ```
   PGHOST_EMPRESA_18=viaduct.proxy.rlwy.net
   PGPORT_EMPRESA_18=12345
   PGDATABASE_EMPRESA_18=railway
   PGUSER_EMPRESA_18=postgres
   PGPASSWORD_EMPRESA_18=abc123...
   ```
5. Repita para cada empresa

### Opção B: Database Único com Schemas Separados (Mais Barato)

1. Conecte no PostgreSQL atual
2. Crie databases:
   ```sql
   CREATE DATABASE empresa_18;
   CREATE DATABASE empresa_20;
   ```
3. Use mesma URL, mudando apenas o nome:
   ```
   postgresql://user:pass@host:5432/empresa_18
   postgresql://user:pass@host:5432/empresa_20
   ```

## ⚙️ FASE 3: Configurar Variáveis de Ambiente (2 minutos)

Railway → Variables:

```env
# Banco Admin (atual)
DATABASE_ADMIN_URL=postgresql://...

# Chave de criptografia (gere uma nova)
DB_ENCRYPTION_KEY=gAAAAABl...

# Opcional: Se não usar plugins separados
PGHOST=viaduct.proxy.rlwy.net
PGPORT=12345
PGUSER=postgres
PGPASSWORD=abc123...
```

Gerar chave:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## 🔧 FASE 4: Criar Databases para Empresas Existentes (5 minutos)

Execute este script Python:

```python
from database_manager import create_empresa_database

# Para empresa 18
result = create_empresa_database(
    empresa_id=18,
    razao_social="CONSERVADORA NEVES ALCANTARA LTDA"
)
print(result)

# Para empresa 20 (COOPSERVICOS)
result = create_empresa_database(
    empresa_id=20,
    razao_social="COOPSERVICOS"
)
print(result)
```

Isso irá:
- ✅ Criar database `empresa_18` e `empresa_20`
- ✅ Criar usuários de banco
- ✅ Aplicar schema completo
- ✅ Salvar configuração no banco admin

## 📊 FASE 5: Migrar Dados Existentes (10 minutos)

```python
from database_manager import migrate_existing_data

# Migrar dados da empresa 18
migrate_existing_data(18)

# Migrar dados da empresa 20
migrate_existing_data(20)
```

Isso copia todos os dados do banco antigo para os novos databases.

## 🧪 FASE 6: Testar (3 minutos)

1. **Faça login** com usuário da empresa 18
2. **Verifique** que os dados aparecem corretamente
3. **Crie um lançamento** de teste
4. **Conecte no banco** e verifique:
   ```sql
   -- No banco empresa_18
   SELECT * FROM lancamentos ORDER BY id DESC LIMIT 1;
   
   -- No banco empresa_20 (NÃO DEVE TER DADOS DA EMPRESA 18)
   SELECT COUNT(*) FROM lancamentos;  -- Deve ser 0 ou só dados da empresa 20
   ```

## ✅ Checklist Final

- [ ] migration_add_db_fields.py executado com sucesso
- [ ] Databases criados no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Empresas 18 e 20 têm databases criados
- [ ] Dados migrados com sucesso
- [ ] Teste de login funcionando
- [ ] Isolamento verificado (empresa 18 não vê dados da 20)

## ⚠️ IMPORTANTE: Rollback

Se algo der errado, você pode voltar ao sistema antigo:

1. **Não delete** o banco antigo ainda
2. **Remova** as configurações de variáveis multi-database
3. **Reverta** o código para commit anterior:
   ```bash
   git revert HEAD
   git push
   ```

## 📝 Próximos Passos (Após Validação)

1. **Integrar** database_manager nas rotas do web_server.py
2. **Atualizar** database_postgresql.py para usar pools por empresa
3. **Remover** filtros `empresa_id` das queries
4. **Testar** exaustivamente antes de deletar banco antigo

## 💰 Custos Estimados

### Opção A: Plugins Separados
- Admin: $5/mês
- Empresa 18: $5/mês
- Empresa 20: $5/mês
- **Total**: $15/mês (2 empresas)

### Opção B: Database Único
- 1 PostgreSQL: $5/mês (+ $0.20/GB extra)
- **Total**: ~$7-10/mês (2 empresas)

## 📞 Suporte

Se tiver problemas:
1. Verifique logs do Railway
2. Teste conexão manual: `psql $DATABASE_URL`
3. Confira se variáveis estão corretas
4. Entre em contato se precisar de ajuda

---

**Tempo total estimado**: ~35 minutos
**Dificuldade**: Média
**Reversível**: Sim (mantenha backup do banco antigo)

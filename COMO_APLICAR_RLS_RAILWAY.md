# 🚀 APLICAR RLS NO RAILWAY - INSTRUÇÕES

## Opção 1: Via Terminal Local (RECOMENDADO)

### Passo 1: Pegar credenciais do Railway

1. Acesse [Railway Dashboard](https://railway.app)
2. Selecione seu projeto
3. Clique no **PostgreSQL** plugin
4. Clique em **"Connect"**
5. Copie a **DATABASE_URL** completa

Exemplo:
```
postgresql://postgres:senha@xxxx.railway.app:5432/railway
```

### Passo 2: Configurar variável de ambiente

**No PowerShell:**
```powershell
$env:DATABASE_URL="postgresql://postgres:senha@xxxx.railway.app:5432/railway"
```

**Ou crie um arquivo `.env.railway` com:**
```
DATABASE_URL=postgresql://postgres:senha@xxxx.railway.app:5432/railway
```

### Passo 3: Executar o script

```powershell
cd Sistema_financeiro_dwm
python aplicar_rls.py
```

---

## Opção 2: Forçar Redeploy no Railway

1. Acesse Railway Dashboard
2. Vá no seu projeto
3. Clique em **"Deployments"**
4. No último deploy, clique nos **3 pontinhos** ⋮
5. Selecione **"Redeploy"**
6. Aguarde ~2 minutos
7. Verifique os logs - deve aparecer:
   ```
   🔍 VERIFICANDO ROW LEVEL SECURITY
   ✅ Row Level Security aplicado com sucesso!
   ```

---

## Opção 3: Via Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Conectar ao projeto
railway link

# Executar script
railway run python aplicar_rls.py
```

---

## ✅ Como Verificar se Aplicou

### No PostgreSQL (Railway Dashboard):

Vá em PostgreSQL > Query e execute:

```sql
SELECT * FROM rls_status;
```

**Se RLS está ativo, você verá:**
```
tablename          | rls_enabled | policy_count
-------------------+-------------+-------------
lancamentos        | true        | 1
categorias         | true        | 1
clientes           | true        | 1
contas             | true        | 1
...
```

**Se RLS NÃO está ativo:**
```
ERROR: relation "rls_status" does not exist
```

---

## 🎯 Recomendação

**Use a Opção 1 agora mesmo!**

É a forma mais rápida e segura. Leva apenas 2 minutos:

1. Copie DATABASE_URL do Railway
2. Execute no PowerShell:
   ```powershell
   $env:DATABASE_URL="sua_url_aqui"
   cd Sistema_financeiro_dwm
   python aplicar_rls.py
   ```
3. Confirme com "s" quando perguntar
4. Pronto! RLS aplicado.

---

## ⚠️ Importante

Após aplicar manualmente (Opção 1), o `setup_database.py` nos próximos deploys vai:
- Detectar que RLS já existe
- Pular a aplicação
- Continuar normalmente

Ou seja: **seguro aplicar manualmente agora** e deixar o script automático para o futuro.

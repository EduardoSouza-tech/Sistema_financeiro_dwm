# 🔧 VARIÁVEIS DE AMBIENTE - Railway

Configurações para os 3 serviços do sistema.

---

## 📊 **SERVIÇO 1: ERP Financeiro** (Principal)

### Nome no Railway: `ERP Financeiro` ou `sistemafinanceirodwm-production-c3e6`

```bash
# ===== BANCO DE DADOS =====
DATABASE_URL="${{Postgres.DATABASE_URL}}"
DATABASE_TYPE="postgresql"
PGDATABASE="${{Postgres.PGDATABASE}}"
PGPASSWORD="${{Postgres.PGPASSWORD}}"

# ===== FLASK =====
SECRET_KEY="1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45"
FLASK_ENV="production"

# ===== CRIPTOGRAFIA =====
DB_ENCRYPTION_KEY="2b8eb9483aa5a086fb33387a91c61218031faf4cd10ffe284d5ec68f0cea67f1"
FERNET_KEY="GERAR_NOVA_CHAVE_ABAIXO"

# ===== LOGGING =====
LOG_LEVEL="INFO"

# ===== GOOGLE (opcional) =====
GOOGLE_CLIENT_SECRET="bvg6jb32q989qdrtibplxcsg8qq35bna"

# ===== ADMIN (opcional) =====
PGDATABASE_ADMIN="${{Postgres.PGDATABASE_ADMIN}}"
```

**Gerar FERNET_KEY:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## 🧾 **SERVIÇO 2: Busca de Notas** (NF-e/CT-e)

### Nome no Railway: `Busca de Notas`

```bash
# ===== BANCO DE DADOS =====
DATABASE_URL="${{Postgres.DATABASE_URL}}"

# ===== FLASK =====
SECRET_KEY="1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45"
FLASK_ENV="production"

# ===== CRIPTOGRAFIA (OBRIGATÓRIA) =====
FERNET_KEY="GERAR_NOVA_CHAVE_ABAIXO"

# ===== INTEGRAÇÃO =====
FRONTEND_URL="https://sistemafinanceirodwm-production-c3e6.up.railway.app"

# ===== LOGGING =====
LOG_LEVEL="INFO"
```

**⚠️ IMPORTANTE:** `FERNET_KEY` é **OBRIGATÓRIA** para este serviço!

---

## 📋 **SERVIÇO 3: NFS-e Exportação**

### Nome no Railway: `NFS-e Exportação`

```bash
# ===== BANCO DE DADOS =====
DATABASE_URL="${{Postgres.DATABASE_URL}}"

# ===== FLASK =====
SECRET_KEY="1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45"
FLASK_ENV="production"

# ===== INTEGRAÇÃO =====
FRONTEND_URL="https://sistemafinanceirodwm-production-c3e6.up.railway.app"

# ===== LOGGING =====
LOG_LEVEL="INFO"
```

---

## 🗄️ **PostgreSQL** (Compartilhado)

Os 3 serviços usam o **mesmo banco** PostgreSQL no Railway.

**Configuração automática pelo Railway:**
```bash
PGHOST=centerbeam.proxy.rlwy.net
PGPORT=12659
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT
DATABASE_URL=postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway
```

---

## 📋 RESUMO - Variáveis Necessárias

| Variável | ERP Principal | Busca Notas | NFS-e | Obrigatória? |
|----------|---------------|-------------|-------|-------------|
| `DATABASE_URL` | ✅ | ✅ | ✅ | **SIM** |
| `SECRET_KEY` | ✅ | ✅ | ✅ | **SIM** |
| `FLASK_ENV` | ✅ | ✅ | ✅ | **SIM** |
| `FERNET_KEY` | ✅ | ✅ | ❌ | **SIM** (para NF-e) |
| `DB_ENCRYPTION_KEY` | ✅ | ❌ | ❌ | Recomendada |
| `FRONTEND_URL` | ❌ | ✅ | ✅ | Recomendada |
| `LOG_LEVEL` | ✅ | ✅ | ✅ | Opcional |

---

## 🚀 COMO CONFIGURAR NO RAILWAY

### Para cada serviço:

1. Acesse o serviço no Railway Dashboard
2. Vá em **Settings → Variables**
3. Clique em **New Variable**
4. Cole as variáveis correspondentes

### Usar referências entre serviços:

```bash
# Para conectar ao PostgreSQL existente:
DATABASE_URL="${{Postgres.DATABASE_URL}}"

# Para conectar a outro serviço:
FRONTEND_URL="${{ERP-Financeiro.RAILWAY_PUBLIC_DOMAIN}}"
```

---

## 🔐 GERAR CHAVES DE CRIPTOGRAFIA

### FERNET_KEY (Python):
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
# Exemplo: xK8jD3mP9qR2sT5vW8yZ1aB4cE7fG0hI3jL6mN9pQ2s=
```

### SECRET_KEY (Python):
```python
import secrets
print(secrets.token_hex(32))
# Exemplo: 1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45
```

### DB_ENCRYPTION_KEY (Python):
```python
import secrets
print(secrets.token_hex(32))
# Exemplo: 2b8eb9483aa5a086fb33387a91c61218031faf4cd10ffe284d5ec68f0cea67f1
```

---

## ✅ CHECKLIST FINAL

### ERP Financeiro:
- [ ] DATABASE_URL configurado
- [ ] SECRET_KEY configurado
- [ ] FLASK_ENV = production
- [ ] FERNET_KEY gerado e configurado
- [ ] DB_ENCRYPTION_KEY configurado

### Busca de Notas:
- [ ] DATABASE_URL = ${{Postgres.DATABASE_URL}}
- [ ] SECRET_KEY configurado
- [ ] FLASK_ENV = production
- [ ] **FERNET_KEY gerado e configurado** ⚠️
- [ ] FRONTEND_URL configurado

### NFS-e Exportação:
- [ ] DATABASE_URL = ${{Postgres.DATABASE_URL}}
- [ ] SECRET_KEY configurado
- [ ] FLASK_ENV = production
- [ ] FRONTEND_URL configurado

---

## 🔗 URLs dos Serviços

Após o deploy, os serviços estarão disponíveis em:

- **ERP:** https://sistemafinanceirodwm-production-c3e6.up.railway.app
- **Busca Notas:** https://busca-de-notas.up.railway.app
- **NFS-e:** https://nfs-e-exportacao.up.railway.app

---

**Última atualização:** 17/02/2026

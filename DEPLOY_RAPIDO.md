# 🚀 DEPLOY SIMPLIFICADO - Railway

**SERVIÇOS UNIFICADOS:** NF-e + CT-e + NFS-e = 1 microserviço só!

---

## 📋 **VARIÁVEIS PARA COPIAR**

### 🏢 **ERP Financeiro** (Serviço que já existe)

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_TYPE=postgresql
SECRET_KEY=1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45
FLASK_ENV=production
DB_ENCRYPTION_KEY=2b8eb9483aa5a086fb33387a91c61218031faf4cd10ffe284d5ec68f0cea67f1
FERNET_KEY=tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=
LOG_LEVEL=INFO
PGDATABASE=${{Postgres.PGDATABASE}}
PGPASSWORD=${{Postgres.PGPASSWORD}}
```

---

### 📊 **Documentos Fiscais** (CRIAR NOVO - unifica NF-e + CT-e + NFS-e)

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45
FLASK_ENV=production
FERNET_KEY=tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=
FRONTEND_URL=https://sistemafinanceirodwm-production-c3e6.up.railway.app
LOG_LEVEL=INFO
```

**Build Command:**
```
pip install -r requirements_fiscal.txt
```

**Start Command:**
```
gunicorn app_fiscal:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Healthcheck Path:**
```
/health
```

---

## 🎯 **PASSO A PASSO RÁPIDO**

### 1️⃣ **Adicionar FERNET_KEY no ERP** (1 minuto)

1. Railway → **ERP Financeiro** → Settings → Variables
2. **+ New Variable**
3. Nome: `FERNET_KEY`
4. Valor: `tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=`
5. **Add** → Aguarde reiniciar (30-60s)

---

### 2️⃣ **Criar "Documentos Fiscais"** (5 minutos)

1. Railway → **+ New** → **GitHub Repo** 
2. Repo: `Sistema_financeiro_dwm`
3. Nome: **`Documentos Fiscais`**

#### Configurar Build:
- Settings → Build → Custom Build Command:
  ```
  pip install -r requirements_fiscal.txt
  ```

#### Configurar Deploy:
- Settings → Deploy → Custom Start Command:
  ```
  gunicorn app_fiscal:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
  ```
- Deploy → Healthcheck Path:
  ```
  /health
  ```

#### Adicionar Variáveis:
Settings → Variables → Cole as 6 variáveis acima (uma por vez)

---

### 3️⃣ **Testar** (2 minutos)

Acesse: `https://[seu-dominio].up.railway.app/health`

Deve retornar:
```json
{
  "status": "healthy",
  "service": "documentos-fiscais",
  "modules": ["nfe", "cte", "nfse"],
  "timestamp": "2026-02-17T..."
}
```

---

## ✅ **PRONTO!**

**Arquitetura final:**
- ✅ ERP Financeiro (principal)
- ✅ Documentos Fiscais (NF-e + CT-e + NFS-e unificados)
- ✅ PostgreSQL (compartilhado)

**Total:** 2 serviços aplicação + 1 banco = **3 serviços no Railway**

---

## 📡 **ENDPOINTS DISPONÍVEIS**

### NF-e/CT-e (11 endpoints):
- `GET /api/nfe/certificados` - Listar certificados
- `POST /api/nfe/certificados/novo` - Cadastrar certificado
- `POST /api/nfe/buscar-documentos` - Busca automática SEFAZ
- `POST /api/nfe/consultar-chave` - Consultar por chave
- `GET /api/nfe/documentos` - Listar documentos
- `GET /api/nfe/documento/:id/xml` - Download XML

### NFS-e (9 endpoints):
- `GET /api/nfse/config` - Listar municípios
- `POST /api/nfse/config` - Cadastrar município
- `POST /api/nfse/buscar` - Buscar por período
- `GET /api/nfse` - Listar NFS-e
- `GET /api/nfse/:id/pdf` - Download PDF
- `GET /api/nfse/provedores` - Listar provedores (GINFES, ISS.NET, BETHA...)

### Gerais (3 endpoints):
- `GET /health` - Health check
- `POST /api/fiscal/exportar-excel` - Exportar Excel (NF-e ou NFS-e)
- `GET /api/fiscal/estatisticas` - Estatísticas consolidadas

---

## 🔧 **TROUBLESHOOTING**

### ❌ Build failed
→ Verifique: `pip install -r requirements_fiscal.txt`

### ❌ FERNET_KEY not configured
→ Adicione: `tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=`

### ❌ Health retorna 503
→ Verifique `DATABASE_URL=${{Postgres.DATABASE_URL}}`

### ❌ ModuleNotFoundError
→ Confirme que pastas `relatorios/nfe/` e arquivos `nfse_*.py` existem

---

**📖 Documentação completa:** `GUIA_DEPLOY_RAILWAY.md`

**✅ Commit:** `9fd5add` - Sistema unificado pronto!

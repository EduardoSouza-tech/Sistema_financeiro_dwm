# 🚀 Deploy Railway - Configuração Multi-Serviço

Este repositório contém **2 serviços separados** que devem ser deployados em instâncias diferentes do Railway:

## 📦 Serviços

### 1️⃣ Sistema Financeiro DWM (ERP Principal)
**URL**: `sistemafinanceirodwm-production.up.railway.app`

**Configuração no Railway Dashboard:**
```
Root Directory: /
Build Command: pip install -r requirements.txt
Start Command: python web_server.py
Healthcheck Path: /health
```

**Variáveis de ambiente necessárias:**
- `DATABASE_URL` (PostgreSQL)
- `SECRET_KEY`
- `FERNET_KEY`
- `DB_ENCRYPTION_KEY`
- Todas as outras do arquivo `.env`

**Arquivos usados:**
- `requirements.txt` (dependências)
- `Procfile` (opcional - Railway detecta automaticamente)
- `railway.toml` (configuração principal)

---

### 2️⃣ Microserviço Busca NFS-e
**URL**: `busca-de-notas-production.up.railway.app`

**Configuração no Railway Dashboard:**
```
Root Directory: /
Build: Rename nixpacks_nfse.toml to nixpacks.toml (ou configurar manualmente)
Start Command: . /tmp/venv/bin/activate && gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 1800 --log-level info
Healthcheck Path: /health
```

**Variáveis de ambiente necessárias:**
- `DATABASE_URL` (PostgreSQL - mesmo banco do ERP)
- `FRONTEND_URL` (URL do ERP principal)

**Arquivos usados:**
- `requirements_nfse.txt` (dependências)
- `nixpacks_nfse.toml` → renomear para `nixpacks.toml` no serviço
- `Procfile_nfse` (backup)

---

## 🔧 Como Configurar no Railway

### Método 1: Comandos Manuais (Recomendado)

1. **Criar serviço ERP Principal:**
   - New Service → GitHub Repo
   - Settings → Build: `pip install -r requirements.txt`
   - Settings → Deploy: `python web_server.py`
   - Settings → Healthcheck: `/health`

2. **Criar serviço Microserviço:**
   - New Service → GitHub Repo (mesmo repositório)
   - Settings → No Railway Dashboard, em "Settings → Deploy → Custom Start Command":
     ```
     cp nixpacks_nfse.toml nixpacks.toml && . /tmp/venv/bin/activate && gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 1800 --log-level info
     ```
   - **OU** criar branch separado `microservico-nfse` com nixpacks.toml na raiz

### Método 2: Branches Separados (Alternativa)

**Branch `main`:**
- ERP Principal (web_server.py)
- Sem nixpacks.toml
- railway.toml aponta para Procfile

**Branch `microservico-nfse`:**
- Renomear `nixpacks_nfse.toml` → `nixpacks.toml`
- Deploy apenas app_nfse.py

---

## ⚠️ Problemas Comuns

### "ERP não está iniciando"
- ✅ Verificar se o serviço está usando `railway.toml` (não nixpacks)
- ✅ Confirmar que `requirements.txt` está sendo instalado
- ✅ Verificar variáveis de ambiente (DATABASE_URL, etc)

### "Microserviço com erro de pip"
- ✅ Verificar se `nixpacks.toml` está presente no deploy do microserviço
- ✅ Confirmar que virtualenv está sendo criado
- ✅ Checar logs de build: deve criar `/tmp/venv`

### "Ambos usando mesma configuração"
- ✅ Railway detecta automaticamente `nixpacks.toml` se estiver na raiz
- ✅ Para evitar conflito, usar branches separados OU comandos manuais

---

## 📝 Resumo Visual

```
┌────────────────────────────────────────────────────┐
│ GitHub Repo (main branch)                          │
│                                                    │
│  ├─ web_server.py ────────►  ERP Principal         │
│  │  requirements.txt         (Railway Service 1)  │
│  │  railway.toml                                   │
│  │  Procfile                                       │
│  │                                                 │
│  └─ app_nfse.py ──────────►  Microserviço         │
│     requirements_nfse.txt     (Railway Service 2)  │
│     nixpacks_nfse.toml*                            │
│     Procfile_nfse                                  │
│                                                    │
│  * Renomear para nixpacks.toml no deploy          │
└────────────────────────────────────────────────────┘
```

---

## 🎯 Status Esperado

Após configuração correta:

✅ **ERP Principal**: https://sistemafinanceirodwm-production.up.railway.app
   - Interface completa do sistema
   - Login, dashboard, relatórios, etc

✅ **Microserviço**: https://busca-de-notas-production.up.railway.app
   - Página simples "API NFS-e Consulta"
   - Endpoints: /api/nfse/buscar, /health, etc
   - Não é interface pública - usado pelo ERP

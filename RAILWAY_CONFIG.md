# ⚙️ CONFIGURAÇÃO RAILWAY - SEPARAÇÃO DE SERVIÇOS

Este repositório contém **2 serviços independentes** que devem ser deployados separadamente no Railway.

> **⚠️ IMPORTANTE**: Railway agora usa **Railpack** por padrão (substituiu Nixpacks em 2025-2026).

---

## ✅ **CONFIGURAÇÃO VALIDADA E FUNCIONANDO (Fev/2026)**

### 🎯 Microserviço NFS-e: **DEPLOY CONFIRMADO** ✅

**Logs de sucesso:**
```
INFO:app_nfse:✅ DATABASE_URL configurada
[2026-02-26 22:43:22] [INFO] Starting gunicorn 21.2.0
[2026-02-26 22:43:22] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2026-02-26 22:43:22] [INFO] Using worker: sync
[2026-02-26 22:43:22] [INFO] Booting worker with pid: 4
[2026-02-26 22:43:22] [INFO] Booting worker with pid: 5
INFO:app_nfse:✅ Microserviço de busca inicializado (modo stateless)
```

---

## 📋 ARQUIVOS DE CONFIGURAÇÃO

```
├── nixpacks.toml          → ERP Principal (Nixpacks/Railpack compatível)
├── nixpacks_nfse.toml     → Microserviço (Nixpacks/Railpack compatível)
├── requirements.txt       → Dependências ERP
├── requirements_nfse.txt  → Dependências Microserviço
├── Procfile               → Start command ERP
└── Procfile_nfse          → Start command Microserviço
```

---

## 🎯 SERVIÇO 1: ERP Principal (sistemafinanceirodwm-production)

### Configuração no Railway:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python web_server.py`
- **Python Version**: 3.11 (via nixpacks.toml ou runtime.txt)

✅ Railway detecta automaticamente via `nixpacks.toml` ou `Procfile`.

---

## 🎯 SERVIÇO 2: Microserviço Busca NFS-e (busca-de-notas-production)

### 🔧 CONFIGURAÇÃO MANUAL (TESTADA E VALIDADA ✅)

**Status:** Deploy bem-sucedido em 26/Fev/2026

#### Settings → Deploy:

**Build Command:**
```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements_nfse.txt
```

**Start Command:**
```bash
gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 1800 --log-level info
```

**Pre-deploy Command:** *(DEIXAR VAZIO)*

---

#### Settings → Variables (CONFIGURAÇÃO EXATA QUE FUNCIONOU):

```bash
DATABASE_URL = ${{Postgres.DATABASE_URL}}
SECRET_KEY = 1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45
FLASK_ENV = production
PORT = 8080
PYTHON_VERSION = 3.11
LOG_LEVEL = INFO
FRONTEND_URL = https://sistemafinanceirodwm-production.up.railway.app
```

**⚠️ NÃO ADICIONAR:**
- ❌ `NIXPACKS_CONFIG_FILE` (obsoleto com Railpack)
- ❌ Qualquer configuração de virtualenv customizado

---

#### Settings → Healthcheck:

```
Path: /health
Timeout: 30s
```

---

### ✅ RESULTADO ESPERADO (CONFIRMADO):

**Build Logs:**
```
Successfully installed Flask-3.0.0 Jinja2-3.1.6 ... gunicorn-21.2.0
Build time: ~24s
```

**Deploy Logs:**
```
INFO:app_nfse:✅ DATABASE_URL configurada
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080 (1)
[INFO] Using worker: sync
[INFO] Booting worker with pid: 4
[INFO] Booting worker with pid: 5
INFO:app_nfse:✅ Microserviço de busca inicializado (modo stateless)
```

**Healthcheck:**
```
✅ PASSED - Service healthy
```

---

## ✅ VARIÁVEIS DE AMBIENTE

### ERP Principal:
```bash
DATABASE_URL="${{Postgres.DATABASE_URL}}"
DATABASE_TYPE="postgresql"
SECRET_KEY="..."
FLASK_ENV="production"
DB_ENCRYPTION_KEY="..."
FERNET_KEY="..."
LOG_LEVEL="INFO"
NFSE_SERVICE_URL="https://busca-de-notas-production.up.railway.app"
# ... outras variáveis SMTP, Google, etc
```

### Microserviço:
```bash
DATABASE_URL="${{Postgres.DATABASE_URL}}"
SECRET_KEY="..."
FLASK_ENV="production"
LOG_LEVEL="INFO"
FRONTEND_URL="https://sistemafinanceirodwm-production.up.railway.app"
PORT=8080
PYTHON_VERSION=3.11
```

---

## 🚨 CHECKLIST PÓS-DEPLOY

### ERP Principal:
- [ ] Build completa sem erros
- [ ] Detectou Python (não Node.js)
- [ ] Instalou requirements.txt
- [ ] Iniciou com `python web_server.py`
- [ ] Healthcheck `/health` passou
- [ ] URL acessível: sistemafinanceirodwm-production.up.railway.app

### Microserviço:
- [ ] Build completa sem erros (Railpack)
- [ ] Detectou Python 3.11
- [ ] Instalou requirements_nfse.txt
- [ ] Iniciou com gunicorn (timeout 1800s, 2 workers)
- [ ] Healthcheck `/health` passou (retry window 30s)
- [ ] URL acessível: busca-de-notas-production.up.railway.app
- [ ] Log: "Listening at: http://0.0.0.0:8080"

---

## ❌ ERROS COMUNS E SOLUÇÕES

### 🔴 "/tmp/venv/bin/activate: No such file or directory" (ATUAL - RAILPACK)
**Causa:** Railpack não persiste `/tmp` entre build e deploy
**Logs:** 
```
Build: Successfully installed Flask-3.0.0...
Deploy: /bin/bash: line 1: /tmp/venv/bin/activate: No such file or directory
Healthcheck failed!
```
**Solução:**
1. Settings → Deploy → **Start Command**:
   ```
   gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 1800 --log-level info
   ```
2. Settings → Deploy → **Build Command**:
   ```
   pip install --upgrade pip setuptools wheel && pip install -r requirements_nfse.txt
   ```
3. **Redeploy** o serviço

### 🟠 "Provider: Node" no Microserviço
**Causa:** Railway detectando Node.js ao invés de Python
**Solução:** 
- Confirmar que `package.json` foi renomeado para `package.json.dev`
- Adicionar arquivo `runtime.txt` com `python-3.11`
- Redeploy forçado

### 🟡 "python: command not found"
**Causa:** Cache do Railway ou detecção incorreta de runtime
**Solução:** 
- Settings → Deploy → Clear build cache
- Redeploy forçado

### 🟢 "Pre-deploy: npm run migrate" executando
**Causa:** Comando Node.js residual de detecção anterior
**Solução:** Settings → Deploy → Pre-deploy command → **DELETAR TUDO**

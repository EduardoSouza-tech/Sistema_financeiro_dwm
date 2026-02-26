# ⚙️ CONFIGURAÇÃO RAILWAY - SEPARAÇÃO DE SERVIÇOS

Este repositório contém **2 serviços independentes** que devem ser deployados separadamente no Railway.

> **⚠️ IMPORTANTE**: Railway agora usa **Railpack** por padrão (substituiu Nixpacks em 2025-2026).

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

### 🔧 CONFIGURAÇÃO MANUAL OBRIGATÓRIA (Railpack):

**1. Remover Comandos Antigos:**
- Settings → Deploy → Pre-deploy command: **DELETAR** qualquer comando (especialmente "npm run migrate")
- Settings → Variables → **DELETAR** `NIXPACKS_CONFIG_FILE` (se existir)

**2. Configurar Build & Start Commands:**

**Settings → Deploy:**
```bash
Build Command:
pip install --upgrade pip setuptools wheel && pip install -r requirements_nfse.txt

Start Command:
gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 1800 --log-level info
```

**3. Variáveis de Ambiente Obrigatórias:**

Settings → Variables → Add:
```
FRONTEND_URL=https://sistemafinanceirodwm-production.up.railway.app
PORT=8080
PYTHON_VERSION=3.11
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

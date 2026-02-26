# ⚙️ CONFIGURAÇÃO RAILWAY - SEPARAÇÃO DE SERVIÇOS

Este repositório contém **2 serviços independentes** que devem ser deployados separadamente no Railway.

## 📋 ARQUIVOS DE CONFIGURAÇÃO

```
├── nixpacks.toml          → ERP Principal APENAS
├── nixpacks_nfse.toml     → Microserviço APENAS
├── Procfile               → Backup (ERP)
└── Procfile_nfse          → Backup (Microserviço)
```

---

## 🎯 SERVIÇO 1: ERP Principal (sistemafinanceirodwm-production)

### Arquivo: `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip"]

[phases.install]
cmds = ["pip install --upgrade pip setuptools wheel", "pip install -r requirements.txt"]

[start]
cmd = "python web_server.py"
```

### Configuração no Railway:
- **NADA A FAZER** - Railway detecta `nixpacks.toml` automaticamente
- Build: Automático (pip install requirements.txt)
- Start: Automático (python web_server.py)

---

## 🎯 SERVIÇO 2: Microserviço Busca NFS-e (busca-de-notas-production)

### Arquivo: `nixpacks_nfse.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "python311Packages.virtualenv", "zlib"]

[phases.install]
cmds = [
  "python3 -m venv /tmp/venv",
  ". /tmp/venv/bin/activate && pip install --upgrade pip setuptools wheel",
  ". /tmp/venv/bin/activate && pip install -r requirements_nfse.txt"
]

[start]
cmd = ". /tmp/venv/bin/activate && gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 1800 --log-level info"
```

### ⚠️ AÇÃO OBRIGATÓRIA no Railway Dashboard:

**Opção 1 - Variável de Ambiente (RECOMENDADO):**
```
Settings → Variables → Add Variable:
Nome: NIXPACKS_CONFIG_FILE  
Valor: nixpacks_nfse.toml
```

**Opção 2 - Config-as-code:**
```
Settings → Config-as-code → Railway Config File:
Adicionar path: nixpacks_nfse.toml
```

**Depois:** Clicar em **Redeploy**

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
- [ ] Build completa sem erros
- [ ] Detectou Python (não Node.js)
- [ ] Criou virtualenv em `/tmp/venv`
- [ ] Instalou requirements_nfse.txt dentro do venv
- [ ] Iniciou com gunicorn + timeout 1800s
- [ ] Healthcheck `/health` passou
- [ ] URL acessível: busca-de-notas-production.up.railway.app

---

## ❌ ERROS COMUNS

### "Provider: Node" no Microserviço
**Causa:** Railway não está usando `nixpacks_nfse.toml`
**Solução:** Adicionar variável `NIXPACKS_CONFIG_FILE=nixpacks_nfse.toml`

### "python: command not found"
**Causa:** Removido package.json mas Railway ainda com cache
**Solução:** Redeploy forçado ou limpar cache

### "/tmp/venv/bin/activate: No such file or directory"
**Causa:** Microserviço usando `nixpacks.toml` (sem virtualenv)
**Solução:** Configurar `NIXPACKS_CONFIG_FILE=nixpacks_nfse.toml`

### "Pre-deploy: npm run migrate"
**Causa:** Comando Node.js residual de detecção anterior
**Solução:** Settings → Deploy → Remover Pre-deploy command

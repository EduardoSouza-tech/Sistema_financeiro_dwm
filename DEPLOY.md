# 🚀 Guia de Deploy - Railway

**Última atualização:** 20/01/2026  
**Plataforma:** Railway.app  
**Versão:** 2.0

---

## 📋 Pré-requisitos

- Conta no [Railway.app](https://railway.app)
- Repositório GitHub configurado
- PostgreSQL plugin no Railway
- Variáveis de ambiente configuradas

---

## ⚡ Quick Deploy

### 1. **Setup Inicial no Railway**

```bash
# 1. Criar novo projeto no Railway
# 2. Adicionar PostgreSQL Plugin
# 3. Conectar repositório GitHub
# 4. Railway detectará automaticamente Procfile/requirements
```

### 2. **Variáveis de Ambiente**

Configure no Railway Dashboard → Variables:

```env
# Banco de Dados (auto-gerado pelo Railway)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Segurança
SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_hex(32))">

# Ambiente
RAILWAY_ENVIRONMENT=production
FLASK_ENV=production

# Logging (Opcional)
LOG_LEVEL=INFO
SENTRY_DSN=<seu_sentry_dsn>  # Se usar Sentry

# Session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
```

### 3. **Deploy Automático**

```bash
# Push para GitHub
git push origin main

# Railway fará deploy automaticamente
# Aguardar ~2-3 minutos
```

---

## 🔧 Configuração Detalhada

### **Procfile** (já configurado)

```
web: gunicorn web_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Explicação:**
- `web_server:app`: Módulo e instância do Flask
- `--bind 0.0.0.0:$PORT`: Porta dinâmica do Railway
- `--workers 2`: 2 workers Gunicorn (ajustar conforme plano)
- `--timeout 120`: Timeout de 120s (relatórios pesados)

### **requirements_web.txt**

```txt
flask==3.0.0
flask-cors==4.0.0
flask-limiter==3.5.0
flask-compress==1.14
bcrypt==4.1.2
psycopg2-binary==2.9.9
ofxparse==0.21
gunicorn==21.2.0
python-dotenv==1.0.0
```

**Instalação automática** pelo Railway via `pip install -r requirements_web.txt`

---

## 🗄️ Setup do Banco de Dados

### **1. Criar Plugin PostgreSQL**

No Railway Dashboard:
1. Clique em "New" → "Database" → "Add PostgreSQL"
2. Railway criará automaticamente `DATABASE_URL`
3. Conecte-se via Railway Console ou pgAdmin

### **2. Executar Migrations**

#### **Via Railway Console:**

```bash
# Abrir Railway Shell
railway shell

# Executar Python
python
>>> import migration_performance_indexes
>>> migration_performance_indexes.create_indexes()
>>> migration_performance_indexes.analyze_tables()
>>> exit()
```

#### **Via API Endpoint:**

```bash
# Executar POST request
curl -X POST https://[SEU-APP].up.railway.app/api/debug/create-performance-indexes \
     -H "Content-Type: application/json" \
     -d '{}'
```

**Resultado esperado:**
```json
{
  "success": true,
  "summary": {
    "indexes_created": 36,
    "indexes_skipped": 0,
    "errors": 0
  }
}
```

### **3. Verificar Índices**

```sql
-- Conectar via Railway Console → PostgreSQL
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Deve retornar 36 linhas
```

---

## 🌐 Configuração de Domínio

### **Domínio Railway (padrão)**

```
https://sistema-financeiro-dwm-production.up.railway.app
```

### **Domínio Customizado**

1. Railway Dashboard → Settings → Domains
2. Add Custom Domain: `seudominio.com.br`
3. Adicionar registros DNS:
   ```
   CNAME www seudominio.railway.app
   A @ <ip-do-railway>
   ```
4. Aguardar propagação (até 24h)
5. Railway configurará SSL automaticamente

---

## 🔒 Segurança em Produção

### **HTTPS Obrigatório**

Railway fornece SSL automático via Let's Encrypt.

### **CSRF Protection**

Já configurado em `web_server.py`:
```python
csrf = CSRFProtect(app)
app.config['SESSION_COOKIE_SECURE'] = True  # Em produção
```

### **Rate Limiting**

```python
limiter = Limiter(
    app=app,
    default_limits=["200 per day", "50 per hour"]
)
```

### **Variáveis Sensíveis**

⚠️ **NUNCA** commitar:
- `SECRET_KEY`
- `DATABASE_URL`
- `SENTRY_DSN`
- Senhas ou tokens

✅ Usar Railway Variables

---

## 📊 Monitoramento

### **Railway Metrics**

1. Railway Dashboard → Metrics
2. Acompanhar:
   - CPU Usage
   - Memory Usage
   - Network Traffic
   - Response Times

### **Logs**

```bash
# Via Railway CLI
railway logs

# Ou no Dashboard → Deployments → View Logs
```

### **Sentry (Opcional)**

```python
# Já configurado em web_server.py
SENTRY_DSN = os.getenv('SENTRY_DSN')
init_sentry(dsn=SENTRY_DSN, environment='production')
```

Adicionar `SENTRY_DSN` nas variáveis do Railway.

---

## 🐛 Troubleshooting

### **Problema: Deploy falha com "Module not found"**

**Causa:** Dependência faltando em `requirements_web.txt`

**Solução:**
```bash
# Localmente, verificar imports
pip freeze > requirements_check.txt
# Comparar com requirements_web.txt
# Adicionar dependências faltantes
git commit -am "fix: adicionar dependências"
git push
```

---

### **Problema: "DATABASE_URL not found"**

**Causa:** PostgreSQL plugin não conectado

**Solução:**
1. Railway Dashboard → Project
2. Adicionar PostgreSQL Plugin
3. Conectar ao serviço web
4. Redeploy

---

### **Problema: Índices não estão criando**

**Causa:** Migration não executada

**Solução:**
```bash
# Via API
curl -X POST https://[APP].railway.app/api/debug/create-performance-indexes

# Ou via Railway Shell
railway shell
python
>>> import migration_performance_indexes
>>> migration_performance_indexes.create_indexes()
```

---

### **Problema: App fica lento após algum tempo**

**Causa:** Cache desatualizado ou queries sem índices

**Solução:**
```python
# Limpar cache via Python shell
from app.utils.cache_helper import clear_all_cache
clear_all_cache()

# Ou reiniciar app no Railway Dashboard
```

---

### **Problema: "502 Bad Gateway"**

**Causa:** App não iniciou corretamente

**Solução:**
1. Verificar logs: `railway logs`
2. Verificar se Gunicorn está rodando
3. Verificar PORT: `echo $PORT` (Railway define automaticamente)
4. Verificar Procfile

---

### **Problema: CSRF Token inválido**

**Causa:** Sessão expirou ou domínio incorreto

**Solução:**
```python
# Verificar configuração em web_server.py
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # Em produção

# Limpar cookies do navegador
# Fazer login novamente
```

---

## 📈 Escalabilidade

### **Aumentar Workers Gunicorn**

Editar `Procfile`:
```
web: gunicorn web_server:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

**Fórmula:** `workers = (2 x CPU cores) + 1`

### **Upgrade de Plano Railway**

- **Starter ($5/mês)**: 512 MB RAM, 1 GB disco
- **Developer ($20/mês)**: 8 GB RAM, 100 GB disco
- **Team ($20/user/mês)**: Ilimitado

### **Cache com Redis**

```python
# Futuro: migrar de cache em memória para Redis
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL')
```

---

## 🔄 CI/CD

### **Deploy Automático**

Railway detecta pushes no branch `main` automaticamente.

```bash
# Workflow
git add .
git commit -m "feat: nova funcionalidade"
git push origin main
# Railway inicia deploy (~2-3 min)
```

### **Deploy Manual**

```bash
# Via Railway CLI
railway up

# Ou no Dashboard
# Deployments → Redeploy
```

### **Rollback**

```bash
# Via Railway Dashboard
# Deployments → [versão anterior] → Redeploy

# Ou via Git
git revert HEAD
git push origin main
```

---

## ✅ Checklist de Deploy

- [ ] PostgreSQL plugin adicionado
- [ ] `DATABASE_URL` configurado
- [ ] `SECRET_KEY` gerado e configurado
- [ ] `RAILWAY_ENVIRONMENT=production`
- [ ] `requirements_web.txt` atualizado
- [ ] Procfile configurado
- [ ] Push para main branch
- [ ] Aguardar deploy (2-3 min)
- [ ] Acessar URL do Railway
- [ ] Testar login/autenticação
- [ ] Executar migration de índices
- [ ] Verificar logs para erros
- [ ] Testar performance dos relatórios
- [ ] Configurar domínio customizado (opcional)
- [ ] Configurar Sentry (opcional)

---

## 📞 Suporte

### **Railway**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### **Projeto**
- Issues: GitHub Issues
- Docs: Este repositório

---

## 🎉 Deploy de Sucesso!

Após seguir este guia, seu sistema estará:
- ✅ Rodando em produção no Railway
- ✅ Com HTTPS automático
- ✅ Com 36 índices otimizados
- ✅ Com compressão gzip ativa
- ✅ Com logs estruturados
- ✅ Pronto para escalar

**Próximos passos:**
1. Monitorar métricas
2. Configurar backups do PostgreSQL
3. Configurar alertas (Sentry/PagerDuty)
4. Documentar processos internos

---

**Criado por:** Time de DevOps DWM  
**Última atualização:** 20/01/2026  
**Versão:** 2.0

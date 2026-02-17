# 🚀 GUIA COMPLETO DE DEPLOY - Railway

**Data:** 17/02/2026  
**Chave gerada:** `tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=`

---

## ✅ **PASSO 1: Adicionar FERNET_KEY no ERP Financeiro**

### 1.1 Acessar o serviço
1. Acesse **Railway Dashboard**
2. Selecione o serviço **"ERP Financeiro"** (sistemafinanceirodwm-production-c3e6)

### 1.2 Adicionar variável
1. Clique em **Settings** (engrenagem)
2. Vá em **Variables**
3. Clique em **+ New Variable**
4. Cole isto:

```
Name: FERNET_KEY
Value: tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=
```

5. Clique em **Add**
6. O serviço vai **reiniciar automaticamente**

### 1.3 Verificar
- Aguarde 30-60 segundos
- Status deve ficar **verde** (Active)
- Se der erro, veja os logs

---

## ✅ **PASSO 2: Criar serviço "Busca de Notas"**

### 2.1 Criar novo serviço
1. No Railway Dashboard, clique em **+ New**
2. Selecione **GitHub Repo**
3. Escolha o repositório: **`EduardoSouza-tech/Sistema_financeiro_dwm`**
4. Nome do serviço: **`Busca de Notas`**
5. Clique em **Deploy**

### 2.2 Configurar Build
1. No serviço "Busca de Notas", clique em **Settings**
2. Vá em **Build** → **Custom Build Command**
3. Cole:
```
pip install -r requirements_nfe.txt
```
4. Clique em **Update**

### 2.3 Configurar Deploy
1. Ainda em **Settings**, vá em **Deploy**
2. Clique em **Custom Start Command**
3. Cole:
```
gunicorn app_nfe:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```
4. Clique em **Update**

### 2.4 Configurar Healthcheck
1. Ainda em **Deploy**, role até **Healthcheck Path**
2. Cole:
```
/health
```
3. Clique em **Update**

### 2.5 Adicionar Variáveis de Ambiente
1. Vá em **Variables**
2. Clique em **+ New Variable** para cada uma:

```plaintext
DATABASE_URL = ${{Postgres.DATABASE_URL}}
```
(Salve, depois adicione a próxima)

```plaintext
SECRET_KEY = 1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45
```

```plaintext
FLASK_ENV = production
```

```plaintext
FERNET_KEY = tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=
```

```plaintext
FRONTEND_URL = https://sistemafinanceirodwm-production-c3e6.up.railway.app
```

```plaintext
LOG_LEVEL = INFO
```

### 2.6 Aguardar Deploy
- O Railway vai detectar automaticamente o código
- Build vai rodar (2-3 minutos)
- Status deve ficar **verde** (Active)

### 2.7 Testar Health Check
1. Vá em **Settings** → **Networking** → **Public Networking**
2. Copie o domínio (ex: `busca-de-notas-xyz.up.railway.app`)
3. Abra no navegador: `https://busca-de-notas-xyz.up.railway.app/health`
4. Deve retornar:
```json
{
  "status": "healthy",
  "service": "busca-nfe-cte",
  "timestamp": "2026-02-17T..."
}
```

---

## ✅ **PASSO 3: Criar serviço "NFS-e Exportação"**

### 3.1 Criar novo serviço
1. No Railway Dashboard, clique em **+ New**
2. Selecione **GitHub Repo**
3. Escolha o repositório: **`EduardoSouza-tech/Sistema_financeiro_dwm`**
4. Nome do serviço: **`NFS-e Exportação`**
5. Clique em **Deploy**

### 3.2 Configurar Build
1. No serviço "NFS-e Exportação", clique em **Settings**
2. Vá em **Build** → **Custom Build Command**
3. Cole:
```
pip install -r requirements_nfse.txt
```
4. Clique em **Update**

### 3.3 Configurar Deploy
1. Ainda em **Settings**, vá em **Deploy**
2. Clique em **Custom Start Command**
3. Cole:
```
gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```
4. Clique em **Update**

### 3.4 Configurar Healthcheck
1. Ainda em **Deploy**, role até **Healthcheck Path**
2. Cole:
```
/health
```
3. Clique em **Update**

### 3.5 Adicionar Variáveis de Ambiente
1. Vá em **Variables**
2. Clique em **+ New Variable** para cada uma:

```plaintext
DATABASE_URL = ${{Postgres.DATABASE_URL}}
```

```plaintext
SECRET_KEY = 1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45
```

```plaintext
FLASK_ENV = production
```

```plaintext
FRONTEND_URL = https://sistemafinanceirodwm-production-c3e6.up.railway.app
```

```plaintext
LOG_LEVEL = INFO
```

### 3.6 Aguardar Deploy
- Build vai rodar (2-3 minutos)
- Status deve ficar **verde** (Active)

### 3.7 Testar Health Check
1. Vá em **Settings** → **Networking** → **Public Networking**
2. Copie o domínio (ex: `nfs-e-exportacao-xyz.up.railway.app`)
3. Abra no navegador: `https://nfs-e-exportacao-xyz.up.railway.app/health`
4. Deve retornar:
```json
{
  "status": "healthy",
  "service": "nfse-consulta",
  "timestamp": "2026-02-17T..."
}
```

---

## ✅ **PASSO 4: Verificar todos os serviços**

### 4.1 Status dos Serviços

Verifique se todos estão **verdes** (Active):

| Serviço | Status | URL Health Check |
|---------|--------|------------------|
| **ERP Financeiro** | 🟢 | https://sistemafinanceirodwm-production-c3e6.up.railway.app/ |
| **Busca de Notas** | 🟢 | https://[seu-dominio].up.railway.app/health |
| **NFS-e Exportação** | 🟢 | https://[seu-dominio].up.railway.app/health |
| **Postgres** | 🟢 | (interno) |

### 4.2 Logs
Se algum serviço estiver com erro:
1. Clique no serviço
2. Vá em **Deployments** → último deploy
3. Clique em **View Logs**
4. Procure por `ERROR` ou `FAIL`

---

## ✅ **PASSO 5: Integrar Frontend com APIs**

### 5.1 URLs dos microserviços

Anote as URLs dos serviços (Settings → Networking → Public Networking):

```javascript
// Configurar no frontend do ERP
const API_URLS = {
    erp: 'https://sistemafinanceirodwm-production-c3e6.up.railway.app',
    nfe: 'https://busca-de-notas-[xyz].up.railway.app',
    nfse: 'https://nfs-e-exportacao-[xyz].up.railway.app'
};
```

### 5.2 Exemplo de chamada API

```javascript
// Buscar NF-e
async function buscarNFe() {
    const response = await fetch(`${API_URLS.nfe}/api/certificados`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Empresa-ID': empresaId
        }
    });
    
    const data = await response.json();
    console.log(data);
}

// Buscar NFS-e
async function buscarNFSe() {
    const response = await fetch(`${API_URLS.nfse}/api/nfse/config`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Empresa-ID': empresaId
        }
    });
    
    const data = await response.json();
    console.log(data);
}
```

---

## 🔍 **TROUBLESHOOTING**

### Erro: "Build failed"
**Causa:** Arquivo requirements incorreto  
**Solução:** 
- Verifique se o Build Command está correto
- `requirements_nfe.txt` para Busca de Notas
- `requirements_nfse.txt` para NFS-e Exportação

### Erro: "DATABASE_URL not configured"
**Causa:** Variável não está referenciando o Postgres  
**Solução:** Use exatamente: `${{Postgres.DATABASE_URL}}`

### Erro: "FERNET_KEY not configured"
**Causa:** Falta a chave (obrigatória para Busca de Notas)  
**Solução:** Adicione: `tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=`

### Erro: "ModuleNotFoundError"
**Causa:** Dependências não instaladas  
**Solução:** 
- Verifique o Build Command
- Veja os logs do build
- Confirme que o arquivo requirements existe

### Health check retorna 503
**Causa:** Serviço não consegue conectar ao banco  
**Solução:**
- Verifique DATABASE_URL
- Confirme que Postgres está rodando
- Veja logs do serviço

---

## 📊 **ARQUITETURA FINAL**

```
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Railway)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │    ERP    │     │   Busca   │     │   NFS-e   │
    │ Financeiro│     │  de Notas │     │Exportação │
    │   (main)  │     │  (NF-e)   │     │  (NFS-e)  │
    └───────────┘     └───────────┘     └───────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
                            │
                     ┌──────▼──────┐
                     │   Frontend  │
                     │  (Browser)  │
                     └─────────────┘
```

---

## ✅ **CHECKLIST FINAL**

- [ ] FERNET_KEY adicionada no ERP Financeiro
- [ ] ERP Financeiro reiniciou com sucesso
- [ ] Serviço "Busca de Notas" criado
- [ ] Build configurado (requirements_nfe.txt)
- [ ] Deploy configurado (app_nfe.py)
- [ ] Variáveis adicionadas (6 variáveis)
- [ ] Health check OK (GET /health)
- [ ] Serviço "NFS-e Exportação" criado
- [ ] Build configurado (requirements_nfse.txt)
- [ ] Deploy configurado (app_nfse.py)
- [ ] Variáveis adicionadas (5 variáveis)
- [ ] Health check OK (GET /health)
- [ ] URLs anotadas para frontend
- [ ] Teste de integração realizado

---

## 🎯 **PRÓXIMOS PASSOS**

1. **Certificados Digitais:**
   - Upload de certificado A1 (.pfx) no Busca de Notas
   - Testar busca em homologação

2. **Municípios NFS-e:**
   - Configurar município no NFS-e Exportação
   - Testar conexão com webservice
   - Buscar notas de teste

3. **Dashboard:**
   - Criar páginas no frontend para visualização
   - Gráficos de documentos fiscais
   - Exportação de relatórios

---

**🎉 Deploy completo! Sistema em produção com 3 microserviços!**

---

**Documentação completa:**  
- `README_MICROSERVICO_NFE.md` - Busca de Notas  
- `README_MICROSERVICO_NFSE.md` - NFS-e Exportação  
- `RAILWAY_VARIAVEIS.md` - Todas as variáveis  
- `DEPLOY_NFE_CTE.md` - Deploy NF-e específico  

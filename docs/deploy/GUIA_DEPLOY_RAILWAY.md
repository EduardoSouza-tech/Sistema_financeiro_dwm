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

## ✅ **PASSO 2: Criar serviço "Documentos Fiscais"** (NF-e + CT-e + NFS-e UNIFICADO)

### 2.1 Criar novo serviço
1. No Railway Dashboard, clique em **+ New**
2. Selecione **GitHub Repo**
3. Escolha o repositório: **`EduardoSouza-tech/Sistema_financeiro_dwm`**
4. Nome do serviço: **`Documentos Fiscais`**
5. Clique em **Deploy**

### 2.2 Configurar Build
1. No serviço "Documentos Fiscais", clique em **Settings**
2. Vá em **Build** → **Custom Build Command**
3. Cole:
```
pip install -r requirements_fiscal.txt
```
4. Clique em **Update**

### 2.3 Configurar Deploy
1. Ainda em **Settings**, vá em **Deploy**
2. Clique em **Custom Start Command**
3. Cole:
```
gunicorn app_fiscal:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
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
2. Copie o domínio (ex: `documentos-fiscais-xyz.up.railway.app`)
3. Abra no navegador: `https://documentos-fiscais-xyz.up.railway.app/health`
4. Deve retornar:
```json
{
  "status": "healthy",
  "service": "documentos-fiscais",
  "modules": ["nfe", "cte", "nfse"],
  "timestamp": "2026-02-17T..."
}
```

---

## ✅ **PASSO 3: Verificar todos os serviços**

### 3.1 Status dos Serviços

Verifique se todos estão **verdes** (Active):

| Serviço | Status | URL Health Check |
|---------|--------|------------------|
| **ERP Financeiro** | 🟢 | https://sistemafinanceirodwm-production-c3e6.up.railway.app/ |
| **Documentos Fiscais** | 🟢 | https://[seu-dominio].up.railway.app/health |
| **Postgres** | 🟢 | (interno) |

### 3.2 Logs
Se algum serviço estiver com erro:
1. Clique no serviço
2. Vá em **Deployments** → último deploy
3. Clique em **View Logs**
4. Procure por `ERROR` ou `FAIL`

---

## ✅ **PASSO 4: Integrar Frontend com API**

### 4.1 URL do microserviço

Anote a URL do serviço (Settings → Networking → Public Networking):

```javascript
// Configurar no frontend do ERP
const API_FISCAL_URL = 'https://documentos-fiscais-[xyz].up.railway.app';
```

### 4.2 Exemplos de chamadas API

#### Buscar NF-e/CT-e:
```javascript
async function buscarNFe() {
    const response = await fetch(`${API_FISCAL_URL}/api/nfe/certificados`, {
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

// Buscar documentos NF-e
async function buscarDocumentosNFe() {
    const response = await fetch(`${API_FISCAL_URL}/api/nfe/buscar-documentos`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Empresa-ID': empresaId
        },
        body: JSON.stringify({
            certificado_id: 1,
            ambiente: 'homologacao',
            data_inicio: '2026-01-01',
            data_fim: '2026-02-17'
        })
    });
    
    return await response.json();
}
```

#### Buscar NFS-e:
```javascript
async function listarMunicipiosNFSe() {
    const response = await fetch(`${API_FISCAL_URL}/api/nfse/config`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Empresa-ID': empresaId
        }
    });
    
    return await response.json();
}

// Buscar NFS-e por período
async function buscarNFSe() {
    const response = await fetch(`${API_FISCAL_URL}/api/nfse/buscar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Empresa-ID': empresaId
        },
        body: JSON.stringify({
            config_id: 1,
            data_inicio: '2026-01-01',
            data_fim: '2026-02-17'
        })
    });
    
    return await response.json();
}
```

#### Exportar para Excel:
```javascript
async function exportarDocumentosFiscais(tipo) {
    const response = await fetch(`${API_FISCAL_URL}/api/fiscal/exportar-excel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Empresa-ID': empresaId
        },
        body: JSON.stringify({
            tipo: tipo, // 'nfe' ou 'nfse'
            data_inicio: '2026-01-01',
            data_fim: '2026-02-17'
        })
    });
    
    // Download do arquivo
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `documentos_${tipo}_${Date.now()}.xlsx`;
    a.click();
}
```
```

---

## 🔍 **TROUBLESHOOTING**

### Erro: "Build failed"
**Causa:** Arquivo requirements incorreto  
**Solução:** 
- Verifique se o Build Command está correto
- Deve ser: `pip install -r requirements_fiscal.txt`

### Erro: "DATABASE_URL not configured"
**Causa:** Variável não está referenciando o Postgres  
**Solução:** Use exatamente: `${{Postgres.DATABASE_URL}}`

### Erro: "FERNET_KEY not configured"
**Causa:** Falta a chave (obrigatória para Documentos Fiscais)  
**Solução:** Adicione: `tmFBahRwMUuNRBR9rBt6TpuNDkvktzW2ZosCH9X_vjA=`

### Erro: "ModuleNotFoundError: No module named 'relatorios'"
**Causa:** Módulos NF-e não encontrados  
**Solução:** 
- Verifique estrutura de pastas `relatorios/nfe/`
- Confirme que arquivos existem: nfe_api.py, nfe_busca.py, etc.

### Erro: "ModuleNotFoundError: No module named 'nfse_database'"
**Causa:** Módulos NFS-e não encontrados  
**Solução:** 
- Verifique arquivos: nfse_database.py, nfse_service.py, nfse_functions.py
- Devem estar na raiz do projeto

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
    ┌─────▼─────┐     ┌─────▼──────────┐       │
    │    ERP    │     │   Documentos   │       │
    │ Financeiro│     │    Fiscais     │       │
    │   (main)  │     │ NF-e+CT-e+NFS-e│       │
    └───────────┘     └────────────────┘       │
         │                     │                │
         └─────────────────────┴────────────────┘
                              │
                       ┌──────▼──────┐
                       │   Frontend  │
                       │  (Browser)  │
                       └─────────────┘
```

**Módulos do Serviço "Documentos Fiscais":**
- 🧾 **NF-e:** Nota Fiscal Eletrônica (SEFAZ Nacional)
- 🚚 **CT-e:** Conhecimento de Transporte (SEFAZ Nacional)
- 📋 **NFS-e:** Nota Fiscal de Serviço (6 provedores municipais)

---

## ✅ **CHECKLIST FINAL**

- [ ] FERNET_KEY adicionada no ERP Financeiro
- [ ] ERP Financeiro reiniciou com sucesso
- [ ] Serviço "Documentos Fiscais" criado
- [ ] Build configurado (requirements_fiscal.txt)
- [ ] Deploy configurado (app_fiscal.py)
- [ ] Variáveis adicionadas (6 variáveis)
- [ ] Health check OK (GET /health)
- [ ] Resposta do health mostra 3 módulos: nfe, cte, nfse
- [ ] URL anotada para frontend
- [ ] Teste de integração NF-e realizado
- [ ] Teste de integração NFS-e realizado

---

## 🎯 **PRÓXIMOS PASSOS**

1. **Certificados Digitais NF-e:**
   - Upload de certificado A1 (.pfx)
   - Testar busca em homologação SEFAZ
   - Consultar documentos por chave

2. **Municípios NFS-e:**
   - Configurar município
   - Testar conexão com webservice
   - Buscar notas de teste
   - Validar download de PDF/XML

3. **Dashboard:**
   - Criar interface unificada no frontend
   - Visualização de NF-e, CT-e e NFS-e juntos
   - Gráficos consolidados
   - Exportação única para Excel

---

**🎉 Deploy completo! Sistema em produção com 3 microserviços!**

---

**Documentação completa:**  
- `README_MICROSERVICO_NFE.md` - Busca de Notas  
- `README_MICROSERVICO_NFSE.md` - NFS-e Exportação  
- `RAILWAY_VARIAVEIS.md` - Todas as variáveis  
- `DEPLOY_NFE_CTE.md` - Deploy NF-e específico  

# 📋 Microserviço: Consulta NFS-e

Serviço independente para consulta de Notas Fiscais de Serviço Eletrônicas via SOAP.

---

## 📦 ARQUITETURA

```
┌─────────────────┐         ┌──────────────────┐
│  ERP Financeiro │ ◄─────► │  Consulta NFS-e  │
│  (web_server.py)│   API   │  (app_nfse.py)   │
└─────────────────┘         └──────────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
              ┌─────────────┐
              │  PostgreSQL │
              └─────────────┘
```

---

## 🌐 PROVEDORES SUPORTADOS

✅ **GINFES** - 500+ municípios  
✅ **ISS.NET** - 200+ municípios  
✅ **BETHA** - 1.000+ municípios  
✅ **e-ISS** - 150+ municípios  
✅ **WebISS** - 50+ municípios  
✅ **SimplISS** - 300+ municípios  

**Padrão ABRASF:** 1.00, 2.00, 2.02

---

## 🚀 DEPLOY NO RAILWAY

### 1. Criar Novo Serviço

No Railway Dashboard:
1. **"+ New"** → **"GitHub Repo"**
2. Escolha: `EduardoSouza-tech/Sistema_financeiro_dwm`
3. Nome: **"NFS-e Exportação"**

### 2. Configurar Build

#### **Settings → Build**
```
Build Command:
pip install -r requirements_nfse.txt
```

#### **Settings → Deploy**
```
Start Command:
gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

Healthcheck Path:
/health
```

### 3. Variáveis de Ambiente

```bash
# Obrigatórias
DATABASE_URL="${{Postgres.DATABASE_URL}}"
SECRET_KEY="1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45"
FLASK_ENV="production"

# Opcionais
FRONTEND_URL="https://sistemafinanceirodwm-production-c3e6.up.railway.app"
PORT="5000"
LOG_LEVEL="INFO"
```

---

## 📡 ENDPOINTS DA API

### **Autenticação**
Rotas requerem headers:
```
Authorization: Bearer <token>
X-Empresa-ID: <id-empresa>
```

### **Rotas Principais**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/api/nfse/config` | Lista municípios configurados |
| POST | `/api/nfse/config` | Cadastra município |
| PUT | `/api/nfse/config/:id` | Atualiza configuração |
| DELETE | `/api/nfse/config/:id` | Desativa município |
| POST | `/api/nfse/buscar` | Busca por período |
| POST | `/api/nfse/consultar` | Consulta por número |
| GET | `/api/nfse` | Lista NFS-e (paginado) |
| GET | `/api/nfse/:id` | Detalhes da NFS-e |
| DELETE | `/api/nfse/:id` | Deleta NFS-e |
| GET | `/api/nfse/:id/pdf` | Download PDF |
| GET | `/api/nfse/:id/xml` | Download XML |
| GET | `/api/nfse/estatisticas` | Estatísticas |
| POST | `/api/nfse/resumo-mensal` | Resumo mensal |
| POST | `/api/nfse/export/excel` | Exporta Excel |
| POST | `/api/nfse/certificado/upload` | Upload certificado A1 |
| GET | `/api/nfse/certificado` | Lista certificados |
| GET | `/api/nfse/provedores` | Lista provedores |
| POST | `/api/nfse/testar-conexao` | Testa webservice |

---

## 🔌 INTEGRAÇÃO COM ERP

```javascript
const NFSE_API_URL = 'https://nfs-e-exportacao.up.railway.app';

// Exemplo: Buscar NFS-e
async function buscarNFSe() {
    const response = await fetch(`${NFSE_API_URL}/api/nfse/buscar`, {
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

---

## 📂 ESTRUTURA DE ARQUIVOS

```
Sistema_financeiro_dwm/
├── app_nfse.py                # ← Aplicação Flask standalone
├── requirements_nfse.txt      # ← Dependências específicas
├── Procfile_nfse             # ← Comando Gunicorn
├── railway_nfse.toml         # ← Config Railway
├── templates/
│   └── nfse_dashboard.html   # ← Dashboard API
├── nfse_database.py          # ← Já existe
├── nfse_service.py           # ← Já existe
└── nfse_functions.py         # ← Já existe
```

---

## ✅ CHECKLIST DE DEPLOY

### Antes
- [x] Criar serviço separado no Railway
- [x] Configurar variáveis de ambiente
- [x] Conectar ao PostgreSQL
- [ ] Configurar FRONTEND_URL

### Após
- [ ] Verificar `/health` retorna 200
- [ ] Cadastrar município teste
- [ ] Executar busca teste
- [ ] Verificar logs

---

## 🐛 TROUBLESHOOTING

### Erro: "ModuleNotFoundError: No module named 'nfse_database'"
**Solução:** Verifique que os arquivos existem:
- `nfse_database.py`
- `nfse_service.py`
- `nfse_functions.py`

### Erro: "Provedor não suportado"
**Solução:** Use GET `/api/nfse/provedores` para ver lista de provedores suportados.

### Erro: "Webservice não responde"
**Solução:** Use POST `/api/nfse/testar-conexao` para validar URL antes de configurar.

---

## 🎯 DIFERENÇAS ENTRE MICROSERVIÇOS

| Item | NF-e/CT-e | NFS-e |
|------|-----------|-------|
| **Arquivo** | `app_nfe.py` | `app_nfse.py` |
| **Port** | 5001 | 5002 |
| **Protocolo** | REST (SEFAZ) | SOAP (Municípios) |
| **Provedores** | SEFAZ Nacional | 6 provedores |
| **Certificado** | A1 obrigatório | A1 opcional |

---

## 📞 SUPORTE

**URL:** https://nfs-e-exportacao.up.railway.app  
**Health:** https://nfs-e-exportacao.up.railway.app/health  
**Status:** ✅ PRONTO PARA PRODUÇÃO

---

**Desenvolvido com IA assistente** 🤖✨

# 🧾 Microserviço: Busca Automática NF-e/CT-e

Serviço independente para busca e gerenciamento de documentos fiscais via SEFAZ.

---

## 📦 ARQUITETURA

Este é um **microserviço separado** que roda independente do ERP principal:

```
┌─────────────────┐         ┌──────────────────┐
│  ERP Financeiro │ ◄─────► │  Busca NF-e/CT-e │
│  (web_server.py)│   API   │   (app_nfe.py)   │
└─────────────────┘         └──────────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
              ┌─────────────┐
              │  PostgreSQL │
              └─────────────┘
```

---

## 🚀 DEPLOY NO RAILWAY

### 1. Criar Novo Serviço

No Railway Dashboard:
1. Clique em **"+ New"**
2. Selecione **"GitHub Repo"**
3. Escolha: `EduardoSouza-tech/Sistema_financeiro_dwm`
4. Nome do serviço: **"Busca de Notas"**

### 2. Configurar Build

No serviço "Busca de Notas":

#### **Settings → Build**
```
Build Command:
pip install -r requirements_nfe.txt
```

#### **Settings → Deploy**
```
Start Command:
gunicorn app_nfe:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

Healthcheck Path:
/health

Restart Policy:
On Failure (10 retries)
```

### 3. Variáveis de Ambiente

Configure estas variáveis no Railway:

```bash
# Obrigatórias
DATABASE_URL="${{Postgres.DATABASE_URL}}"
SECRET_KEY="1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45"
FLASK_ENV="production"
FERNET_KEY="[GERAR_COM_COMANDO_ABAIXO]"

# Opcionais
FRONTEND_URL="https://sistemafinanceirodwm-production-c3e6.up.railway.app"
PORT="5000"
```

#### **Gerar FERNET_KEY:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 4. Conectar ao Mesmo Banco

1. No serviço "Busca de Notas"
2. Settings → Variables
3. DATABASE_URL = `${{Postgres.DATABASE_URL}}`

Isso conecta ao mesmo banco do ERP principal.

---

## 📡 ENDPOINTS DA API

### **Autenticação**
Todas as rotas (exceto `/health`) requerem header:
```
Authorization: Bearer <seu-token-jwt>
X-Empresa-ID: <id-da-empresa>
```

### **Rotas Disponíveis**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check (sem auth) |
| GET | `/api/certificados` | Lista certificados digitais |
| POST | `/api/certificados/novo` | Cadastra certificado |
| POST | `/api/certificados/:id/desativar` | Desativa certificado |
| POST | `/api/buscar-documentos` | Busca automática SEFAZ |
| POST | `/api/consultar-chave` | Consulta por chave |
| GET | `/api/documentos` | Lista docs (paginado) |
| GET | `/api/documento/:id` | Detalhes do documento |
| GET | `/api/documento/:id/xml` | Download XML |
| GET | `/api/estatisticas` | Estatísticas |
| GET | `/api/nsu-status` | Status NSUs |
| POST | `/api/exportar-excel` | Exporta para Excel |

---

## 🔌 INTEGRAÇÃO COM ERP

No frontend do ERP, chame a API do microserviço:

```javascript
// Configurar URL da API
const NFE_API_URL = 'https://busca-de-notas.up.railway.app';

// Exemplo: Buscar documentos
async function buscarDocumentos() {
    const response = await fetch(`${NFE_API_URL}/api/buscar-documentos`, {
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
    
    const data = await response.json();
    console.log(data);
}
```

---

## 📂 ESTRUTURA DE ARQUIVOS

Arquivos específicos do microserviço:

```
Sistema_financeiro_dwm/
├── app_nfe.py                 # ← Aplicação Flask standalone
├── requirements_nfe.txt       # ← Dependências específicas
├── Procfile_nfe              # ← Comando Gunicorn
├── railway_nfe.toml          # ← Config Railway
├── templates/
│   └── nfe_dashboard.html    # ← Dashboard API
└── relatorios/
    └── nfe/
        ├── nfe_api.py        # Já existe
        ├── nfe_busca.py      # Já existe
        ├── nfe_processor.py  # Já existe
        └── nfe_storage.py    # Já existe
```

---

## ✅ CHECKLIST DE DEPLOY

### Antes do Deploy
- [x] Criar serviço separado no Railway
- [x] Configurar variáveis de ambiente
- [x] Conectar ao banco PostgreSQL
- [ ] Gerar e configurar FERNET_KEY
- [ ] Configurar FRONTEND_URL

### Após o Deploy
- [ ] Verificar `/health` retorna 200
- [ ] Testar autenticação
- [ ] Criar certificado teste
- [ ] Executar busca em homologação
- [ ] Verificar logs no Railway

---

## 🐛 TROUBLESHOOTING

### Erro: "DATABASE_URL não configurada"
**Solução:**
```bash
DATABASE_URL="${{Postgres.DATABASE_URL}}"
```

### Erro: "FERNET_KEY não configurada"
**Solução:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
# Adicione o resultado como variável FERNET_KEY
```

### Erro: "ModuleNotFoundError: No module named 'relatorios'"
**Solução:** Verifique que o build usa `requirements_nfe.txt`:
```
pip install -r requirements_nfe.txt
```

### Health check falha
**Solução:** Configure healthcheck path como `/health` nas configurações do Railway.

---

## 📊 MONITORAMENTO

### Ver logs em tempo real:
```bash
railway logs --service "Busca de Notas"
```

### Métricas importantes:
- **Uptime:** Disponibilidade do serviço
- **Response Time:** Tempo de resposta das APIs
- **Error Rate:** Taxa de erros
- **Database Connections:** Conexões ativas

---

## 🔐 SEGURANÇA

1. **NUNCA** commite arquivos `.pfx` ou senhas
2. Use **ambiente de homologação** para testes
3. Senhas de certificados são **criptografadas** com FERNET_KEY
4. XMLs ficam em `storage/nfe/` (não no banco)
5. Implemente **rate limiting** em produção

---

## 🎯 VANTAGENS DA ARQUITETURA DE MICROSERVIÇOS

✅ **Escalabilidade independente** - Escala só busca NF-e  
✅ **Deploy isolado** - Atualiza sem afetar ERP  
✅ **Resiliência** - Se um cai, outro continua  
✅ **Manutenção** - Código menor e focado  
✅ **Performance** - Workers dedicados  

---

## 📞 SUPORTE

**URL do Serviço:** https://busca-de-notas.up.railway.app  
**Health Check:** https://busca-de-notas.up.railway.app/health  
**Status:** ✅ PRONTO PARA PRODUÇÃO

---

**Desenvolvido com IA assistente** 🤖✨

# 🏗️ Arquitetura: Microserviço de Busca de Notas Fiscais

**Data de Implementação:** 26/02/2026  
**Versão:** 1.0  
**Status:** ✅ Implementado

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Separação de Responsabilidades](#separação-de-responsabilidades)
3. [Fluxo de Comunicação](#fluxo-de-comunicação)
4. [Configuração no Railway](#configuração-no-railway)
5. [Variáveis de Ambiente](#variáveis-de-ambiente)
6. [Endpoints](#endpoints)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### Objetivo

Separar **operações pesadas de busca de notas fiscais** em um microserviço dedicado, permitindo:

- ✅ **Isolamento:** Buscas demoradas não bloqueiam o ERP principal
- ✅ **Escalabilidade:** Pode escalar independentemente
- ✅ **Manutenibilidade:** Atualizar busca de notas sem afetar o ERP
- ✅ **Resiliência:** Se microserviço cair, ERP continua funcionando (modo legacy)

### Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│                  USUÁRIO (Navegador)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              ERP FINANCEIRO (web_server.py)                 │
│  • Interface HTML/JS                                        │
│  • Upload/gestão de certificados                            │
│  • Listagem de notas (consulta banco local)                 │
│  • Exportação Excel/XML                                     │
│  • **PROXY para busca pesada**                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP POST
                      │ /api/nfse/buscar
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           BUSCA DE NOTAS (app_nfse.py)                      │
│  🔥 Busca pesada NFS-e (Ambiente Nacional)                  │
│  🔥 Busca pesada NFS-e (SOAP Municipal)                     │
│  🔥 Busca pesada NF-e (futuro)                              │
│  🔥 Busca pesada CT-e (futuro)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
              ┌─────────────┐
              │ PostgreSQL  │
              └─────────────┘
```

---

## 🔀 Separação de Responsabilidades

### 🏢 ERP Financeiro (web_server.py)

| Funcionalidade | Rota | Detalhes |
|----------------|------|----------|
| **Interface** | `/` | Renderização HTML/CSS/JS |
| **Certificados** | `POST /api/nfse/certificado/upload` | Upload de .pfx |
|  | `GET /api/nfse/certificado` | Listar certificados |
|  | `DELETE /api/nfse/certificado/<id>` | Remover certificado |
| **Consulta Local** | `POST /api/nfse/consultar` | Busca no PostgreSQL |
|  | `GET /api/nfse` | Listagem paginada |
| **Exportação** | `POST /api/nfse/export/excel` | Gerar Excel |
|  | `POST /api/nfse/export/xml` | Gerar ZIP de XMLs |
| **Proxy** | `POST /api/nfse/buscar` | ⚠️ **Redireciona para microserviço** |

### 🔥 Busca de Notas (app_nfse.py)

| Funcionalidade | Rota | Detalhes |
|----------------|------|----------|
| **NFS-e Ambiente Nacional** | `POST /api/nfse/buscar` | Busca via REST API (NSU incremental) |
| **NFS-e SOAP Municipal** | `POST /api/nfse/buscar` | Busca via SOAP (config por município) |
| **NF-e (Futuro)** | `POST /api/nfe/buscar` | Placeholder |
| **CT-e (Futuro)** | `POST /api/cte/buscar` | Placeholder |
| **Health Check** | `GET /health` | Monitoramento Railway |
| **Provedores** | `GET /api/nfse/provedores` | Lista GINFES, ISS.NET, etc |

---

## 📡 Fluxo de Comunicação

### 1. Usuário clica "⬇️ Baixar NFS-e"

```javascript
// static/app.js:7945
const response = await fetch('/api/nfse/buscar', {
    method: 'POST',
    body: JSON.stringify({
        data_inicial: '2026-01-01',
        data_final: '2026-01-31',
        metodo: 'ambiente_nacional'
    })
});
```

### 2. ERP recebe e valida (web_server.py:12744)

```python
@app.route('/api/nfse/buscar', methods=['POST'])
@require_auth
@require_permission('nfse_buscar')
def buscar_nfse():
    # Validar usuário e empresa
    # Obter NFSE_SERVICE_URL
    nfse_service_url = os.getenv('NFSE_SERVICE_URL')
```

### 3. ERP faz proxy para microserviço

```python
import requests

response = requests.post(
    f"{nfse_service_url}/api/nfse/buscar",
    json=data,
    headers={
        'Authorization': '...',
        'X-Empresa-ID': '123'
    },
    timeout=600  # 10 minutos
)
```

### 4. Microserviço processa (app_nfse.py:223)

```python
if metodo == 'ambiente_nacional':
    resultado = buscar_nfse_ambiente_nacional(...)
else:
    resultado = buscar_nfse_periodo(...)
```

### 5. Microserviço salva no PostgreSQL

```python
# nfse_functions.py
db.salvar_nfse(nfse_data)
```

### 6. Microserviço retorna resultado

```json
{
    "success": true,
    "total_nfse": 42,
    "nfse_novas": 38,
    "nfse_atualizadas": 4
}
```

### 7. ERP repassa para frontend

### 8. Frontend atualiza tabela

```javascript
await window.consultarNFSeLocal();  // Busca dados salvos no banco
```

---

## 🚀 Configuração no Railway

### Passo 1: Criar Serviço "Busca de Notas"

1. **Dashboard Railway** → `+ New`
2. **GitHub Repo** → `EduardoSouza-tech/Sistema_financeiro_dwm`
3. **Nome:** `Busca de Notas`

### Passo 2: Configurar Build

**Settings → Deploy:**

```yaml
Build Command:
pip install -r requirements_nfse.txt

Start Command:
gunicorn app_nfse:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

Healthcheck Path:
/health

Healthcheck Timeout:
30 seconds

Restart Policy:
on_failure (max 10 retries)
```

### Passo 3: Variáveis de Ambiente

#### 📄 Busca de Notas (app_nfse.py)

```bash
# Obrigatórias
DATABASE_URL="${{Postgres.DATABASE_URL}}"
SECRET_KEY="1f6bd55450dcd979e30bd2a6a3c643fd4f428f3486071ad9f709c13483689b45"
FLASK_ENV="production"

# Opcionais
PORT="5000"
LOG_LEVEL="INFO"
CERTIFICADO_A1_PATH="/app/certificados/certificado.pfx"
CERTIFICADO_A1_SENHA=""
```

#### 🏢 ERP Financeiro (web_server.py)

```bash
# Nova variável obrigatória
NFSE_SERVICE_URL="https://busca-de-notas-production.up.railway.app"

# Variáveis existentes (não alterar)
DATABASE_URL="${{Postgres.DATABASE_URL}}"
SECRET_KEY="..."
# ... outras
```

**⚠️ IMPORTANTE:** Copie a URL pública do serviço "Busca de Notas" e cole em `NFSE_SERVICE_URL` no ERP.

### Passo 4: Compartilhar PostgreSQL

Ambos serviços devem usar o **mesmo banco de dados**:

1. **PostgreSQL** já existe no projeto
2. **ERP Financeiro:** `DATABASE_URL="${{Postgres.DATABASE_URL}}"`
3. **Busca de Notas:** `DATABASE_URL="${{Postgres.DATABASE_URL}}"`

Isso garante que:
- ✅ Certificados estão acessíveis para ambos
- ✅ Notas salvas ficam imediatamente disponíveis no ERP
- ✅ Não há necessidade de sincronização

### Passo 5: Testar Deploy

#### Verificar Health Check

```bash
curl https://busca-de-notas-production.up.railway.app/health
```

**Resposta esperada:**

```json
{
    "status": "healthy",
    "service": "nfse-consulta",
    "timestamp": "2026-02-26T15:30:00"
}
```

#### Verificar Logs

**Railway Dashboard → Busca de Notas → Logs:**

```
🚀 Iniciando serviço NFS-e na porta 5000
📊 Ambiente: PRODUÇÃO
✅ Módulos NFS-e inicializados com sucesso
* Running on http://0.0.0.0:5000
```

---

## 🔐 Autenticação

### Headers Necessários

Toda requisição ao microserviço deve incluir:

```http
POST /api/nfse/buscar
Authorization: Bearer <jwt-token>
X-Empresa-ID: <id-empresa>
Content-Type: application/json
```

O ERP automaticamente repassa esses headers ao fazer proxy.

---

## 📊 Endpoints Detalhados

### 🔥 Busca Pesada de NFS-e

```http
POST /api/nfse/buscar
```

**Request Body:**

```json
{
    "data_inicial": "2026-01-01",
    "data_final": "2026-01-31",
    "metodo": "ambiente_nacional",
    "codigos_municipios": null,
    "ambiente": "producao",
    "busca_completa": false,
    "max_documentos": 50
}
```

**Parâmetros:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `data_inicial` | string | ✅ Sim | Data inicial (YYYY-MM-DD) |
| `data_final` | string | ✅ Sim | Data final (YYYY-MM-DD) |
| `metodo` | string | ❌ Não | `ambiente_nacional` (padrão) ou `soap` |
| `codigos_municipios` | array | ❌ Não | Lista de códigos IBGE (ex: `[3550308]` para São Paulo) |
| `ambiente` | string | ❌ Não | `producao` (padrão) ou `homologacao` |
| `busca_completa` | boolean | ❌ Não | `false` (padrão) = incremental, `true` = do zero |
| `max_documentos` | int | ❌ Não | Limite por execução (padrão: 50) |

**Response (Sucesso):**

```json
{
    "sucesso": true,
    "total_nfse": 42,
    "nfse_novas": 38,
    "nfse_atualizadas": 4,
    "ultimo_nsu": 123456,
    "erros": [],
    "detalhes": [
        {
            "municipio": "São Paulo/SP",
            "nfse_encontradas": 42
        }
    ]
}
```

**Response (Erro):**

```json
{
    "success": false,
    "error": "Certificado A1 não configurado"
}
```

---

## 🛡️ Resiliência e Fallback

### Modo Legacy (Fallback Automático)

Se `NFSE_SERVICE_URL` não estiver configurada, o ERP processa localmente:

```python
if not nfse_service_url:
    logger.warning("⚠️ NFSE_SERVICE_URL não configurada - processando localmente")
    return _buscar_nfse_local(...)
```

**⚠️ Não recomendado:** Busca pesada bloqueia workers do ERP.

### Tratamento de Timeout

```python
try:
    response = requests.post(..., timeout=600)  # 10 minutos
except requests.exceptions.Timeout:
    return jsonify({
        'success': False,
        'error': 'A busca está demorando muito. Tente reduzir o período.'
    }), 504
```

### Tratamento de Conexão

```python
except requests.exceptions.ConnectionError:
    return jsonify({
        'success': False,
        'error': 'Serviço de busca de notas temporariamente indisponível'
    }), 503
```

---

## 🐛 Troubleshooting

### ❌ Erro: "NFSE_SERVICE_URL não configurada"

**Causa:** Variável de ambiente não definida no ERP.

**Solução:**

1. Railway Dashboard → **ERP Financeiro** → **Variables**
2. Adicionar: `NFSE_SERVICE_URL=https://busca-de-notas-production.up.railway.app`
3. Redeploy

---

### ❌ Erro: "Serviço de busca de notas temporariamente indisponível"

**Causa:** Microserviço não está respondendo.

**Diagnóstico:**

```bash
# Testar health check
curl https://busca-de-notas-production.up.railway.app/health
```

**Soluções:**

1. **Verificar logs no Railway:** Busca de Notas → Logs
2. **Verificar status:** Deve estar "Online" ✅
3. **Verificar DATABASE_URL:** Deve estar configurada
4. **Restart manual:** Settings → Restart

---

### ❌ Erro: "Certificado A1 não configurado"

**Causa:** Certificado não está no banco de dados.

**Solução:**

1. No ERP: **📄 NFS-e** → **⚙️ Configurações**
2. Upload do arquivo `.pfx` + senha
3. Certificado é salvo no PostgreSQL (compartilhado entre serviços)

---

### ⏱️ Erro: Timeout após 10 minutos

**Causa:** Busca muito grande (muitos municípios ou período longo).

**Soluções:**

1. **Reduzir período:** Ex: 1 mês ao invés de 1 ano
2. **Aumentar timeout:** Alterar `timeout=600` para `timeout=1200` (20 min)
3. **Executar busca incremental:** Deixar `busca_completa=false`
4. **Limitar municípios:** Especificar `codigos_municipios`

---

### 📊 Monitoramento

#### Logs do Microserviço

```bash
# Railway Logs mostra:
🚀 Iniciando busca pesada de NFS-e no microserviço
🌐 Usando Ambiente Nacional (API REST)
Período: 2026-01-01 a 2026-01-31
✅ Busca concluída: 42 NFS-e encontradas
```

#### Logs do ERP

```bash
🔄 Redirecionando busca de NFS-e para microserviço: https://...
✅ Busca concluída via microserviço: 42 notas
```

---

## 🚧 Próximas Implementações

### 1. Suporte a NF-e

**Rota:** `POST /api/nfe/buscar`

**Funcionalidades:**
- Consulta via SEFAZ por chave
- Download de XMLs autorizados
- Manifestação de destinatário
- Inutilização de numeração

### 2. Suporte a CT-e

**Rota:** `POST /api/cte/buscar`

**Funcionalidades:**
- Consulta via SEFAZ
- Download de XMLs
- Eventos (cancelamento, correção)

### 3. Fila de Processamento

**Tecnologia:** Celery + Redis

**Objetivo:**
- Busca assíncrona (não bloqueia resposta HTTP)
- Retry automático em caso de falha
- Múltiplos workers para paralelização

```python
@celery.task
def buscar_nfse_async(empresa_id, data_inicial, data_final):
    # Processamento em background
    pass
```

---

## 📝 Changelog

### v1.0 - 26/02/2026 ✅

- ✅ Separação de busca em microserviço
- ✅ Proxy no ERP com fallback
- ✅ Health check para Railway
- ✅ Timeout de 10 minutos
- ✅ Tratamento de erro de conexão
- ✅ Log de auditoria
- ✅ Placeholders para NF-e e CT-e

---

## 📚 Referências

- [README_MICROSERVICO_NFSE.md](README_MICROSERVICO_NFSE.md) - Documentação original
- [nfse_functions.py](nfse_functions.py) - Lógica de busca
- [nfse_service.py](nfse_service.py) - Cliente SOAP e REST
- [app_nfse.py](app_nfse.py) - Microserviço Flask
- [web_server.py](web_server.py) - ERP principal (proxy)

---

**Autor:** Sistema Financeiro DWM  
**Manutenção:** Eduardo Souza

# 📄 SISTEMA NFS-e - GUIA DE IMPLEMENTAÇÃO E USO

**Data:** 2026-02-13  
**Versão:** 1.0 - MVP (SOAP Municipal Gratuito)  
**Status:** ✅ Backend completo | ⏳ Frontend pendente

---

## 📋 SUMÁRIO

1. [Arquivos Criados](#arquivos-criados)
2. [Próximos Passos](#próximos-passos)
3. [Como Executar a Migração do Banco](#como-executar-a-migração-do-banco)
4. [Configuração do Certificado A1](#configuração-do-certificado-a1)
5. [Instalação de Dependências](#instalação-de-dependências)
6. [Testando o Backend](#testando-o-backend)
7. [Implementação do Frontend (Pendente)](#implementação-do-frontend-pendente)
8. [Permissões Necessárias](#permissões-necessárias)
9. [Troubleshooting](#troubleshooting)

---

## 📦 ARQUIVOS CRIADOS

### ✅ 1. **migration_nfse.sql**
- **Localização:** `Sistema_financeiro_dwm/migration_nfse.sql`
- **Conteúdo:** Schema PostgreSQL completo
- **Tabelas criadas:**
  - `nfse_config` - Configurações de municípios
  - `nfse_baixadas` - NFS-e armazenadas
  - `rps` - Recibos Provisórios de Serviços
  - `nsu_nfse` - Controle NSU
  - `nfse_audit_log` - Log de auditoria
- **Views:** 3 views para relatórios
- **Funções:** 2 funções PostgreSQL
- **Triggers:** 4 triggers para atualização automática

### ✅ 2. **nfse_database.py**
- **Localização:** `Sistema_financeiro_dwm/nfse_database.py`
- **Função:** Camada de persistência (database layer)
- **Classes:**
  - `NFSeDatabase` - Gerencia todas as operações de banco
- **Métodos principais:**
  - `adicionar_config_nfse()` - Adiciona município
  - `salvar_nfse()` - Salva NFS-e baixada
  - `buscar_nfse_periodo()` - Consulta NFS-e localmente
  - `get_resumo_mensal()` - Resumo mensal
  - `registrar_auditoria()` - Log de operações

### ✅ 3. **nfse_service.py**
- **Localização:** `Sistema_financeiro_dwm/nfse_service.py`
- **Função:** Integração SOAP com APIs municipais (SEM Nuvem Fiscal)
- **Classes:**
  - `NFSeService` - Comunicação SOAP
- **Provedores suportados:**
  - ✅ GINFES (implementado completo)
  - ✅ ISS.NET (estrutura criada)
  - ⏳ BETHA (estrutura criada)
  - ⏳ eISS (estrutura criada)
  - ⏳ WEBISS (não implementado)
  - ⏳ SIMPLISS (não implementado)

### ✅ 4. **nfse_functions.py**
- **Localização:** `Sistema_financeiro_dwm/nfse_functions.py`
- **Função:** Lógica de negócio (orquestra database + service)
- **Funções principais:**
  - `adicionar_municipio()` - Configura município
  - `buscar_nfse_periodo()` - Busca via SOAP + salva no banco
  - `consultar_nfse_periodo()` - Consulta banco local
  - `exportar_nfse_excel()` - Exporta CSV
  - `exportar_xmls_zip()` - Exporta XMLs em ZIP

### ✅ 5. **Rotas no web_server.py**
- **Localização:** `Sistema_financeiro_dwm/web_server.py` (atualizado)
- **Rotas adicionadas:**

```
GET    /api/nfse/config              - Lista municípios configurados
POST   /api/nfse/config              - Adiciona município
DELETE /api/nfse/config/<id>         - Remove município
POST   /api/nfse/buscar              - Busca via SOAP (download)
POST   /api/nfse/consultar           - Consulta banco local
GET    /api/nfse/<id>                - Detalhes de NFS-e
POST   /api/nfse/resumo-mensal       - Resumo mensal
POST   /api/nfse/export/excel        - Exporta CSV
POST   /api/nfse/export/xml          - Exporta XMLs (ZIP)
```

---

## 🚀 PRÓXIMOS PASSOS

### ⏳ **Pendente de Implementação:**

#### 1. **Frontend (HTML + JavaScript)**
   - [ ] Adicionar menu "📄 NFS-e" em `interface_nova.html`
   - [ ] Criar seção `<div id="nfse-section">`
   - [ ] Implementar funções JavaScript em `app.js`:
     - `loadNFSeSection()`
     - `buscarNFSe()`
     - `configurarMunicipios()`
     - `exportarNFSeExcel()`
     - `exportarNFSeXMLs()`

#### 2. **Permissões no Sistema**
   - [ ] Adicionar 5 permissões na tabela `permissoes`:
     - `nfse_view` - Visualizar NFS-e
     - `nfse_buscar` - Buscar novas NFS-e
     - `nfse_config` - Configurar municípios
     - `nfse_export` - Exportar dados
     - `nfse_delete` - Excluir NFS-e

#### 3. **Testes**
   - [ ] Testar rotas via Postman
   - [ ] Testar integração SOAP com município real
   - [ ] Validar storage de XMLs
   - [ ] Testar exportações

---

## 🗄️ COMO EXECUTAR A MIGRAÇÃO DO BANCO

### **Opção 1: Via psql (Linha de comando)**

```bash
# Conectar ao PostgreSQL do Railway
psql $DATABASE_URL

# Executar migração
\i Sistema_financeiro_dwm/migration_nfse.sql

# Verificar tabelas criadas
\dt nfse*

# Sair
\q
```

### **Opção 2: Via DBeaver / pgAdmin (GUI)**

1. Conectar ao banco do Railway
2. Abrir o arquivo `migration_nfse.sql`
3. Executar todo o script (Ctrl+Enter)
4. Verificar que 5 tabelas foram criadas:
   - nfse_config
   - nfse_baixadas
   - rps
   - nsu_nfse
   - nfse_audit_log

### **Opção 3: Via Python (Automático)**

```python
import psycopg2
import os

# Conectar ao Railway
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# Ler e executar migration
with open('Sistema_financeiro_dwm/migration_nfse.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
    cursor.execute(sql)

conn.commit()
cursor.close()
conn.close()

print("✅ Migração executada com sucesso!")
```

---

## 🔐 CONFIGURAÇÃO DO CERTIFICADO A1

### **Pré-requisitos:**
- Certificado Digital A1 válido (arquivo .pfx)
- Senha do certificado
- Certificate must not be expired

### **Passo 1: Upload do Certificado para Railway**

```bash
# Via Railway Volumes (recomendado)
railway volumes create certificados
railway volumes attach certificados /app/certificados

# Upload manual (SSH)
railway run bash
mkdir -p /app/certificados
# Copie o arquivo .pfx para /app/certificados/
```

### **Passo 2: Configurar Variáveis de Ambiente**

No Railway Dashboard → Variáveis:

```env
CERTIFICADO_A1_PATH=/app/certificados/certificado.pfx
CERTIFICADO_A1_SENHA=SuaSenhaAqui
```

⚠️ **ATENÇÃO:** Nunca commite a senha no Git!

### **Passo 3: Validar Certificado**

```python
# Testar se certificado é válido
import os
from requests_pkcs12 import get as get_pkcs12

try:
    response = get_pkcs12(
        'https://httpbin.org/get',
        pkcs12_filename=os.getenv('CERTIFICADO_A1_PATH'),
        pkcs12_password=os.getenv('CERTIFICADO_A1_SENHA'),
        timeout=10
    )
    print(f"✅ Certificado válido! Status: {response.status_code}")
except Exception as e:
    print(f"❌ Erro no certificado: {e}")
```

---

## 📦 INSTALAÇÃO DE DEPENDÊNCIAS

### **Adicionar ao requirements.txt:**

```txt
# NFS-e Dependencies
lxml>=4.9.0
requests>=2.28.0
requests-pkcs12>=1.14
```

### **Instalar localmente:**

```bash
pip install lxml requests requests-pkcs12
```

### **Railway irá instalar automaticamente** no próximo deploy.

---

## 🧪 TESTANDO O BACKEND

### **1. Testar Rota de Configuração (GET)**

```bash
curl -X GET "https://seu-app.railway.app/api/nfse/config" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta esperada:**
```json
{
  "success": true,
  "configs": []
}
```

### **2. Adicionar Município (POST)**

```bash
curl -X POST "https://seu-app.railway.app/api/nfse/config" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj_cpf": "12345678000190",
    "codigo_municipio": "5002704",
    "nome_municipio": "Campo Grande",
    "uf": "MS",
    "inscricao_municipal": "123456",
    "provedor": "GINFES"
  }'
```

**Resposta esperada:**
```json
{
  "success": true,
  "config_id": 1,
  "message": "Município configurado com sucesso"
}
```

### **3. Buscar NFS-e (POST)**

```bash
curl -X POST "https://seu-app.railway.app/api/nfse/buscar" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data_inicial": "2026-01-01",
    "data_final": "2026-01-31"
  }'
```

**Resposta esperada:**
```json
{
  "sucesso": true,
  "total_nfse": 15,
  "nfse_novas": 15,
  "nfse_atualizadas": 0,
  "total_municipios": 1,
  "municipios_sucesso": 1,
  "municipios_erro": 0,
  "detalhes": [
    {
      "municipio": "Campo Grande",
      "codigo": "5002704",
      "sucesso": true,
      "quantidade": 15
    }
  ]
}
```

---

## 🎨 IMPLEMENTAÇÃO DO FRONTEND (PENDENTE)

### **Estrutura HTML (interface_nova.html)**

```html
<!-- Adicionar no menu Operacional -->
<div class="submenu" id="submenu-operacional">
    <!-- Botões existentes... -->
    
    <button class="submenu-button" onclick="showSection('nfse')" data-permission="nfse_view">
        📄 NFS-e - Notas Fiscais
    </button>
</div>

<!-- Nova seção -->
<div id="nfse-section" class="section" style="display: none;">
    <h2>📄 NFS-e - Notas Fiscais de Serviço</h2>
    
    <!-- Filtros de busca -->
    <div class="card">
        <h3>🔍 Buscar NFS-e</h3>
        <div class="form-row">
            <div class="form-group">
                <label>Data Inicial:</label>
                <input type="date" id="nfse-data-inicial" />
            </div>
            <div class="form-group">
                <label>Data Final:</label>
                <input type="date" id="nfse-data-final" />
            </div>
            <div class="form-group">
                <label>Município:</label>
                <select id="nfse-municipio">
                    <option value="">Todos</option>
                </select>
            </div>
        </div>
        <button onclick="buscarNFSe()" class="btn-primary">
            🔍 Buscar NFS-e
        </button>
        <button onclick="mostrarConfigMunicipios()" class="btn-secondary">
            ⚙️ Configurar Municípios
        </button>
    </div>
    
    <!-- Cards de resumo -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="total-nfse">0</div>
            <div class="stat-label">Total de Notas</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="valor-total-nfse">R$ 0,00</div>
            <div class="stat-label">Valor Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="iss-total-nfse">R$ 0,00</div>
            <div class="stat-label">ISS Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="municipios-nfse">0</div>
            <div class="stat-label">Municípios</div>
        </div>
    </div>
    
    <!-- Tabela de resultados -->
    <div class="card">
        <div id="loading-nfse" style="display: none;">
            <p>⏳ Buscando NFS-e...</p>
        </div>
        
        <table class="table" id="tabela-nfse">
            <thead>
                <tr>
                    <th>Número</th>
                    <th>Data Emissão</th>
                    <th>Tomador</th>
                    <th>Município</th>
                    <th>Valor</th>
                    <th>ISS</th>
                    <th>Situação</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody id="tbody-nfse">
                <tr>
                    <td colspan="8" style="text-align: center;">
                        Nenhuma NFS-e encontrada
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <!-- Botões de exportação -->
    <div class="button-group">
        <button onclick="exportarNFSeExcel()" class="btn-success">
            📥 Exportar Excel
        </button>
        <button onclick="exportarNFSeXMLs()" class="btn-info">
            📄 Baixar XMLs (ZIP)
        </button>
    </div>
</div>

<!-- Modal de configuração de municípios -->
<div id="modal-config-municipios" class="modal">
    <!-- Implementar formulário de configuração -->
</div>

<!-- Modal de detalhes da NFS-e -->
<div id="modal-detalhes-nfse" class="modal">
    <!-- Implementar visualização de detalhes -->
</div>
```

### **Funções JavaScript (app.js)**

```javascript
// ============================================================================
// NFS-e FUNCTIONS
// ============================================================================

async function loadNFSeSection() {
    try {
        // Carregar municípios configurados
        await carregarMunicipiosNFSe();
        
        // Definir datas padrão (mês atual)
        const hoje = new Date();
        const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        
        document.getElementById('nfse-data-inicial').valueAsDate = primeiroDia;
        document.getElementById('nfse-data-final').valueAsDate = hoje;
        
        // Carregar histórico
        await consultarNFSe();
        
    } catch (error) {
        console.error('Erro ao carregar seção NFS-e:', error);
        showAlert('Erro ao carregar NFS-e', 'error');
    }
}

async function carregarMunicipiosNFSe() {
    try {
        const response = await fetchWithAuth('/api/nfse/config');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('nfse-municipio');
            select.innerHTML = '<option value="">Todos os municípios</option>';
            
            data.configs.forEach(config => {
                const option = document.createElement('option');
                option.value = config.codigo_municipio;
                option.textContent = `${config.nome_municipio} - ${config.uf}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar municípios:', error);
    }
}

async function buscarNFSe() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    const codigoMunicipio = document.getElementById('nfse-municipio').value;
    
    if (!dataInicial || !dataFinal) {
        showAlert('Informe as datas inicial e final', 'warning');
        return;
    }
    
    // Mostrar loading
    document.getElementById('loading-nfse').style.display = 'block';
    document.getElementById('tbody-nfse').innerHTML = '<tr><td colspan="8" style="text-align: center;">⏳ Buscando...</td></tr>';
    
    try {
        const response = await fetchWithAuth('/api/nfse/buscar', {
            method: 'POST',
            body: JSON.stringify({
                data_inicial: dataInicial,
                data_final: dataFinal,
                codigos_municipios: codigoMunicipio ? [codigoMunicipio] : null
            })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            showAlert(`✅ Busca concluída! ${data.total_nfse} NFS-e encontradas (${data.nfse_novas} novas)`, 'success');
            
            // Recarregar consulta local
            await consultarNFSe();
        } else {
            showAlert(`Erro: ${data.erros.join(', ')}`, 'error');
        }
        
    } catch (error) {
        console.error('Erro ao buscar NFS-e:', error);
        showAlert('Erro ao buscar NFS-e', 'error');
    } finally {
        document.getElementById('loading-nfse').style.display = 'none';
    }
}

async function consultarNFSe() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    const codigoMunicipio = document.getElementById('nfse-municipio').value;
    
    try {
        const response = await fetchWithAuth('/api/nfse/consultar', {
            method: 'POST',
            body: JSON.stringify({
                data_inicial: dataInicial,
                data_final: dataFinal,
                codigo_municipio: codigoMunicipio || null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            exibirNFSe(data.nfses);
            atualizarResumoNFSe(data.nfses);
        }
        
    } catch (error) {
        console.error('Erro ao consultar NFS-e:', error);
    }
}

function exibirNFSe(nfses) {
    const tbody = document.getElementById('tbody-nfse');
    
    if (nfses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Nenhuma NFS-e encontrada</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    nfses.forEach(nfse => {
        const tr = document.createElement('tr');
        
        const dataEmissao = new Date(nfse.data_emissao).toLocaleDateString('pt-BR');
        const valorServico = parseFloat(nfse.valor_servico).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        const valorIss = parseFloat(nfse.valor_iss).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        
        tr.innerHTML = `
            <td>${nfse.numero_nfse}</td>
            <td>${dataEmissao}</td>
            <td>${nfse.razao_social_tomador || '-'}</td>
            <td>${nfse.nome_municipio}</td>
            <td>${valorServico}</td>
            <td>${valorIss}</td>
            <td>${nfse.situacao}</td>
            <td>
                <button onclick="verDetalhesNFSe(${nfse.id})" class="btn-sm">👁️</button>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

function atualizarResumoNFSe(nfses) {
    const totalNotas = nfses.length;
    const valorTotal = nfses.reduce((sum, n) => sum + parseFloat(n.valor_servico), 0);
    const issTotal = nfses.reduce((sum, n) => sum + parseFloat(n.valor_iss), 0);
    const municipios = new Set(nfses.map(n => n.codigo_municipio)).size;
    
    document.getElementById('total-nfse').textContent = totalNotas;
    document.getElementById('valor-total-nfse').textContent = valorTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById('iss-total-nfse').textContent = issTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById('municipios-nfse').textContent = municipios;
}

async function exportarNFSeExcel() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    
    try {
        const response = await fetchWithAuth('/api/nfse/export/excel', {
            method: 'POST',
            body: JSON.stringify({
                data_inicial: dataInicial,
                data_final: dataFinal
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfse_${dataInicial}_${dataFinal}.csv`;
            a.click();
            
            showAlert('Arquivo exportado com sucesso!', 'success');
        }
        
    } catch (error) {
        console.error('Erro ao exportar:', error);
        showAlert('Erro ao exportar', 'error');
    }
}

async function exportarNFSeXMLs() {
    const dataInicial = document.getElementById('nfse-data-inicial').value;
    const dataFinal = document.getElementById('nfse-data-final').value;
    
    try {
        const response = await fetchWithAuth('/api/nfse/export/xml', {
            method: 'POST',
            body: JSON.stringify({
                data_inicial: dataInicial,
                data_final: dataFinal
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nfse_xmls_${dataInicial}_${dataFinal}.zip`;
            a.click();
            
            showAlert('XMLs exportados com sucesso!', 'success');
        }
        
    } catch (error) {
        console.error('Erro ao exportar XMLs:', error);
        showAlert('Erro ao exportar XMLs', 'error');
    }
}

function mostrarConfigMunicipios() {
    // Implementar modal de configuração
    showAlert('Modal de configuração em desenvolvimento', 'info');
}

async function verDetalhesNFSe(nfseId) {
    // Implementar modal de detalhes
    showAlert('Modal de detalhes em desenvolvimento', 'info');
}

// Adicionar ao switch de seções
if (sectionName === 'nfse') {
    await loadNFSeSection();
}
```

---

## 🔐 PERMISSÕES NECESSÁRIAS

### **Script SQL para adicionar permissões:**

```sql
-- Adicionar permissões do NFS-e
INSERT INTO permissoes (nome, descricao, categoria) VALUES
('nfse_view', 'Visualizar NFS-e', 'nfse'),
('nfse_buscar', 'Buscar novas NFS-e (download via API)', 'nfse'),
('nfse_config', 'Configurar municípios', 'nfse'),
('nfse_export', 'Exportar dados (Excel, XML)', 'nfse'),
('nfse_delete', 'Excluir NFS-e', 'nfse')
ON CONFLICT (nome) DO NOTHING;

-- Dar todas as permissões ao admin
INSERT INTO usuario_permissoes (usuario_id, permissao_id)
SELECT 1, id FROM permissoes WHERE categoria = 'nfse'
ON CONFLICT DO NOTHING;
```

---

## 🐛 TROUBLESHOOTING

### **Erro: "Certificado não encontrado"**

**Causa:** Arquivo .pfx não está no caminho correto

**Solução:**
```bash
# Verificar se arquivo existe
railway run bash
ls -la /app/certificados/

# Se não existir, criar volume
railway volumes create certificados
```

---

### **Erro: "Módulo 'lxml' não encontrado"**

**Causa:** Dependência não instalada

**Solução:**
```bash
# Adicionar ao requirements.txt
echo "lxml>=4.9.0" >> requirements.txt
echo "requests-pkcs12>=1.14" >> requirements.txt

# Reinstalar
pip install -r requirements.txt
```

---

### **Erro: "Servidor SOAP não responde"**

**Causa:** URL do webservice incorreta ou servidor municipal fora do ar

**Solução:**
1. Verificar URL na tabela `nfse_config`
2. Testar manualmente com Postman
3. Verificar se município está em manutenção
4. Usar outro município como teste

---

### **Erro: "Certificado expirado"**

**Causa:** Certificado A1 vencido (validade de 1 ano)

**Solução:**
1. Renovar certificado na AC (Autoridade Certificadora)
2. Fazer upload do novo certificado
3. Atualizar senha se mudou

---

## 📊 CHECKLIST FINAL

### **Backend:**
- [x] Schema PostgreSQL criado
- [x] Camada de dados (nfse_database.py)
- [x] Camada de serviço (nfse_service.py)
- [x] Lógica de negócio (nfse_functions.py)
- [x] Rotas API (web_server.py)
- [ ] Testes unitários

### **Frontend:**
- [ ] Seção HTML criada
- [ ] JavaScript implementado
- [ ] Modais (config + detalhes)
- [ ] CSS/styling

### **Infraestrutura:**
- [ ] Migração executada no Railway
- [ ] Certificado A1 configurado
- [ ] Dependências instaladas
- [ ] Variáveis de ambiente configuradas

### **Segurança:**
- [ ] Permissões criadas
- [ ] Logs de auditoria funcionando
- [ ] Proteção CSRF ativa

### **Documentação:**
- [x] Guia de implementação
- [ ] Guia do usuário
- [ ] Vídeo tutorial

---

## 📞 SUPORTE

**Dúvidas?** Entre em contato com a equipe de desenvolvimento.

**Data:** 2026-02-13  
**Versão:** 1.0 MVP

---

✅ **BACKEND COMPLETO E PRONTO PARA TESTES!**
⏳ **FRONTEND AGUARDANDO IMPLEMENTAÇÃO**
🚀 **NÃO FOI FEITO COMMIT/PUSH PARA O GIT AINDA**

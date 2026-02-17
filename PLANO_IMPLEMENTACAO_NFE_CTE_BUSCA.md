# 📋 Plano de Implementação: Busca NF-e e CT-e

**Data:** 17 de fevereiro de 2026  
**Objetivo:** Implementar sistema completo de busca e processamento de NF-e e CT-e via API SEFAZ  
**Baseado em:** Sistema existente em "NF-e Exportação"  

---

## 🎯 Visão Geral

### Escopo do Projeto

**Implementar:**
1. ✅ Módulos de busca NF-e (via DFe Distribution e Chave)
2. ✅ Módulos de busca CT-e (via DFe Distribution e Chave)
3. ✅ Sistema de armazenamento de XMLs por certificado
4. ✅ Interface web para gerenciamento
5. ✅ API endpoints para busca automática
6. ✅ Integração com tabela `notas_fiscais` existente

**NÃO Implementar nesta fase:**
- ❌ Geração de DANFe/DACTe (usar geradores externos)
- ❌ Assinatura digital de documentos
- ❌ Emissão de NF-e/CT-e

---

## 📁 Estrutura de Arquivos

### Estrutura Principal

```
Sistema_financeiro_dwm/
│
├── relatorios/                         # 🆕 NOVA PASTA
│   ├── __init__.py
│   │
│   ├── nfe/                            # 🆕 NF-e Module
│   │   ├── __init__.py
│   │   ├── nfe_busca.py               # Core: busca via SEFAZ
│   │   ├── nfe_processor.py           # Processamento e extração
│   │   ├── nfe_storage.py             # Armazenamento de XMLs
│   │   └── nfe_api.py                 # Endpoints específicos
│   │
│   └── cte/                            # 🆕 CT-e Module
│       ├── __init__.py
│       ├── cte_busca.py               # Core: busca via SEFAZ
│       ├── cte_processor.py           # Processamento e extração
│       ├── cte_storage.py             # Armazenamento de XMLs
│       └── cte_api.py                 # Endpoints específicos
│
├── templates/
│   ├── relatorios_fiscais.html        # 🆕 Interface principal
│   └── busca_documentos.html          # 🆕 Interface de busca
│
├── storage/                            # 🆕 Armazenamento de XMLs
│   ├── nfe/
│   │   └── {CNPJ}/
│   │       └── {ANO}/
│   │           └── {MES}/
│   │               ├── NFe_{CHAVE}.xml
│   │               └── procNFe_{CHAVE}.xml
│   │
│   └── cte/
│       └── {CNPJ}/
│           └── {ANO}/
│               └── {MES}/
│                   └── CTe_{CHAVE}.xml
│
└── web_server.py                       # Adicionar rotas
```

---

## 🗄️ Estrutura de Banco de Dados

### Tabelas Necessárias

#### 1. `certificados_digitais` (🆕 CRIAR)

```sql
CREATE TABLE certificados_digitais (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- Dados do certificado
    cnpj VARCHAR(14) NOT NULL,
    nome_certificado VARCHAR(255) NOT NULL,
    caminho_pfx TEXT NOT NULL,              -- Caminho ou base64
    senha_pfx VARCHAR(255) NOT NULL,        -- Criptografado
    
    -- Configuração
    cuf INTEGER NOT NULL,                    -- Código UF (50=MS, 35=SP, etc)
    ambiente VARCHAR(10) DEFAULT 'producao', -- 'producao' ou 'homologacao'
    ativo BOOLEAN DEFAULT true,
    
    -- NSU Control (para busca incremental)
    ultimo_nsu VARCHAR(15) DEFAULT '000000000000000',
    data_ultima_busca TIMESTAMP,
    
    -- Validade
    valido_ate DATE,
    
    -- Auditoria
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT uk_certificado_cnpj UNIQUE (empresa_id, cnpj)
);

CREATE INDEX idx_certificados_empresa ON certificados_digitais(empresa_id);
CREATE INDEX idx_certificados_ativo ON certificados_digitais(ativo);
```

#### 2. `documentos_fiscais_log` (🆕 CRIAR)

```sql
CREATE TABLE documentos_fiscais_log (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    certificado_id INTEGER REFERENCES certificados_digitais(id) ON DELETE SET NULL,
    
    -- Identificação
    nsu VARCHAR(15) NOT NULL,
    chave VARCHAR(44),
    tipo_documento VARCHAR(10) NOT NULL,     -- 'NFe', 'CTe', 'NFSe'
    schema_name VARCHAR(50),                 -- 'procNFe_v4.00', 'resNFe_v1.01', etc
    
    -- Status
    processado BOOLEAN DEFAULT false,
    erro TEXT,
    
    -- Referências
    nota_fiscal_id INTEGER REFERENCES notas_fiscais(id) ON DELETE SET NULL,
    
    -- Armazenamento
    caminho_xml TEXT,
    
    -- Auditoria
    data_busca TIMESTAMP DEFAULT NOW(),
    processado_em TIMESTAMP,
    
    CONSTRAINT uk_doc_nsu_cert UNIQUE (certificado_id, nsu)
);

CREATE INDEX idx_doc_log_empresa ON documentos_fiscais_log(empresa_id);
CREATE INDEX idx_doc_log_chave ON documentos_fiscais_log(chave);
CREATE INDEX idx_doc_log_processado ON documentos_fiscais_log(processado);
```

#### 3. Usar tabela existente `notas_fiscais`

✅ **Já existe** (criada na FASE 5.1)

---

## 🔧 Implementação por Módulo

### MÓDULO 1: NFe Busca (`relatorios/nfe/nfe_busca.py`)

**Responsabilidades:**
- Comunicação com SEFAZ via SOAP
- Busca por NSU (DFe Distribution)
- Busca por chave de acesso
- Decodificação de XMLs compactados (gzip + base64)

**Funções Principais:**

```python
# 1. Consultar último NSU disponível
def consultar_ultimo_nsu_sefaz(
    certificado_id: int
) -> dict

# 2. Baixar documentos por NSU
def baixar_documentos_dfe(
    certificado_id: int,
    nsu_inicial: str,
    limite: int = 50
) -> dict

# 3. Buscar NF-e específica por chave
def consultar_nfe_por_chave(
    certificado_id: int,
    chave: str
) -> str  # XML completo

# 4. Buscar múltiplas chaves
def buscar_multiplas_chaves(
    certificado_id: int,
    chaves: List[str]
) -> List[dict]
```

**Dependências:**
- `requests` (HTTP/SOAP)
- `lxml` (XML parsing)
- `cryptography` (certificado digital)
- `base64`, `gzip` (decodificação)

---

### MÓDULO 2: NFe Processor (`relatorios/nfe/nfe_processor.py`)

**Responsabilidades:**
- Extração de dados de XMLs
- Validação de estrutura
- Detecção de tipo de documento
- Mapeamento para modelo do banco

**Funções Principais:**

```python
# 1. Extrair dados completos da NF-e
def extrair_dados_nfe(
    xml_content: str
) -> dict

# 2. Detectar tipo de schema
def detectar_schema_nfe(
    xml_content: str
) -> str  # 'procNFe', 'resNFe', 'procEventoNFe'

# 3. Validar chave de acesso
def validar_chave_nfe(
    chave: str
) -> bool

# 4. Extraer resumo de resNFe
def extrair_resumo_nfe(
    xml_content: str
) -> dict
```

**Estrutura de Dados Extraídos:**

```python
{
    # Identificação
    'chave': str,              # 44 dígitos
    'numero': str,
    'serie': str,
    'modelo': str,             # '55' para NF-e
    'tipo': str,               # 'NFe'
    
    # Emitente
    'cnpj_emitente': str,
    'nome_emitente': str,
    'uf_emitente': str,
    
    # Destinatário
    'cnpj_destinatario': str,
    'nome_destinatario': str,
    'uf_destinatario': str,
    
    # Valores
    'valor_total': float,
    'base_calculo_icms': float,
    'valor_icms': float,
    'base_calculo_pis': float,
    'valor_pis': float,
    'base_calculo_cofins': float,
    'valor_cofins': float,
    
    # Operação
    'cfop': str,
    'natureza_operacao': str,
    'direcao': str,            # 'ENTRADA' ou 'SAIDA'
    
    # Datas
    'data_emissao': datetime,
    'data_entrada_saida': datetime,
    
    # Protocolo
    'numero_protocolo': str,
    'data_autorizacao': datetime,
    
    # Situação
    'situacao': str,           # 'NORMAL', 'CANCELADA', etc
    
    # Metadados
    'nsu': str,
    'schema': str
}
```

---

### MÓDULO 3: NFe Storage (`relatorios/nfe/nfe_storage.py`)

**Responsabilidades:**
- Salvar XMLs no filesystem
- Organização por pasta (CNPJ/ANO/MÊS)
- Gerenciamento de duplicatas
- Backup e recuperação

**Funções Principais:**

```python
# 1. Salvar XML
def salvar_xml_nfe(
    certificado_id: int,
    chave: str,
    xml_content: str,
    tipo_xml: str = 'procNFe'  # 'procNFe', 'resNFe', 'evento'
) -> str  # Retorna caminho do arquivo

# 2. Recuperar XML
def recuperar_xml_nfe(
    chave: str,
    certificado_id: int = None
) -> str  # Conteúdo XML

# 3. Verificar se existe
def existe_xml_nfe(
    chave: str,
    certificado_id: int = None
) -> bool

# 4. Listar XMLs de um período
def listar_xmls_periodo(
    certificado_id: int,
    data_inicio: date,
    data_fim: date
) -> List[dict]
```

**Estrutura de Pastas:**

```
storage/nfe/
├── 12345678000190/           # CNPJ do certificado
│   ├── 2026/
│   │   ├── 01/
│   │   │   ├── NFe_50260112345678000190550010000001.xml
│   │   │   ├── procNFe_50260112345678000190550010000001.xml
│   │   │   └── evento_110111_50260112345678000190550010000001.xml
│   │   └── 02/
│   │       └── ...
│   └── 2025/
│       └── ...
└── 98765432000100/
    └── ...
```

---

### MÓDULO 4: CTe Busca/Processor/Storage

**Estrutura idêntica ao NFe**, com adaptações:

1. **`relatorios/cte/cte_busca.py`**
   - Mesmas funções do NFe
   - Modelo 57 (CT-e)
   - Schema `procCTe_v4.00`

2. **`relatorios/cte/cte_processor.py`**
   - Campos específicos de transporte:
     - `cfop_transporte`
     - `modal`: 'rodoviario', 'aereo', 'ferroviario', etc
     - `tomador`: 'remetente', 'destinatario', 'expedidor'
     - `valor_frete`
     - `peso_total`
   
3. **`relatorios/cte/cte_storage.py`**
   - Estrutura: `storage/cte/{CNPJ}/{ANO}/{MES}/`

---

## 🌐 API Endpoints

### Endpoints NF-e

```python
# 1. Buscar documentos automático (por NSU)
POST /api/relatorios/nfe/buscar-automatico
Body: {
    "certificado_id": 1,
    "limite": 50  # Opcional, padrão 50
}
Response: {
    "success": true,
    "documentos_encontrados": 23,
    "nsu_inicial": "000000000123456",
    "nsu_final": "000000000123479",
    "novos": 15,
    "duplicados": 8
}

# 2. Buscar por chave específica
POST /api/relatorios/nfe/buscar-chave
Body: {
    "certificado_id": 1,
    "chave": "50260101773924000193550010000173831950403658"
}
Response: {
    "success": true,
    "nota": {dados completos},
    "xml_salvo": true,
    "caminho_xml": "storage/nfe/..."
}

# 3. Listar documentos processados
GET /api/relatorios/nfe/listar?data_inicio=2026-01-01&data_fim=2026-01-31
Response: {
    "success": true,
    "total": 150,
    "notas": [{dados}, ...]
}

# 4. Reprocessar documento
POST /api/relatorios/nfe/reprocessar
Body: {
    "chave": "50260101773924000193550010000173831950403658"
}

# 5. Download XML
GET /api/relatorios/nfe/download-xml/<chave>
Response: XML file

# 6. Estatísticas
GET /api/relatorios/nfe/estatisticas?mes=1&ano=2026
Response: {
    "total_documentos": 200,
    "valor_total": 1500000.50,
    "por_tipo": {
        "entrada": {"qtd": 80, "valor": 500000},
        "saida": {"qtd": 120, "valor": 1000000}
    }
}
```

### Endpoints CT-e

(Estrutura idêntica, substituir `/nfe/` por `/cte/`)

---

## 🖥️ Interface Web

### Página Principal: `relatorios_fiscais.html`

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│  📊 RELATÓRIOS FISCAIS                           [⚙️ Config]  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│  │   📄 NF-e       │  │   🚚 CT-e       │  │  📝 NFS-e    ││
│  │                 │  │                 │  │              ││
│  │  150 docs       │  │  45 docs        │  │  78 docs     ││
│  │  R$ 1.5M        │  │  R$ 85K         │  │  R$ 320K     ││
│  │                 │  │                 │  │              ││
│  │  [🔍 Buscar]    │  │  [🔍 Buscar]    │  │  [🔍 Buscar] ││
│  └─────────────────┘  └─────────────────┘  └──────────────┘│
│                                                              │
│  📅 Período: [Jan/2026 ▼]        [🔄 Atualizar]            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  📊 RESUMO DO MÊS                                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  NF-e Emitidas:   120 docs    R$ 1.000.000,00         │ │
│  │  NF-e Recebidas:   30 docs    R$   500.000,00         │ │
│  │  CT-e Emitidos:    45 docs    R$    85.000,00         │ │
│  │  NFS-e Emitidas:   78 docs    R$   320.000,00         │ │
│  │                                                         │ │
│  │  Total Entradas:               R$   500.000,00         │ │
│  │  Total Saídas:                 R$ 1.405.000,00         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [📥 Exportar XML]  [📄 Gerar Relatório]  [📊 Dashboard]   │
└──────────────────────────────────────────────────────────────┘
```

### Modal de Busca NF-e/CT-e

```
┌──────────────────────────────────────────────────┐
│  🔍 Buscar NF-e                          [✕]     │
├──────────────────────────────────────────────────┤
│                                                  │
│  Certificado: [Empresa XYZ - 12345678000190 ▼]  │
│                                                  │
│  ┌─────────── Busca Automática ───────────────┐ │
│  │                                             │ │
│  │  Último NSU: 000000000123456                │ │
│  │                                             │ │
│  │  [🔄 Buscar Novos Documentos]               │ │
│  │                                             │ │
│  │  Limite: [50▼]  documentos por busca        │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────── Busca por Chave ─────────────────┐ │
│  │                                             │ │
│  │  Chave de Acesso (44 dígitos):              │ │
│  │  [____________________________________]      │ │
│  │                                             │ │
│  │  [🔎 Buscar]                                │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────── Histórico ────────────────────────┐ │
│  │                                             │ │
│  │  ✓ NSU 123457 - NF-e 001 - R$ 1.500,00     │ │
│  │  ✓ NSU 123458 - NF-e 002 - R$ 2.300,00     │ │
│  │  ✓ NSU 123459 - Evento Cancelamento         │ │
│  │                                             │ │
│  │  Total: 3 documentos processados            │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  [Fechar]                                        │
└──────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Processamento

### Busca Automática (NSU)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INICIAR BUSCA                                            │
│    - Carregar configuração do certificado                   │
│    - Recuperar último NSU processado                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CONSULTAR SEFAZ                                          │
│    - Montar SOAP request (DistDFeInt)                       │
│    - Enviar com certificado A1                              │
│    - Receber XML com lote de documentos                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. DECODIFICAR DOCUMENTOS                                   │
│    - Para cada <docZip>:                                    │
│      • Extrair NSU                                          │
│      • Decodificar base64 → gzip → XML                      │
│      • Identificar schema (procNFe, resNFe, procCTe, etc)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PROCESSAR CADA DOCUMENTO                                 │
│    - Verificar se já existe (por NSU ou chave)              │
│    - Se duplicado: pular                                    │
│    - Se novo:                                               │
│      • Extrair dados (processor)                            │
│      • Salvar XML (storage)                                 │
│      • Salvar no banco (notas_fiscais)                      │
│      • Registrar log (documentos_fiscais_log)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. ATUALIZAR NSU                                            │
│    - Salvar ultNSU no certificado                           │
│    - Registrar data/hora da última busca                    │
│    - Retornar estatísticas                                  │
└─────────────────────────────────────────────────────────────┘
```

### Busca por Chave

```
┌─────────────────────────────────────────────────────────────┐
│ 1. VALIDAR CHAVE                                            │
│    - Verificar 44 dígitos                                   │
│    - Validar dígito verificador                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. VERIFICAR SE JÁ EXISTE                                   │
│    - Buscar em notas_fiscais                                │
│    - Se existe: retornar dados salvos                       │
│    - Se não: continuar para SEFAZ                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CONSULTAR SEFAZ                                          │
│    - Montar SOAP request (ConsSitNFe)                       │
│    - Enviar com certificado                                 │
│    - Receber XML da NF-e completa                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PROCESSAR E SALVAR                                       │
│    - Extrair dados                                          │
│    - Salvar XML                                             │
│    - Salvar no banco                                        │
│    - Retornar confirmação                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏰ Agendamento Automático

### Script de Busca Periódica

**Arquivo:** `agendar_busca_nfe_cte.py`

```python
#!/usr/bin/env python3
"""
Agendador de busca automática NF-e/CT-e
Executar via cron ou Celery

Execução recomendada: a cada 1 hora
"""

import schedule
import time
from relatorios.nfe import nfe_api
from relatorios.cte import cte_api

def buscar_todos_certificados():
    """Executa busca para todos os certificados ativos"""
    # Buscar NF-e
    nfe_api.executar_busca_automatica_todos()
    
    # Buscar CT-e
    cte_api.executar_busca_automatica_todos()

# Agendar para rodar a cada hora
schedule.every(1).hours.do(buscar_todos_certificados)

# Loop principal
while True:
    schedule.run_pending()
    time.sleep(60)  # Verificar a cada minuto
```

---

## 🔒 Segurança e Permissões

### Permissões Necessárias

```sql
-- Adicionar permissões
INSERT INTO permissoes (nome, categoria, descricao) VALUES
('relatorios.nfe.visualizar', 'relatorios', 'Visualizar NF-e'),
('relatorios.nfe.buscar', 'relatorios', 'Buscar NF-e'),
('relatorios.nfe.exportar', 'relatorios', 'Exportar XMLs NF-e'),
('relatorios.cte.visualizar', 'relatorios', 'Visualizar CT-e'),
('relatorios.cte.buscar', 'relatorios', 'Buscar CT-e'),
('relatorios.cte.exportar', 'relatorios', 'Exportar XMLs CT-e'),
('relatorios.certificados.gerenciar', 'relatorios', 'Gerenciar certificados digitais');
```

### Criptografia de Senhas

```python
from cryptography.fernet import Fernet
import os

class CertificadoSecurity:
    """Gerenciamento seguro de certificados"""
    
    def __init__(self):
        # Chave deve estar em variável de ambiente
        self.key = os.getenv('CERT_ENCRYPTION_KEY')
        self.cipher = Fernet(self.key.encode())
    
    def criptografar_senha(self, senha: str) -> str:
        """Criptografa senha do certificado"""
        return self.cipher.encrypt(senha.encode()).decode()
    
    def descriptografar_senha(self, senha_encrypted: str) -> str:
        """Descriptografa senha do certificado"""
        return self.cipher.decrypt(senha_encrypted.encode()).decode()
```

---

## 📊 Integração com Sistema Existente

### 1. Integração com `notas_fiscais`

**Campos mapeados:**

| Campo NF-e          | Campo DB                | Observações |
|---------------------|-------------------------|-------------|
| chave               | chave_acesso            | PK única    |
| numero              | numero                  |             |
| serie               | serie                   |             |
| modelo              | modelo                  | '55'        |
| cnpj_emitente       | participante_cnpj_cpf   | Se emissor  |
| cnpj_destinatario   | participante_cnpj_cpf   | Se receptor |
| valor_total         | valor_total             |             |
| data_emissao        | data_emissao            |             |
| cfop                | cfop                    |             |
| base_calculo_pis    | base_calculo_pis        |             |
| valor_pis           | valor_pis               |             |

**Lógica de Direção:**

```python
def determinar_direcao(cnpj_empresa: str, cnpj_emitente: str, cnpj_destinatario: str) -> str:
    """
    Determina se NF-e é de ENTRADA ou SAIDA
    """
    if cnpj_emitente == cnpj_empresa:
        return 'SAIDA'
    elif cnpj_destinatario == cnpj_empresa:
        return 'ENTRADA'
    else:
        # Busca via certificado, pode ser de interesse do CNPJ
        return 'ENTRADA'  # Padrão
```

### 2. Integração com `creditos_tributarios`

Ao importar NF-e de entrada (compra):
- Calcular créditos de PIS/COFINS automaticamente
- Criar registros em `creditos_tributarios`
- Tipo: 'INSUMOS', 'ENERGIA', 'ALUGUEL', etc

---

## 🧪 Testes

### Testes Unitários

```python
# tests/test_nfe_busca.py
def test_validar_chave_nfe():
    assert validar_chave_nfe('50260112345678000190550010000001001234567890') == True
    assert validar_chave_nfe('123456') == False

def test_detectar_schema():
    xml = '<procNFe versao="4.00">...</procNFe>'
    assert detectar_schema_nfe(xml) == 'procNFe_v4.00'

def test_extrair_dados_nfe():
    xml = carregar_xml_teste('nfe_exemplo.xml')
    dados = extrair_dados_nfe(xml)
    assert dados['chave'] == '50260112345678000190550010000001001234567890'
    assert dados['numero'] == '000001'
```

### Testes de Integração

```python
# tests/test_nfe_integracao.py
def test_busca_automatica_completa():
    """Testa fluxo completo: busca → processo → salva"""
    resultado = buscar_documentos_dfe(certificado_id=1, nsu_inicial='0'*15)
    assert resultado['success'] == True
    assert len(resultado['documentos']) > 0

def test_salvar_e_recuperar_xml():
    """Testa salvamento e recuperação de XML"""
    xml_content = '<procNFe>...</procNFe>'
    chave = '50260112345678000190550010000001001234567890'
    
    caminho = salvar_xml_nfe(1, chave, xml_content)
    xml_recuperado = recuperar_xml_nfe(chave)
    
    assert xml_content == xml_recuperado
```

---

## 📈 Cronograma de Implementação

### Fase 1: Estrutura Base (2 horas)
- ✅ Criar pasta `relatorios/`
- ✅ Criar subpastas `nfe/` e `cte/`
- ✅ Criar migrations de banco
- ✅ Executar migrations

### Fase 2: Módulo NF-e Core (4 horas)
- ✅ Implementar `nfe_busca.py` (comunicação SEFAZ)
- ✅ Implementar `nfe_processor.py` (extração)
- ✅ Implementar `nfe_storage.py` (armazenamento)
- ✅ Testes unitários básicos

### Fase 3: API NF-e (2 horas)
- ✅ Criar endpoints no `web_server.py`
- ✅ Implementar `nfe_api.py`
- ✅ Documentar API

### Fase 4: Interface Web NF-e (3 horas)
- ✅ Criar `relatorios_fiscais.html`
- ✅ Implementar busca automática
- ✅ Implementar busca por chave
- ✅ Dashboard de estatísticas

### Fase 5: Módulo CT-e (3 horas)
- ✅ Adaptar código NF-e para CT-e
- ✅ Implementar processamento específico CT-e
- ✅ Testes

### Fase 6: Integração e Testes (2 horas)
- ✅ Integrar com `notas_fiscais`
- ✅ Integrar com `creditos_tributarios`
- ✅ Testes end-to-end
- ✅ Documentação final

**Total Estimado: 16 horas**

---

## 🚀 Próximos Passos

1. ✅ **Aprovação do Plano**
2. ✅ **Criar estrutura de pastas**
3. ✅ **Executar migrations**
4. ✅ **Implementar módulo NF-e**
5. ✅ **Implementar módulo CT-e**
6. ✅ **Criar interfaces**
7. ✅ **Testar com certificado real**
8. ✅ **Deploy em produção**

---

## 📚 Referências

- [Manual de Integração DFe Distribution](https://www.nfe.fazenda.gov.br/portal/principal.aspx)
- [Layout NF-e 4.0](https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=tW+YMyk/50s=)
- [Layout CT-e 4.0](https://www.cte.fazenda.gov.br/)
- Código base: `NF-e Exportação/nfe_search.py`

---

**Status:** 📋 Aguardando aprovação para iniciar implementação  
**Última Atualização:** 17/02/2026 18:45

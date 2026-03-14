# FASE 5.1 - EXPANSÃO NF-e/NFS-e + CRÉDITOS TRIBUTÁRIOS

**Data:** 17/02/2026  
**Status:** ✅ Completo (Backend)  
**Commit:** [Pendente]

---

## 📋 VISÃO GERAL

Expansão do sistema SPED com integração completa de notas fiscais eletrônicas e cálculo automático de créditos tributários para regime de Lucro Real (não cumulativo).

### Objetivos Alcançados

✅ **Banco de Dados**: Estrutura completa para gerenciamento de notas fiscais  
✅ **Importação XML**: Suporte a NF-e 4.0 e NFS-e (múltiplos layouts)  
✅ **Créditos Tributários**: Cálculo automático de PIS/COFINS sobre insumos, energia e aluguéis  
✅ **DCTF**: Geração de Declaração de Débitos Federais  
✅ **DIRF**: Geração de Declaração de IR Retido na Fonte  
✅ **Interface Web**: Template HTML para geração de SPED

---

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### Tabela: `notas_fiscais`

Armazena cabeçalho de NF-e, NFS-e, CT-e e NFC-e.

```sql
CREATE TABLE notas_fiscais (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Identificação
    tipo VARCHAR(10) CHECK (tipo IN ('NFE', 'NFSE', 'CTE', 'NFCE')),
    numero VARCHAR(20) NOT NULL,
    serie VARCHAR(10),
    modelo VARCHAR(10),
    chave_acesso VARCHAR(44) UNIQUE,
    
    -- Datas
    data_emissao DATE NOT NULL,
    data_entrada_saida DATE,
    
    -- Operação
    direcao VARCHAR(10) CHECK (direcao IN ('ENTRADA', 'SAIDA')),
    natureza_operacao VARCHAR(200),
    cfop VARCHAR(10),
    
    -- Participante (Fornecedor/Cliente)
    participante_tipo VARCHAR(20),
    participante_cnpj_cpf VARCHAR(18),
    participante_nome VARCHAR(200),
    participante_uf VARCHAR(2),
    
    -- Valores Totais
    valor_total DECIMAL(15,2) NOT NULL,
    valor_produtos DECIMAL(15,2),
    valor_servicos DECIMAL(15,2),
    valor_desconto DECIMAL(15,2),
    
    -- Tributos
    base_calculo_icms DECIMAL(15,2),
    valor_icms DECIMAL(15,2),
    valor_ipi DECIMAL(15,2),
    base_calculo_pis DECIMAL(15,2),
    valor_pis DECIMAL(15,2),
    base_calculo_cofins DECIMAL(15,2),
    valor_cofins DECIMAL(15,2),
    valor_iss DECIMAL(15,2),
    
    -- PIS/COFINS Detalhado
    aliquota_pis DECIMAL(8,4),
    aliquota_cofins DECIMAL(8,4),
    cst_pis VARCHAR(5),
    cst_cofins VARCHAR(5),
    
    -- Situação
    situacao VARCHAR(20) DEFAULT 'NORMAL' 
        CHECK (situacao IN ('NORMAL', 'CANCELADA', 'DENEGADA')),
    
    -- XML
    xml_completo TEXT,
    xml_importado BOOLEAN DEFAULT FALSE,
    data_importacao TIMESTAMP,
    
    -- Vinculação Contábil
    lancamento_contabil_id INTEGER,
    vinculado_contabil BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_nota UNIQUE (empresa_id, tipo, numero, serie)
);
```

**Índices:**
- `idx_nf_empresa` - Busca por empresa
- `idx_nf_emissao` - Busca por data
- `idx_nf_chave` - Busca por chave de acesso
- `idx_nf_participante` - Busca por CNPJ/CPF

### Tabela: `notas_fiscais_itens`

Armazena itens/produtos das notas fiscais.

```sql
CREATE TABLE notas_fiscais_itens (
    id SERIAL PRIMARY KEY,
    nota_fiscal_id INTEGER NOT NULL,
    
    -- Identificação
    numero_item INTEGER NOT NULL,
    codigo_produto VARCHAR(100),
    codigo_ean VARCHAR(20),
    codigo_ncm VARCHAR(20),
    descricao TEXT NOT NULL,
    
    -- Quantidade e Valores
    quantidade DECIMAL(15,4) DEFAULT 1,
    unidade VARCHAR(10) DEFAULT 'UN',
    valor_unitario DECIMAL(15,4) NOT NULL,
    valor_total DECIMAL(15,2) NOT NULL,
    
    -- CFOP
    cfop VARCHAR(10),
    
    -- ICMS
    cst_icms VARCHAR(5),
    origem_mercadoria VARCHAR(2),
    base_calculo_icms DECIMAL(15,2),
    aliquota_icms DECIMAL(8,4),
    valor_icms DECIMAL(15,2),
    
    -- IPI
    cst_ipi VARCHAR(5),
    base_calculo_ipi DECIMAL(15,2),
    aliquota_ipi DECIMAL(8,4),
    valor_ipi DECIMAL(15,2),
    
    -- PIS
    cst_pis VARCHAR(5),
    base_calculo_pis DECIMAL(15,2),
    aliquota_pis DECIMAL(8,4),
    valor_pis DECIMAL(15,2),
    
    -- COFINS
    cst_cofins VARCHAR(5),
    base_calculo_cofins DECIMAL(15,2),
    aliquota_cofins DECIMAL(8,4),
    valor_cofins DECIMAL(15,2)
);
```

### Tabela: `creditos_tributarios`

Registra créditos de PIS/COFINS (regime não cumulativo).

```sql
CREATE TABLE creditos_tributarios (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    
    -- Período
    mes INTEGER CHECK (mes >= 1 AND mes <= 12),
    ano INTEGER CHECK (ano >= 2000 AND ano <= 2100),
    
    -- Tipo de Crédito
    tipo_credito VARCHAR(50) CHECK (tipo_credito IN (
        'INSUMOS',          -- Matérias-primas, produtos intermediários
        'ENERGIA',          -- Energia elétrica
        'ALUGUEL',          -- Aluguéis de prédios/máquinas
        'DEPRECIACAO',      -- Depreciação de ativos
        'FRETE',            -- Fretes sobre vendas
        'ARMAZENAGEM',      -- Armazenagem de mercadorias
        'SERVICOS_PJ',      -- Serviços de pessoa jurídica
        'OUTROS'
    )),
    
    -- Tributo
    tributo VARCHAR(10) CHECK (tributo IN ('PIS', 'COFINS')),
    
    -- Documento Origem
    nota_fiscal_id INTEGER,
    documento_numero VARCHAR(50),
    documento_data DATE,
    
    -- Valores
    base_calculo DECIMAL(15,2) NOT NULL,
    aliquota DECIMAL(8,4) NOT NULL,
    valor_credito DECIMAL(15,2) NOT NULL,
    
    -- Situação
    aprovado BOOLEAN DEFAULT TRUE,
    utilizado BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT uk_credito UNIQUE (
        empresa_id, mes, ano, tipo_credito, tributo, nota_fiscal_id
    )
);
```

### Tabela: `operacoes_fiscais`

Cadastro de CFOPs e configurações fiscais.

```sql
CREATE TABLE operacoes_fiscais (
    id SERIAL PRIMARY KEY,
    
    -- CFOP
    codigo_cfop VARCHAR(10) UNIQUE NOT NULL,
    descricao_cfop TEXT NOT NULL,
    tipo_operacao VARCHAR(20) CHECK (tipo_operacao IN ('ENTRADA', 'SAIDA')),
    origem VARCHAR(20) CHECK (origem IN ('DENTRO_ESTADO', 'FORA_ESTADO', 'EXTERIOR')),
    
    -- CST Padrão
    cst_pis_padrao VARCHAR(5),
    cst_cofins_padrao VARCHAR(5),
    
    -- Configurações PIS/COFINS
    gera_credito_pis BOOLEAN DEFAULT FALSE,
    gera_credito_cofins BOOLEAN DEFAULT FALSE,
    gera_debito_pis BOOLEAN DEFAULT FALSE,
    gera_debito_cofins BOOLEAN DEFAULT FALSE,
    
    -- Alíquotas Sugeridas
    aliquota_pis_sugerida DECIMAL(8,4),
    aliquota_cofins_sugerida DECIMAL(8,4)
);
```

**CFOPs Cadastrados (18 principais):**
- **Entradas:** 1.102, 1.202, 1.401, 1.556 (dentro estado)
- **Entradas:** 2.102, 2.202, 2.401, 2.556 (fora estado)
- **Saídas:** 5.101, 5.102, 5.933 (dentro estado)
- **Saídas:** 6.101, 6.102, 6.933 (fora estado)
- **Exportação:** 7.102

---

## 📥 IMPORTAÇÃO DE NF-e

### Arquivo: `nfe_import_functions.py`

#### Função: `importar_xml_nfe(empresa_id, xml_content, usuario_id=None)`

Importa XML de NF-e versão 4.0 (layout nacional).

**Processo:**
1. Parse do XML com `xml.etree.ElementTree`
2. Validação da chave de acesso (44 dígitos)
3. Verificação de duplicidade
4. Extração de dados:
   - Identificação (número, série, modelo, data)
   - Emitente e destinatário
   - Totais (produtos, tributos)
   - Informações complementares
5. Inserção no banco (nota + itens)

**Exemplo de Uso:**

```python
from nfe_import_functions import importar_xml_nfe

with open('nfe_12345.xml', 'r', encoding='utf-8') as f:
    xml_content = f.read()

resultado = importar_xml_nfe(
    empresa_id=1,
    xml_content=xml_content,
    usuario_id=5
)

if resultado['success']:
    print(f"✅ NF-e {resultado['numero']}/{resultado['serie']} importada!")
    print(f"   Chave: {resultado['chave_acesso']}")
    print(f"   Valor: R$ {resultado['valor_total']:.2f}")
    print(f"   Itens: {resultado['itens_importados']}")
else:
    print(f"❌ Erro: {resultado['error']}")
```

**Retorno:**
```json
{
  "success": true,
  "nota_id": 123,
  "chave_acesso": "35210112345678901234550010000123451234567890",
  "numero": "12345",
  "serie": "1",
  "valor_total": 15000.50,
  "itens_importados": 5,
  "mensagem": "NF-e 12345/1 importada com sucesso"
}
```

#### Função: `importar_xml_nfse(empresa_id, xml_content, usuario_id=None)`

Importa XML de NFS-e (Nota Fiscal de Serviço Eletrônica).

**Atenção:** Cada prefeitura tem um layout diferente! Esta implementação é simplificada e tenta extrair elementos comuns.

**Layouts Testados:**
- ABRASF 2.0 (padrão nacional)
- São Paulo (SP)
- Porto Alegre (RS)

**Elementos Extraídos:**
- Número da NFS-e
- Data de emissão
- Tomador do serviço (cliente)
- Valores (serviços, deduções, tributos)
- Discriminação do serviço

---

## 💰 CÁLCULO DE CRÉDITOS TRIBUTÁRIOS

### Arquivo: `creditos_tributarios_functions.py`

Cálculo automático de créditos de PIS/COFINS para **Lucro Real (regime não cumulativo)**.

**Alíquotas:**
- PIS: **1,65%**
- COFINS: **7,6%**

#### Função: `calcular_creditos_insumos(empresa_id, mes, ano)`

Calcula créditos sobre aquisição de **insumos** (matérias-primas, produtos intermediários, embalagens).

**Critérios:**
- Notas de entrada
- CFOPs: 1.101, 1.102, 1.401, 1.403, 2.101, 2.102, 2.401, 2.403
- CST PIS/COFINS que geram crédito: 50-67

**Exemplo:**

```python
from creditos_tributarios_functions import calcular_creditos_insumos

resultado = calcular_creditos_insumos(
    empresa_id=1,
    mes=1,
    ano=2026
)

# Resultado:
{
  "success": true,
  "tipo": "INSUMOS",
  "credito_pis": 825.00,
  "credito_cofins": 3800.00,
  "total_creditos": 4625.00,
  "quantidade": 15,
  "creditos": [
    {
      "credito_id": 101,
      "tributo": "PIS",
      "nota": "12345/1",
      "fornecedor": "Fornecedor ABC Ltda",
      "valor": 150.00
    },
    ...
  ]
}
```

#### Função: `calcular_creditos_energia(empresa_id, mes, ano)`

Calcula créditos sobre **energia elétrica** consumida nos estabelecimentos.

**Critérios:**
- CFOPs: 1.253 (dentro estado), 2.253 (fora estado)
- Energia consumida nas atividades produtivas

#### Função: `calcular_creditos_aluguel(empresa_id, mes, ano)`

Calcula créditos sobre **aluguéis** de prédios, máquinas e equipamentos utilizados nas atividades.

**Fonte de Dados:**
- Lançamentos contábeis da conta **3.01.02** (Despesas de Aluguel)

#### Função: `calcular_todos_creditos(empresa_id, mes, ano)`

Calcula **todos os tipos** de créditos e retorna resumo consolidado.

**Exemplo de Retorno:**

```json
{
  "success": true,
  "mes": 1,
  "ano": 2026,
  "detalhamento": {
    "insumos": {
      "credito_pis": 1500.00,
      "credito_cofins": 6900.00
    },
    "energia": {
      "credito_pis": 33.00,
      "credito_cofins": 152.00
    },
    "aluguel": {
      "credito_pis": 82.50,
      "credito_cofins": 380.00
    }
  },
  "resumo": {
    "total_credito_pis": 1615.50,
    "total_credito_cofins": 7432.00,
    "total_geral": 9047.50
  }
}
```

#### Função: `obter_resumo_creditos(empresa_id, mes, ano)`

Retorna resumo dos créditos já calculados e armazenados no banco.

---

## 📄 DCTF - DECLARAÇÃO DE DÉBITOS FEDERAIS

### Arquivo: `dctf_functions.py`

Gera DCTF mensal com débitos de IRPJ, CSLL, PIS e COFINS.

### Estrutura do Arquivo DCTF

```
|00|CNPJ|NOME|MES/ANO|TIPO|SITUACAO|
|10|CNPJ|NOME|MUNICIPIO|UF|TELEFONE|EMAIL|
|50|CODIGO_RECEITA|PERIODO|VALOR_PRINCIPAL|MULTA|JUROS|TOTAL|
|50|CODIGO_RECEITA|PERIODO|VALOR_PRINCIPAL|MULTA|JUROS|TOTAL|
...
|90|TOTAL_REGISTROS|
```

**Códigos de Receita:**
- **2172**: PIS - Regime Não Cumulativo
- **2371**: COFINS - Regime Não Cumulativo
- **5425**: IRPJ - Lucro Real
- **2030**: CSLL

### Função: `gerar_arquivo_dctf(empresa_id, mes, ano)`

**Exemplo:**

```python
from dctf_functions import gerar_arquivo_dctf

resultado = gerar_arquivo_dctf(
    empresa_id=1,
    mes=1,
    ano=2026
)

if resultado['success']:
    print(f"Arquivo: {resultado['nome_arquivo']}")
    print(f"Linhas: {resultado['total_linhas']}")
    print(f"Total Débitos: R$ {resultado['total_debitos']:.2f}")
    
    # Salvar arquivo
    with open(resultado['nome_arquivo'], 'w', encoding='utf-8') as f:
        f.write(resultado['conteudo'])
```

---

## 📋 DIRF - DECLARAÇÃO DE IR RETIDO NA FONTE

### Arquivo: `dirf_functions.py`

Gera DIRF anual com informações de:
- Rendimentos pagos a pessoas físicas (funcionários)
- Rendimentos pagos a pessoas jurídicas (fornecedores)
- Imposto de renda retido
- Contribuições previdenciárias

### Estrutura do Arquivo DIRF

```
|DIRF|ANO|ANO_REF|CNPJ|NOME|
|RESPO|CPF|NOME|DDD|TELEFONE|EMAIL|

|BPFDEC|CPF|NOME|
|RTPO|RENDIMENTOS|IR_RETIDO|INSS|

|BPJDEC|CNPJ|NOME|
|RTPJ|VALOR_PAGO|IR|PIS|COFINS|CSLL|

...
|FIM|TOTAL_REGISTROS|
```

**Registros:**
- **DIRF**: Identificação do declarante
- **RESPO**: Responsável pelas informações
- **BPFDEC**: Beneficiário Pessoa Física
- **RTPO**: Rendimentos Tributáveis Pessoa Física
- **BPJDEC**: Beneficiário Pessoa Jurídica
- **RTPJ**: Rendimentos Pessoa Jurídica
- **FIM**: Encerramento

### Função: `gerar_arquivo_dirf(empresa_id, ano)`

**Exemplo:**

```python
from dirf_functions import gerar_arquivo_dirf

resultado = gerar_arquivo_dirf(
    empresa_id=1,
    ano=2025  # Ano-calendário dos rendimentos
)

if resultado['success']:
    print(f"Arquivo: {resultado['nome_arquivo']}")
    print(f"Beneficiários PF: {resultado['total_beneficiarios_pf']}")
    print(f"Beneficiários PJ: {resultado['total_beneficiarios_pj']}")
```

### Função: `obter_resumo_dirf(empresa_id, ano)`

Retorna resumo antes de gerar o arquivo completo.

**Retorno:**
```json
{
  "success": true,
  "ano": 2025,
  "pessoa_fisica": {
    "quantidade_beneficiarios": 25,
    "total_rendimentos": 450000.00,
    "total_ir_retido": 35000.00
  },
  "pessoa_juridica": {
    "quantidade_beneficiarios": 8,
    "total_pagamentos": 120000.00,
    "total_ir_retido": 1800.00
  }
}
```

---

## 🌐 INTERFACE WEB

### Arquivo: `templates/sped_interface.html`

Interface HTML completa para geração de arquivos SPED.

**Funcionalidades:**
- ✅ Geração de SPED ECD (anual)
- ✅ Cálculo e geração de EFD-Contribuições (mensal)
- ✅ Download de arquivos gerados
- ✅ Prévia dos 50 primeiras linhas
- 🔄 DCTF (interface pronta, endpoint pendente)
- 🔄 DIRF (interface pronta, endpoint pendente)

**Tecnologias:**
- HTML5 + CSS3 (Grid Layout)
- JavaScript (Fetch API)
- Design Responsivo
- Gradiente moderno (roxo)

**Endpoints Utilizados:**
```
POST /api/sped/ecd/gerar
POST /api/sped/ecd/exportar

POST /api/sped/efd-contribuicoes/calcular
POST /api/sped/efd-contribuicoes/gerar
POST /api/sped/efd-contribuicoes/exportar
```

**Como Usar:**
1. Abrir `http://localhost:5000/sped` (quando rota for adicionada)
2. Selecionar tipo de obrigação
3. Informar período
4. Clicar em "Gerar" ou "Baixar"

---

## 🔄 MELHORIAS NA EFD-CONTRIBUIÇÕES

A EFD-Contribuições pode ser expandida para usar notas fiscais reais ao invés de lançamentos contábeis.

### Modificação no Bloco C (Documentos Fiscais)

**Antes (simplificado):**
```python
# Usa lançamentos contábeis como proxy
def gerar_registros_C100_C170_C181(empresa_id, mes, ano):
    lancamentos = buscar_lancamentos_receita(...)
    for lanc in lancamentos:
        # Gera C100 fictício
```

**Depois (com NF-e/NFS-e):**
```python
def gerar_registros_C100_C170_C181(empresa_id, mes, ano):
    # Buscar notas fiscais de saída
    notas = executar_query("""
        SELECT * FROM notas_fiscais
        WHERE empresa_id = %s
        AND direcao = 'SAIDA'
        AND EXTRACT(MONTH FROM data_emissao) = %s
        AND EXTRACT(YEAR FROM data_emissao) = %s
        ORDER BY data_emissao, numero
    """, (empresa_id, mes, ano))
    
    for nota in notas:
        # C100 - Documento fiscal
        registro_c100 = gerar_C100_nota_real(nota)
        
        # C170 - Itens da nota
        itens = buscar_itens_nota(nota['id'])
        for item in itens:
            registro_c170 = gerar_C170_item_real(item)
            
            # C181 - Detalhamento PIS/COFINS
            registro_c181_pis = gerar_C181_real(item, 'PIS')
            registro_c181_cofins = gerar_C181_real(item, 'COFINS')
```

### Modificação no Bloco M (Apuração com Créditos)

**Antes:**
```python
def gerar_registro_M100_M110(empresa_id, mes, ano):
    # PIS sem créditos
    pis = calcular_pis_basico()
    return f"|M100|{pis}|0.00|{pis}|"
```

**Depois:**
```python
def gerar_registro_M100_M110(empresa_id, mes, ano):
    from creditos_tributarios_functions import obter_resumo_creditos
    
    # PIS com créditos
    debito_pis = calcular_pis_debito()
    creditos = obter_resumo_creditos(empresa_id, mes, ano)
    credito_pis = creditos['totais']['PIS']
    
    pis_a_pagar = debito_pis - credito_pis
    
    return f"|M100|{debito_pis:.2f}|{credito_pis:.2f}|{pis_a_pagar:.2f}|"
```

---

## 📊 FLUXO COMPLETO DE OPERAÇÃO

### 1. Importação de Notas Fiscais

```python
# 1.1. Upload do XML pelo usuário
xml_file = request.files['xml']
xml_content = xml_file.read().decode('utf-8')

# 1.2. Importar NF-e
resultado = importar_xml_nfe(empresa_id, xml_content)
# Ou NFS-e
resultado = importar_xml_nfse(empresa_id, xml_content)

# 1.3. Verificar resultado
if resultado['success']:
    nota_id = resultado['nota_id']
```

### 2. Cálculo de Créditos (mensal)

```python
# 2.1. Calcular todos os créditos do mês
creditos = calcular_todos_creditos(empresa_id, mes=1, ano=2026)

# 2.2. Verificar resumo
print(f"Crédito PIS: R$ {creditos['resumo']['total_credito_pis']:.2f}")
print(f"Crédito COFINS: R$ {creditos['resumo']['total_credito_cofins']:.2f}")
```

### 3. Geração de EFD-Contribuições

```python
# 3.1. Gerar arquivo com notas fiscais reais
from sped_efd_contribuicoes_functions import gerar_arquivo_efd_contribuicoes

efd = gerar_arquivo_efd_contribuicoes(empresa_id, mes=1, ano=2026)

# 3.2. Salvar arquivo
with open(efd['nome_arquivo'], 'w', encoding='utf-8') as f:
    f.write(efd['conteudo'])
```

### 4. Geração de DCTF

```python
from dctf_functions import gerar_arquivo_dctf

dctf = gerar_arquivo_dctf(empresa_id, mes=1, ano=2026)

with open(dctf['nome_arquivo'], 'w', encoding='utf-8') as f:
    f.write(dctf['conteudo'])
```

### 5. Geração de DIRF (anual)

```python
from dirf_functions import gerar_arquivo_dirf

# No final do ano, gerar DIRF
dirf = gerar_arquivo_dirf(empresa_id, ano=2025)

with open(dirf['nome_arquivo'], 'w', encoding='utf-8') as f:
    f.write(dirf['conteudo'])
```

---

## ⚠️ LIMITAÇÕES E MELHORIAS FUTURAS

### Limitações Atuais

1. **NFS-e**: Layout simplificado (cada prefeitura tem um padrão diferente)
2. **Créditos**: Implementados apenas 3 tipos (insumos, energia, aluguel)
3. **DCTF**: Simplificado (não inclui todos os códigos de receita)
4. **DIRF**: Requer tabelas `funcionarios` e `pagamentos_salarios` completas
5. **Endpoints API**: DCTF e DIRF ainda não adicionados ao `web_server.py`

### Próximas Melhorias

1. **Layouts NFS-e Municipais**
   - Implementar parsers específicos para principais cidades
   - São Paulo, Rio de Janeiro, Belo Horizonte, etc.

2. **Mais Tipos de Créditos**
   - Depreciação de ativos imobilizados
   - Fretes sobre vendas
   - Armazenagem de mercadorias
   - Serviços de PJ relacionados à produção

3. **Validações Avançadas**
   - Validar chave de acesso com dígito verificador
   - Validar CST PIS/COFINS por CFOP
   - Alertas de operações sem crédito

4. **Relatórios Gerenciais**
   - Dashboard de créditos aproveitados
   - Comparativo mensal de tributos
   - Análise de efetivo tributário

5. **Integração Contábil**
   - Gerar lançamentos contábeis automaticamente ao importar NF-e
   - Vincular notas a centros de custo
   - Ratear tributos por departamento

---

## 📁 ARQUIVOS CRIADOS NESTA FASE

```
migration_notas_fiscais.py                 (408 linhas)
nfe_import_functions.py                    (950 linhas)
creditos_tributarios_functions.py          (535 linhas)
dctf_functions.py                          (235 linhas)
dirf_functions.py                          (310 linhas)
templates/sped_interface.html              (680 linhas)
FASE5.1_EXPANSAO_NFE_COMPLETA.md           (Este arquivo)
```

**Total:** ~3.118 linhas de código novo + documentação

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [x] Migração do banco de dados
- [x] Tabelas: notas_fiscais, notas_fiscais_itens, creditos_tributarios, operacoes_fiscais
- [x] Índices e constraints
- [x] População de CFOPs básicos
- [x] Função importar_xml_nfe()
- [x] Função importar_xml_nfse()
- [x] Extração de todos os campos fiscais
- [x] Validação de chave de acesso
- [x] Detecção de duplicidade
- [x] Função calcular_creditos_insumos()
- [x] Função calcular_creditos_energia()
- [x] Função calcular_creditos_aluguel()
- [x] Função calcular_todos_creditos()
- [x] Função obter_resumo_creditos()
- [x] Geração de DCTF
- [x] Geração de DIRF
- [x] Interface web sped_interface.html
- [ ] Endpoints API (/api/notas-fiscais/importar)
- [ ] Endpoints API (/api/creditos-tributarios/calcular)
- [ ] Endpoints API (/api/dctf/gerar)
- [ ] Endpoints API (/api/dirf/gerar)
- [ ] Testes unitários
- [ ] Documentação de API (Swagger/OpenAPI)

---

## 🎯 RESUMO EXECUTIVO

**FASE 5.1** expande o sistema SPED com:

✅ **4 tabelas** novas no banco de dados  
✅ **5 módulos** Python (importação, créditos, DCTF, DIRF)  
✅ **~3.000 linhas** de código funcional  
✅ **Interface web** completa para geração de SPED  
✅ **Suporte a NF-e 4.0** e NFS-e simplificado  
✅ **Cálculo automático** de créditos tributários  
✅ **Geração de DCTF** mensal  
✅ **Geração de DIRF** anual  

**Benefícios:**
- Automação completa de obrigações fiscais
- Integração entre notas fiscais e contabilidade
- Aproveitamento correto de créditos tributários
- Redução de erros em declarações
- Economia de tempo na geração de arquivos SPED

**Status:** ✅ Backend completo, aguardando integração de endpoints na API

---

**Desenvolvido por:** Eduardo Souza  
**Data:** 17 de Fevereiro de 2026  
**Versão:** 1.0

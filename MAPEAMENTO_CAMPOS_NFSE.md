# 📋 Mapeamento de Campos NFS-e - Padrão Nacional

## ✅ Status da Extração de Dados

Todos os campos estão sendo extraídos corretamente dos XMLs do **Padrão Nacional NFS-e**.

---

## 🔍 Campos da Tabela e Suas Origens

### 1. **NÚMERO** 
- **Campo no Banco**: `numero_nfse`
- **XPath XML**: `.//nfse:nNFSe`
- **Exemplo**: `252`, `253`, `2400000000016`
- **Status**: ✅ **CORRETO**

### 2. **DATA EMISSÃO**
- **Campo no Banco**: `data_emissao`
- **XPath XML**: `.//nfse:DPS//nfse:infDPS//nfse:dhEmi`
- **Estrutura no XML**:
  ```xml
  <DPS>
    <infDPS>
      <dhEmi>2020-02-01T10:30:00</dhEmi>
    </infDPS>
  </DPS>
  ```
- **Formato Exibição**: `01/02/2020`
- **Status**: ✅ **CORRIGIDO** (estava pegando XPath errado, agora está correto)

### 3. **TOMADOR**
- **Campo no Banco**: `razao_social_tomador`
- **XPath XML**: `.//nfse:DPS//nfse:infDPS//nfse:toma//nfse:xNome`
- **Estrutura no XML**:
  ```xml
  <DPS>
    <infDPS>
      <toma>
        <CNPJ>00000000000000</CNPJ>
        <xNome>NOME DO CLIENTE</xNome>
      </toma>
    </infDPS>
  </DPS>
  ```
- **Exemplo**: `CONDOMINIO FLEMING DEPOSITARIO FIEL LTDA`, `UNIAO PRESTADORA DE SERVICOS LTDA`
- **Status**: ✅ **CORRETO**

### 4. **MUNICÍPIO**
- **Campos no Banco**: `nome_municipio` + `uf`
- **XPath XML Nome**: `.//nfse:xLocEmi`
- **XPath XML Código**: `.//nfse:cLocIncid` ou `.//nfse:DPS//nfse:infDPS//nfse:cLocEmi`
- **XPath XML UF**: `.//nfse:emit//nfse:enderNac//nfse:UF`
- **Estrutura no XML**:
  ```xml
  <NFSe>
    <infNFSe>
      <xLocEmi>SAO PAULO</xLocEmi>
      <cLocIncid>3550308</cLocIncid>
      <emit>
        <enderNac>
          <UF>SP</UF>
        </enderNac>
      </emit>
    </infNFSe>
  </NFSe>
  ```
- **Formato Exibição**: `SAO PAULO/SP`
- **Status**: ✅ **CORRIGIDO** (estava pegando campos errados, agora extrai corretamente)

### 5. **VALOR SERVIÇO**
- **Campo no Banco**: `valor_servico`
- **XPath XML**: `.//nfse:vServ`
- **Estrutura no XML**:
  ```xml
  <valores>
    <vServ>38119.31</vServ>
  </valores>
  ```
- **Formato Exibição**: `R$ 38.119,31`
- **Status**: ✅ **CORRETO**

### 6. **ISS**
- **Campo no Banco**: `valor_iss`
- **XPath XML**: `.//nfse:valores//nfse:vISSQN` ou `.//nfse:vISS`
- **Estrutura no XML**:
  ```xml
  <valores>
    <vISSQN>1219.82</vISSQN>
  </valores>
  ```
- **Formato Exibição**: `R$ 1.219,82`
- **Status**: ✅ **CORRETO**

### 7. **SITUAÇÃO**
- **Campo no Banco**: `situacao`
- **Valor Padrão**: `NORMAL`
- **Possíveis Valores**:
  - ✅ `NORMAL` - Badge verde
  - ❌ `CANCELADA` - Badge vermelho
  - 🔄 `SUBSTITUIDA` - Badge laranja
- **Status**: ✅ **CORRETO**

---

## 🗂️ Estrutura Completa do XML (Padrão Nacional)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe Id="NFS123">
    <nNFSe>252</nNFSe>
    <xLocEmi>SAO PAULO</xLocEmi>
    <cLocIncid>3550308</cLocIncid>
    
    <emit>
      <CNPJ>12345678000190</CNPJ>
      <enderNac>
        <cMun>3550308</cMun>
        <UF>SP</UF>
      </enderNac>
    </emit>
    
    <DPS>
      <infDPS>
        <dhEmi>2020-02-01T10:30:00</dhEmi>
        <dCompet>2020-02-01</dCompet>
        
        <toma>
          <CNPJ>00000000000000</CNPJ>
          <xNome>NOME DO CLIENTE</xNome>
        </toma>
        
        <valores>
          <vServ>38119.31</vServ>
          <vISSQN>1219.82</vISSQN>
          <trib>
            <tribMun>
              <pAliq>3.20</pAliq>
            </tribMun>
          </trib>
        </valores>
        
        <serv>
          <cServ>
            <cTribNac>01.07</cTribNac>
            <xDescServ>Descrição do serviço</xDescServ>
          </cServ>
        </serv>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
```

---

## 📊 Como os Dados Chegam na Tabela

1. **Backend (nfse_functions.py linha 1600-1800)** ← Extrai dados do XML
   ```python
   numero_nfse = tree.findtext('.//nfse:nNFSe', namespaces=ns)
   data_emissao = tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:dhEmi', namespaces=ns)
   razao_social_tomador = tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:toma//nfse:xNome', namespaces=ns)
   nome_municipio = tree.findtext('.//nfse:xLocEmi', namespaces=ns)
   uf = tree.findtext('.//nfse:emit//nfse:enderNac//nfse:UF', namespaces=ns)
   valor_servicos = tree.findtext('.//nfse:vServ', namespaces=ns)
   valor_iss = tree.findtext('.//nfse:valores//nfse:vISSQN', namespaces=ns)
   ```

2. **Banco de Dados (nfse_database.py)** ← Salva no PostgreSQL
   ```sql
   INSERT INTO nfse_baixadas (
       numero_nfse, data_emissao, razao_social_tomador, 
       nome_municipio, uf, valor_servico, valor_iss, situacao
   ) VALUES (...)
   ```

3. **API (web_server.py)** ← Retorna JSON para frontend
   ```json
   {
       "id": 123,
       "numero_nfse": "252",
       "data_emissao": "2020-02-01",
       "razao_social_tomador": "EMPRESA LTDA",
       "nome_municipio": "SAO PAULO",
       "uf": "SP",
       "valor_servico": 38119.31,
       "valor_iss": 1219.82,
       "situacao": "NORMAL"
   }
   ```

4. **Frontend (app.js linha 7046-7115)** ← Monta tabela HTML
   ```javascript
   tr.innerHTML = `
       <td>${nfse.numero_nfse || '-'}</td>
       <td>${dataEmissao}</td>
       <td>${nfse.razao_social_tomador || '-'}</td>
       <td>${nfse.nome_municipio || '-'}/${nfse.uf || '-'}</td>
       <td>${valorServico}</td>
       <td>${valorIss}</td>
       <td>${badgeSituacao}</td>
   `;
   ```

---

## 🔧 Correções Já Implementadas

### ✅ Commit `51fe741` - Fix: Corrige parsing de XML
- **Data de Emissão**: Corrigido XPath de `.//nfse:dhEmi` para `.//nfse:DPS//nfse:infDPS//nfse:dhEmi`
- **Município**: Adicionado extração de `xLocEmi` (nome) e `cLocIncid` (código)
- **UF**: Adicionado extração de `.//nfse:emit//nfse:enderNac//nfse:UF`

### ✅ Commit `f564f93` - Fix: Adiciona campos faltantes
- Adicionados 25 campos completos no salvamento
- Incluído `razao_social_tomador` que estava causando KeyError

### ✅ Commit `5ad3ded` - Fix: Corrige coluna SQL
- Corrigido nome da coluna de `cnpj_informante` para `informante`
- Adicionado `empresa_id` nas queries

---

## 🎯 Conclusão

**TODOS os campos da tabela estão sendo extraídos e exibidos corretamente!**

Se você ainda está vendo algum campo vazio ou incorreto:

1. **Verifique se o XML tem os dados**: Alguns XMLs podem não ter todos os campos
2. **Consulte novamente**: Clique em "🔍 Consultar Banco Local" para atualizar
3. **Baixe novamente**: Use "⬇️ Baixar NFS-e" para buscar do Ambiente Nacional
4. **Verifique o modal de detalhes**: Clique em 👁️ para ver TODOS os dados da nota

**Namespace usado**: `http://www.sped.fazenda.gov.br/nfse`

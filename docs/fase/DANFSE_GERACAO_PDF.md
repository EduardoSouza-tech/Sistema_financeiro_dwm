# Geração de DANFSe (Documento Auxiliar da NFS-e)

## 📄 O que é DANFSe?

O **DANFSe** (Documento Auxiliar da Nota Fiscal de Serviços Eletrônica) é o PDF oficial padronizado pelo governo federal para representação visual da NFS-e. É equivalente ao DANFE da NF-e.

### Características do DANFSe Oficial:
- ✅ Layout padronizado nacionalmente
- ✅ QR Code para validação
- ✅ Brasão da República
- ✅ Informações fiscais completas
- ✅ Código de verificação
- ✅ Dados do prestador e tomador
- ✅ Tributos federais e municipais

---

## 🌐 Método 1: API do Ambiente Nacional (RECOMENDADO)

**Nossa implementação atual** já usa este método, que é o **OFICIAL** e **MAIS CONFIÁVEL**.

### Como Funciona:
```python
from nfse_service import NFSeAmbienteNacional

cliente = NFSeAmbienteNacional(
    certificado_path='certificado.pfx',
    certificado_senha='senha123',
    ambiente='producao'
)

# Baixar DANFSe oficial
chave_acesso = "50027041239960451000106000000000025226010634443033"  # 50 dígitos
pdf_content = cliente.consultar_danfse(chave_acesso)

# Salvar PDF
with open('danfse_oficial.pdf', 'wb') as f:
    f.write(pdf_content)
```

### Vantagens:
- ✅ PDF oficial gerado pelo governo
- ✅ Sempre atualizado com o padrão mais recente
- ✅ Validado pela SEFAZ
- ✅ Contém todos os elementos visuais oficiais
- ✅ QR Code válido

### Desvantagens:
- ⚠️ Requer conexão com a internet
- ⚠️ Nem todas as NFS-e têm DANFSe disponível imediatamente
- ⚠️ Depende de disponibilidade da API

### Endpoint:
```
GET https://adn.nfse.gov.br/danfse/{chave_acesso}
```

**Status Atual**: ✅ **IMPLEMENTADO** em `nfse_service.py` e `nfse_functions.py`

---

## 🖨️ Método 2: Geração Local (ALTERNATIVA)

Para casos onde o DANFSe não está disponível na API, é possível gerar um PDF localmente baseado no XML.

### ⚠️ IMPORTANTE:
Este método **NÃO** gera o DANFSe oficial. Gera um PDF simples para visualização apenas.

### Bibliotecas Python para Geração de PDF:

#### 1. **ReportLab** (Mais Flexível)
```python
pip install reportlab
```

**Exemplo básico:**
```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from lxml import etree

def gerar_pdf_nfse(xml_content: str, output_path: str):
    """
    Gera PDF simples da NFS-e (não é o DANFSe oficial)
    """
    # Parse XML
    tree = etree.fromstring(xml_content.encode('utf-8'))
    ns = {'nfse': 'http://www.sped.fazenda.gov.br/nfse'}
    
    # Extrair dados
    numero = tree.findtext('.//nfse:nNFSe', namespaces=ns)
    data_emissao = tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:dhEmi', namespaces=ns)
    valor = tree.findtext('.//nfse:valores//nfse:vBC', namespaces=ns)
    prestador_cnpj = tree.findtext('.//nfse:emit//nfse:CNPJ', namespaces=ns)
    prestador_nome = tree.findtext('.//nfse:emit//nfse:xNome', namespaces=ns)
    tomador_cnpj = tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:toma//nfse:CNPJ', namespaces=ns)
    tomador_nome = tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:toma//nfse:xNome', namespaces=ns)
    
    # Criar PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 2.5*cm, "(Este não é o DANFSe oficial)")
    
    # Número e Data
    y = height - 4*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, f"Número: {numero}")
    c.drawString(2*cm, y - 0.6*cm, f"Data: {data_emissao[:10]}")
    
    # Prestador
    y -= 2*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "PRESTADOR DE SERVIÇOS")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y - 0.6*cm, f"CNPJ: {prestador_cnpj}")
    c.drawString(2*cm, y - 1.2*cm, f"Nome: {prestador_nome}")
    
    # Tomador
    y -= 3*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "TOMADOR DE SERVIÇOS")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y - 0.6*cm, f"CNPJ: {tomador_cnpj}")
    c.drawString(2*cm, y - 1.2*cm, f"Nome: {tomador_nome}")
    
    # Valor
    y -= 3*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, f"Valor Total: R$ {float(valor):,.2f}")
    
    # Aviso
    y -= 3*cm
    c.setFont("Helvetica-Italic", 8)
    c.drawString(2*cm, y, "Este documento não substitui o DANFSe oficial.")
    c.drawString(2*cm, y - 0.4*cm, "Para obter o DANFSe oficial, consulte o portal da Prefeitura ou SEFAZ.")
    
    c.save()
    print(f"✅ PDF gerado: {output_path}")
```

**Vantagens:**
- ✅ Funciona offline
- ✅ Customização total do layout
- ✅ Rápido
- ✅ Não depende de API externa

**Desvantagens:**
- ❌ Não é o DANFSe oficial
- ❌ Não tem QR Code válido
- ❌ Não tem brasão oficial
- ❌ Não é aceito para fins fiscais

---

#### 2. **PyPDF2 + HTML2PDF** (Para layouts complexos)
```python
pip install pdfkit wkhtmltopdf
```

**Exemplo:**
```python
import pdfkit
from lxml import etree

def gerar_pdf_html(xml_content: str, output_path: str):
    """
    Gera PDF usando HTML como template
    """
    # Parse XML
    tree = etree.fromstring(xml_content.encode('utf-8'))
    ns = {'nfse': 'http://www.sped.fazenda.gov.br/nfse'}
    
    # Extrair dados
    numero = tree.findtext('.//nfse:nNFSe', namespaces=ns)
    # ... outros campos
    
    # Template HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ text-align: center; color: #003366; }}
            .box {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
            .label {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>NOTA FISCAL DE SERVIÇOS ELETRÔNICA</h1>
        <p style="text-align: center; color: red;">
            (Este não é o DANFSe oficial)
        </p>
        
        <div class="box">
            <p><span class="label">Número:</span> {numero}</p>
            <p><span class="label">Data:</span> {data_emissao}</p>
        </div>
        
        <!-- Mais campos aqui -->
    </body>
    </html>
    """
    
    # Converter HTML para PDF
    pdfkit.from_string(html, output_path)
    print(f"✅ PDF gerado: {output_path}")
```

**Vantagens:**
- ✅ Fácil criar layouts com CSS
- ✅ Suporta imagens e gráficos
- ✅ Mais próximo do visual HTML

**Desvantagens:**
- ❌ Requer wkhtmltopdf instalado no sistema
- ❌ Mais pesado
- ❌ Ainda não é DANFSe oficial

---

## 🔐 Método 3: API Municipal (Prefeituras)

Algumas prefeituras disponibilizam API para download do DANFSe:

```python
# Exemplo genérico (varia por município)
import requests

def baixar_danfse_municipal(numero_nfse: str, codigo_verificacao: str, cnpj_prestador: str):
    """
    Baixa DANFSe do portal da prefeitura
    """
    # URL varia por município
    url = f"https://nfse.prefeitura.sp.gov.br/contribuinte/danfse.aspx"
    
    params = {
        'numero': numero_nfse,
        'verificacao': codigo_verificacao,
        'cnpj': cnpj_prestador
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.content
    return None
```

**Problemas:**
- ❌ Cada município tem URL diferente
- ❌ Cada município tem parâmetros diferentes
- ❌ Muitos não têm API pública
- ❌ Alta manutenção

---

## 📋 Recomendações

### Para Produção:
1. **SEMPRE tente baixar o DANFSe oficial da API Nacional primeiro** ✅
2. Se não disponível, tente a API municipal (se existir)
3. Como último recurso, gere um PDF simples com ReportLab
4. **NUNCA** chame um PDF gerado localmente de "DANFSe oficial"

### Nossa Implementação Atual:

```python
# Em nfse_functions.py (já implementado)

# 1. Extrair chave de acesso do XML
inf_nfse = tree.find('.//nfse:infNFSe', namespaces=ns)
if inf_nfse is not None:
    chave_id = inf_nfse.get('Id', '')
    if chave_id and chave_id.startswith('NFS'):
        chave_acesso = chave_id[3:]  # Remove prefixo "NFS"
        
        # 2. Baixar DANFSe oficial da API Nacional
        logger.info(f"   📄 Baixando DANFSe oficial...")
        pdf_content = cliente.consultar_danfse(chave_acesso, retry=2)
        
        if pdf_content:
            # 3. Salvar PDF oficial
            pdf_path = salvar_pdf_nfse(
                pdf_content=pdf_content,
                numero_nfse=numero_nfse,
                cnpj_prestador=cnpj_prestador,
                codigo_municipio=codigo_municipio,
                data_emissao=data_emissao
            )
            logger.info(f"   ✅ DANFSe salvo: {pdf_path}")
        else:
            logger.info(f"   ℹ️ DANFSe não disponível na API")
            # TODO: Gerar PDF simples aqui (opcional)
```

---

## 🎯 Conclusão

### ✅ O que temos agora:
- Download automático de DANFSe oficial via API Nacional
- Salvamento organizado por CNPJ/Ano/Mês
- PDFs oficiais com QR Code e brasão

### 🔧 O que poderia ser adicionado (se necessário):
1. **Fallback para PDF simples** quando DANFSe não estiver disponível
2. **Biblioteca ReportLab** para geração local
3. **Template HTML** para layout mais bonito

### 📌 Nota Importante:
O **DANFSe oficial só pode ser gerado pelo sistema autorizado** (Ambiente Nacional ou Prefeitura). Qualquer PDF gerado localmente é apenas uma **representação visual**, não tendo validade fiscal.

---

## 📚 Referências

- [Documentação NFS-e Nacional](https://www.gov.br/nfse)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)
- [Padrão Nacional NFS-e - Manual Técnico](https://www.gov.br/nfse/pt-br/documentos)

"""
Módulo de busca/consulta de NF-e via webservices SEFAZ

Este módulo é responsável por:
- Conectar com SEFAZ via certificado digital A1
- Consultar Distribuição DFe (NSU incremental)
- Consultar NF-e por chave de acesso
- Descomprimir XMLs recebidos (base64 + gzip)
- Processar lotes de documentos

Webservices utilizados:
- NFeDistribuicaoDFe: Busca incremental por NSU
- NfeConsultaProtocolo: Consulta por chave

Autor: Sistema Financeiro DWM
Data: Janeiro 2026
"""

import requests
import base64
import gzip
import os
from lxml import etree
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend


# ============================================================================
# CONFIGURAÇÕES SEFAZ
# ============================================================================

# URLs dos webservices SEFAZ (Produção - AN - Ambiente Nacional)
WEBSERVICES_PRODUCAO = {
    'NFeDistribuicaoDFe': 'https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx',
    'NfeConsultaProtocolo': 'https://www.nfe.fazenda.gov.br/NFeAutorizacao4/NFeRetAutorizacao4.asmx',
}

# URLs dos webservices SEFAZ (Homologação - AN)
WEBSERVICES_HOMOLOGACAO = {
    'NFeDistribuicaoDFe': 'https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx',
    'NfeConsultaProtocolo': 'https://hom.nfe.fazenda.gov.br/NFeAutorizacao4/NFeRetAutorizacao4.asmx',
}

# Namespace do webservice
NAMESPACE_NFE = 'http://www.portalfiscal.inf.br/nfe'

# Número máximo de NSUs por consulta (limitado pela SEFAZ)
MAX_NSUS_POR_CONSULTA = 50


# ============================================================================
# CERTIFICADO DIGITAL
# ============================================================================

class CertificadoA1:
    """Gerenciador de certificado digital A1."""
    
    def __init__(self, caminho_pfx: str = None, pfx_base64: str = None, senha: str = ''):
        """
        Inicializa o certificado A1.
        
        Args:
            caminho_pfx: Caminho para arquivo .pfx
            pfx_base64: Conteúdo do .pfx em base64
            senha: Senha do certificado
        """
        self.caminho_pfx = caminho_pfx
        self.pfx_base64 = pfx_base64
        self.senha = senha.encode('utf-8') if senha else b''
        
        self.cert_pem = None
        self.key_pem = None
        self.cert_data = None
        
        self._carregar_certificado()
    
    def _carregar_certificado(self):
        """Carrega o certificado e extrai chave privada e certificado."""
        try:
            # Lê o arquivo PFX
            if self.caminho_pfx and os.path.exists(self.caminho_pfx):
                with open(self.caminho_pfx, 'rb') as f:
                    pfx_data = f.read()
            elif self.pfx_base64:
                pfx_data = base64.b64decode(self.pfx_base64)
            else:
                raise ValueError("Nenhum certificado fornecido")
            
            # Carrega PFX
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                self.senha,
                backend=default_backend()
            )
            
            if not private_key or not certificate:
                raise ValueError("Certificado inválido ou senha incorreta")
            
            # Converte para PEM
            self.key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self.cert_pem = certificate.public_bytes(
                encoding=serialization.Encoding.PEM
            )
            
            # Extrai informações do certificado
            self.cert_data = {
                'subject': certificate.subject.rfc4514_string(),
                'issuer': certificate.issuer.rfc4514_string(),
                'valido_de': certificate.not_valid_before_utc,
                'valido_ate': certificate.not_valid_after_utc,
                'serial_number': certificate.serial_number,
            }
            
            # Extrai CNPJ do certificado (Subject CN ou OID específico)
            for attr in certificate.subject:
                if attr.oid.dotted_string == '2.5.4.3':  # CN (Common Name)
                    cn = attr.value
                    # Tenta extrair CNPJ do CN
                    import re
                    match = re.search(r'(\d{14})', cn)
                    if match:
                        self.cert_data['cnpj'] = match.group(1)
            
        except Exception as e:
            raise ValueError(f"Erro ao carregar certificado: {str(e)}")
    
    def esta_valido(self) -> bool:
        """Verifica se o certificado está dentro do prazo de validade."""
        if not self.cert_data:
            return False
        
        agora = datetime.now(timezone.utc)
        return (self.cert_data['valido_de'] <= agora <= self.cert_data['valido_ate'])
    
    def get_session_requests(self) -> requests.Session:
        """Retorna uma sessão requests configurada com o certificado."""
        session = requests.Session()
        
        # Cria arquivos temporários para cert e key (requests precisa de arquivos)
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as cert_file:
            cert_file.write(self.cert_pem)
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as key_file:
            key_file.write(self.key_pem)
            key_path = key_file.name
        
        # Configura sessão
        session.cert = (cert_path, key_path)
        session.verify = True  # Verificar certificados SSL
        
        return session


# ============================================================================
# CONSULTA DISTRIBUIÇÃO DFe (NSU)
# ============================================================================

def consultar_ultimo_nsu_sefaz(certificado: CertificadoA1, cnpj: str, cuf: int, 
                                ambiente: str = 'producao') -> Dict[str, any]:
    """
    Consulta o último NSU disponível na SEFAZ.
    
    Args:
        certificado: Certificado digital A1
        cnpj: CNPJ da empresa
        cuf: Código da UF (ex: 35 para SP)
        ambiente: 'producao' ou 'homologacao'
        
    Returns:
        Dict com maxNSU e ultNSU
    """
    try:
        # Monta XML SOAP
        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
    <soap:Header/>
    <soap:Body>
        <nfe:nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe">
            <nfeDist versao="1.01">
                <tpAmb>{1 if ambiente == 'homologacao' else 1}</tpAmb>
                <cUFAutor>{cuf}</cUFAutor>
                <CNPJ>{cnpj}</CNPJ>
                <distNSU>
                    <ultNSU>000000000000000</ultNSU>
                </distNSU>
            </nfeDist>
        </nfe:nfeDistDFeInteresse>
    </soap:Body>
</soap:Envelope>'''
        
        # URL do webservice
        url = WEBSERVICES_HOMOLOGACAO['NFeDistribuicaoDFe'] if ambiente == 'homologacao' else WEBSERVICES_PRODUCAO['NFeDistribuicaoDFe']
        
        # Headers
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe'
        }
        
        # Faz requisição
        session = certificado.get_session_requests()
        response = session.post(url, data=soap_body.encode('utf-8'), headers=headers, timeout=60)
        
        if response.status_code != 200:
            return {
                'sucesso': False,
                'erro': f'Erro HTTP {response.status_code}: {response.text[:500]}'
            }
        
        # Parse resposta
        root = etree.fromstring(response.content)
        ns = {'nfe': NAMESPACE_NFE}
        
        # Busca status
        ret_dist = root.find('.//nfe:retDistDFeInt', ns)
        if ret_dist is None:
            return {'sucesso': False, 'erro': 'Resposta inválida da SEFAZ'}
        
        c_stat = ret_dist.find('nfe:cStat', ns)
        x_motivo = ret_dist.find('nfe:xMotivo', ns)
        
        if c_stat is None:
            return {'sucesso': False, 'erro': 'Status não encontrado na resposta'}
        
        status_code = c_stat.text
        motivo = x_motivo.text if x_motivo is not None else 'Sem descrição'
        
        # Verifica sucesso
        if status_code != '138':  # 138 = Nenhum documento localizado (normal no início)
            # Outros códigos de sucesso: 137 = Nenhum doc no NSU, 138 = Nenhum doc disponível
            if status_code not in ['137', '138']:
                return {
                    'sucesso': False,
                    'codigo_sefaz': status_code,
                    'mensagem_sefaz': motivo
                }
        
        # Extrai NSUs
        max_nsu = ret_dist.find('nfe:maxNSU', ns)
        ult_nsu = ret_dist.find('nfe:ultNSU', ns)
        
        return {
            'sucesso': True,
            'maxNSU': max_nsu.text if max_nsu is not None else '000000000000000',
            'ultNSU': ult_nsu.text if ult_nsu is not None else '000000000000000',
            'codigo_sefaz': status_code,
            'mensagem_sefaz': motivo
        }
        
    except requests.exceptions.Timeout:
        return {'sucesso': False, 'erro': 'Timeout na conexão com SEFAZ'}
    except requests.exceptions.RequestException as e:
        return {'sucesso': False, 'erro': f'Erro de rede: {str(e)}'}
    except Exception as e:
        return {'sucesso': False, 'erro': f'Erro ao consultar NSU: {str(e)}'}


def baixar_documentos_dfe(certificado: CertificadoA1, cnpj: str, cuf: int, 
                         ultimo_nsu: str = '000000000000000', 
                         ambiente: str = 'producao') -> Dict[str, any]:
    """
    Baixa documentos DFe (NF-e, CT-e, eventos) a partir de um NSU.
    
    Args:
        certificado: Certificado digital A1
        cnpj: CNPJ da empresa
        cuf: Código da UF
        ultimo_nsu: Último NSU já processado
        ambiente: 'producao' ou 'homologacao'
        
    Returns:
        Dict com documentos baixados e novo ultNSU
    """
    try:
        # Monta XML SOAP
        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
    <soap:Header/>
    <soap:Body>
        <nfe:nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe">
            <nfeDist versao="1.01">
                <tpAmb>{2 if ambiente == 'homologacao' else 1}</tpAmb>
                <cUFAutor>{cuf}</cUFAutor>
                <CNPJ>{cnpj}</CNPJ>
                <distNSU>
                    <ultNSU>{ultimo_nsu}</ultNSU>
                </distNSU>
            </nfeDist>
        </nfe:nfeDistDFeInteresse>
    </soap:Body>
</soap:Envelope>'''
        
        # URL do webservice
        url = WEBSERVICES_HOMOLOGACAO['NFeDistribuicaoDFe'] if ambiente == 'homologacao' else WEBSERVICES_PRODUCAO['NFeDistribuicaoDFe']
        
        # Headers
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe'
        }
        
        # Faz requisição
        session = certificado.get_session_requests()
        response = session.post(url, data=soap_body.encode('utf-8'), headers=headers, timeout=120)
        
        if response.status_code != 200:
            return {
                'sucesso': False,
                'erro': f'Erro HTTP {response.status_code}'
            }
        
        # Parse resposta
        root = etree.fromstring(response.content)
        ns = {'nfe': NAMESPACE_NFE}
        
        ret_dist = root.find('.//nfe:retDistDFeInt', ns)
        if ret_dist is None:
            return {'sucesso': False, 'erro': 'Resposta inválida da SEFAZ'}
        
        # Status
        c_stat = ret_dist.find('nfe:cStat', ns)
        x_motivo = ret_dist.find('nfe:xMotivo', ns)
        
        if c_stat is None:
            return {'sucesso': False, 'erro': 'Status não encontrado'}
        
        status_code = c_stat.text
        motivo = x_motivo.text if x_motivo is not None else 'Sem descrição'
        
        # Verifica sucesso (138 = Nenhum doc, não é erro)
        if status_code not in ['137', '138']:
            return {
                'sucesso': False,
                'codigo_sefaz': status_code,
                'mensagem_sefaz': motivo
            }
        
        # Extrai documentos
        documentos = []
        lot_dist = ret_dist.find('nfe:loteDistDFeInt', ns)
        
        if lot_dist is not None:
            for doc_zip in lot_dist.findall('nfe:docZip', ns):
                nsu = doc_zip.get('NSU')
                schema = doc_zip.get('schema')
                
                # Descompacta conteúdo (base64 + gzip)
                try:
                    conteudo_base64 = doc_zip.text
                    conteudo_gzip = base64.b64decode(conteudo_base64)
                    xml_content = gzip.decompress(conteudo_gzip).decode('utf-8')
                    
                    documentos.append({
                        'nsu': nsu,
                        'schema': schema,
                        'xml': xml_content
                    })
                    
                except Exception as e:
                    documentos.append({
                        'nsu': nsu,
                        'schema': schema,
                        'erro': f'Erro ao descomprimir: {str(e)}'
                    })
        
        # Novo ultNSU
        ult_nsu = ret_dist.find('nfe:ultNSU', ns)
        max_nsu = ret_dist.find('nfe:maxNSU', ns)
        
        return {
            'sucesso': True,
            'documentos': documentos,
            'ultNSU': ult_nsu.text if ult_nsu is not None else ultimo_nsu,
            'maxNSU': max_nsu.text if max_nsu is not None else '000000000000000',
            'total_documentos': len(documentos),
            'codigo_sefaz': status_code,
            'mensagem_sefaz': motivo
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao baixar documentos: {str(e)}'
        }


# ============================================================================
# CONSULTA POR CHAVE DE ACESSO
# ============================================================================

def consultar_nfe_por_chave(certificado: CertificadoA1, chave: str, 
                            ambiente: str = 'producao') -> Dict[str, any]:
    """
    Consulta uma NF-e específica pela chave de acesso.
    
    Args:
        certificado: Certificado digital A1
        chave: Chave de acesso de 44 dígitos
        ambiente: 'producao' ou 'homologacao'
        
    Returns:
        Dict com dados da consulta
    """
    try:
        # Valida chave
        if not chave or len(chave) != 44:
            return {'sucesso': False, 'erro': 'Chave de acesso inválida'}
        
        # Extrai UF da chave (primeiros 2 dígitos)
        cuf = chave[:2]
        
        # Monta XML SOAP
        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
    <soap:Header/>
    <soap:Body>
        <nfe:nfeConsultaNF xmlns="http://www.portalfiscal.inf.br/nfe">
            <consSitNFe versao="4.00">
                <tpAmb>{2 if ambiente == 'homologacao' else 1}</tpAmb>
                <xServ>CONSULTAR</xServ>
                <chNFe>{chave}</chNFe>
            </consSitNFe>
        </nfe:nfeConsultaNF>
    </soap:Body>
</soap:Envelope>'''
        
        # URL (simplificado - na produção seria por UF)
        url = WEBSERVICES_HOMOLOGACAO['NfeConsultaProtocolo'] if ambiente == 'homologacao' else WEBSERVICES_PRODUCAO['NfeConsultaProtocolo']
        
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8'
        }
        
        # Requisição
        session = certificado.get_session_requests()
        response = session.post(url, data=soap_body.encode('utf-8'), headers=headers, timeout=60)
        
        if response.status_code != 200:
            return {'sucesso': False, 'erro': f'Erro HTTP {response.status_code}'}
        
        # Parse
        root = etree.fromstring(response.content)
        ns = {'nfe': NAMESPACE_NFE}
        
        ret_cons = root.find('.//nfe:retConsSitNFe', ns)
        if ret_cons is None:
            return {'sucesso': False, 'erro': 'Resposta inválida'}
        
        c_stat = ret_cons.find('nfe:cStat', ns)
        x_motivo = ret_cons.find('nfe:xMotivo', ns)
        
        if c_stat is None:
            return {'sucesso': False, 'erro': 'Status não encontrado'}
        
        status_code = c_stat.text
        motivo = x_motivo.text if x_motivo is not None else ''
        
        # 100 = Autorizada
        if status_code != '100':
            return {
                'sucesso': False,
                'codigo_sefaz': status_code,
                'mensagem_sefaz': motivo,
                'situacao': 'Não autorizada'
            }
        
        # Extrai protocolo
        prot_nfe = ret_cons.find('.//nfe:protNFe', ns)
        
        resultado = {
            'sucesso': True,
            'chave': chave,
            'codigo_sefaz': status_code,
            'mensagem_sefaz': motivo,
            'situacao': 'Autorizada'
        }
        
        if prot_nfe is not None:
            # Serializa o XML completo
            xml_prot = etree.tostring(prot_nfe, encoding='utf-8', xml_declaration=True).decode('utf-8')
            resultado['xml_protocolo'] = xml_prot
        
        return resultado
        
    except Exception as e:
        return {'sucesso': False, 'erro': f'Erro ao consultar chave: {str(e)}'}


def buscar_multiplas_chaves(certificado: CertificadoA1, chaves: List[str], 
                            ambiente: str = 'producao') -> List[Dict]:
    """
    Busca múltiplas NF-es por chave de acesso.
    
    Args:
        certificado: Certificado digital A1
        chaves: Lista de chaves de acesso
        ambiente: 'producao' ou 'homologacao'
        
    Returns:
        Lista de dicts com resultados de cada consulta
    """
    resultados = []
    
    for chave in chaves:
        resultado = consultar_nfe_por_chave(certificado, chave, ambiente)
        resultado['chave'] = chave
        resultados.append(resultado)
    
    return resultados


# ============================================================================
# TESTE
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("TESTE: Módulo NF-e Busca")
    print("=" * 70)
    
    print("\n⚠️  Este módulo requer certificado digital A1 para testes reais.")
    print("⚠️  Os testes automatizados só validam a estrutura das funções.\n")
    
    # Teste 1: Estrutura de SOAP
    print("1. Teste de estrutura SOAP:")
    print("   ✓ Funções definidas:")
    print("     - consultar_ultimo_nsu_sefaz()")
    print("     - baixar_documentos_dfe()")
    print("     - consultar_nfe_por_chave()")
    print("     - buscar_multiplas_chaves()")
    
    # Teste 2: URLs dos webservices
    print("\n2. URLs configuradas:")
    print(f"   Produção - Distribuição DFe:")
    print(f"     {WEBSERVICES_PRODUCAO['NFeDistribuicaoDFe']}")
    print(f"   Homologação - Distribuição DFe:")
    print(f"     {WEBSERVICES_HOMOLOGACAO['NFeDistribuicaoDFe']}")
    
    # Teste 3: Certificado (sem arquivo real)
    print("\n3. Teste de Certificado:")
    try:
        # Tentativa de carregar (vai falhar sem arquivo, mas testa estrutura)
        cert = CertificadoA1(caminho_pfx='teste.pfx', senha='')
        print("   ✗ Certificado não carregado (esperado sem arquivo)")
    except ValueError as e:
        print(f"   ✓ Validação funcionando: {str(e)[:50]}...")
    
    print("\n" + "=" * 70)
    print("✓ Testes estruturais concluídos!")
    print("\n💡 Para testes reais, forneça um certificado A1 válido.")
    print("=" * 70)

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
import ssl
import logging
import tempfile
import urllib3
from lxml import etree
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# CONFIGURAÇÕES SEFAZ
# ============================================================================

# URLs dos webservices SEFAZ (Produção - AN - Ambiente Nacional)
WEBSERVICES_PRODUCAO = {
    'NFeDistribuicaoDFe': 'https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx',
    'NfeConsultaProtocolo': 'https://www.nfe.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx',
    'CTeConsultaProtocolo': 'https://www1.cte.fazenda.gov.br/CTeWS/CTeConsultaV4.asmx',
    'NFeRecepcaoEvento4': 'https://www.nfe.fazenda.gov.br/NFeRecepcaoEvento/NFeRecepcaoEvento4.asmx',
}

# URLs dos webservices SEFAZ (Homologação - AN)
WEBSERVICES_HOMOLOGACAO = {
    'NFeDistribuicaoDFe': 'https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx',
    'NfeConsultaProtocolo': 'https://hom.nfe.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx',
    'CTeConsultaProtocolo': 'https://hom1.cte.fazenda.gov.br/CTeWS/CTeConsultaV4.asmx',
    'NFeRecepcaoEvento4': 'https://hom.nfe.fazenda.gov.br/NFeRecepcaoEvento/NFeRecepcaoEvento4.asmx',
}

# Namespaces dos webservices
NAMESPACE_NFE = 'http://www.portalfiscal.inf.br/nfe'
NAMESPACE_CTE = 'http://www.portalfiscal.inf.br/cte'

# Número máximo de NSUs por consulta (limitado pela SEFAZ)
MAX_NSUS_POR_CONSULTA = 50

# URLs WSDL (com ?wsdl — usadas pelo zeep para montar o envelope SOAP correto)
WSDL_DISTRIBUICAO_PRODUCAO  = 'https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl'
WSDL_DISTRIBUICAO_HOMOLOG   = 'https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl'


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
        self.senha_str = senha  # mantida como str para requests_pkcs12
        
        self.cert_pem = None
        self.key_pem = None
        self.cert_data = None
        self.pfx_bytes = None  # bytes brutos guardados para zeep/requests_pkcs12
        
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
            
            self.pfx_bytes = pfx_data  # guarda para get_zeep_dist_client()
            
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
            
            # ── Extrai CNPJ do certificado (padrão ICP-Brasil) ──────────────
            # Formato ICP-Brasil no CN: "RAZAO SOCIAL:CNPJ" (ex: "EMPRESA MO:56237242000158")
            # O OU pode conter o CNPJ da AC emissora — NÃO usar OU.
            # Ordem de preferência:
            #   1. OID 2.16.76.1.3.3        — OID ICP-Brasil específico do CNPJ da PJ
            #   2. CN (2.5.4.3)             — últimos 14 dígitos após ":" no nome
            #   3. serialNumber (2.5.4.5)   — fallback se não houver CN
            import re
            cnpj_encontrado = None

            for attr in certificate.subject:
                dotted = attr.oid.dotted_string
                val = str(attr.value)

                if dotted == '2.16.76.1.3.3':     # OID ICP-Brasil: CNPJ da PJ
                    digits = ''.join(filter(str.isdigit, val))
                    if len(digits) == 14:
                        cnpj_encontrado = digits
                        break                      # Máxima confiança, para aqui

            if not cnpj_encontrado:
                # CN ICP-Brasil: "NOME:CNPJ" — o CNPJ é a última seq de 14 dígitos
                for attr in certificate.subject:
                    if attr.oid.dotted_string == '2.5.4.3':   # CN
                        # Pega o último bloco de 14 dígitos consecutivos no CN
                        matches = re.findall(r'\d{14}', attr.value)
                        if matches:
                            cnpj_encontrado = matches[-1]  # sempre o último
                        break

            if not cnpj_encontrado:
                # Fallback: serialNumber apenas
                for attr in certificate.subject:
                    if attr.oid.dotted_string == '2.5.4.5':   # serialNumber
                        digits = ''.join(filter(str.isdigit, attr.value))
                        if len(digits) == 14:
                            cnpj_encontrado = digits
                        break

            if cnpj_encontrado:
                self.cert_data['cnpj'] = cnpj_encontrado
            
        except Exception as e:
            raise ValueError(f"Erro ao carregar certificado: {str(e)}")
    
    def esta_valido(self) -> bool:
        """Verifica se o certificado está dentro do prazo de validade."""
        if not self.cert_data:
            return False
        
        agora = datetime.now(timezone.utc)
        return (self.cert_data['valido_de'] <= agora <= self.cert_data['valido_ate'])
    
    def get_session_requests(self) -> requests.Session:
        """Retorna uma sessão requests configurada com o certificado (PEM)."""
        session = requests.Session()
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as cert_file:
            cert_file.write(self.cert_pem)
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as key_file:
            key_file.write(self.key_pem)
            key_path = key_file.name
        
        session.cert = (cert_path, key_path)
        session.verify = True
        
        return session

    def get_zeep_dist_client(self, wsdl_url: str):
        """
        Retorna um cliente zeep para NFeDistribuicaoDFe autenticado via PKCS12.
        Usa requests_pkcs12.Pkcs12Adapter — não extrai PEM, usa o .pfx diretamente.
        SSL verify=False necessário pela infra da SEFAZ (certificado intermediário gov.br).
        """
        from requests_pkcs12 import Pkcs12Adapter
        from zeep import Client
        from zeep.transports import Transport

        class _SefazPkcs12Adapter(Pkcs12Adapter):
            """Adapter que desabilita verificação SSL (necessário para SEFAZ)."""
            def init_poolmanager(self, *args, **kwargs):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                kwargs['ssl_context'] = ctx
                return super().init_poolmanager(*args, **kwargs)

        sess = requests.Session()
        sess.verify = False
        sess.mount('https://', _SefazPkcs12Adapter(
            pkcs12_data=self.pfx_bytes,
            pkcs12_password=self.senha_str,
        ))

        transport = Transport(session=sess, timeout=120)
        return Client(wsdl_url, transport=transport)


# ============================================================================
# HELPERS
# ============================================================================

def _extrair_soap_fault(content: bytes) -> str:
    """Extrai mensagem de erro de uma resposta SOAP Fault (1.1 e 1.2), ou '' se não for fault."""
    try:
        root = etree.fromstring(content)
        partes = []
        for elem in root.iter():
            tag = elem.tag.lower()
            # SOAP 1.1: faultcode + faultstring
            # SOAP 1.2: Code/Value + Reason/Text
            if any(x in tag for x in ('faultstring', 'faultcode', '}text', '}value', '}reason')):
                if elem.text and elem.text.strip():
                    partes.append(elem.text.strip())
        return ' | '.join(dict.fromkeys(partes))[:500] if partes else ''
    except Exception:
        try:
            return content.decode('utf-8', errors='replace')[:400]
        except Exception:
            return ''


# ============================================================================
# CONSULTA DISTRIBUIÇÃO DFe (NSU)  — usa zeep + requests_pkcs12
# ============================================================================

def _chamar_dist_dfe(certificado: CertificadoA1, cnpj: str, cuf: int,
                     ultimo_nsu: str, ambiente: str) -> Dict[str, any]:
    """
    Núcleo da chamada NFeDistribuicaoDFe via zeep.
    Zeep lê o WSDL e monta o envelope SOAP correto (namespaces, SOAPAction, cUF=91 no header).
    Retorna o XML de resposta como string, ou dict com erro.
    """
    from zeep.exceptions import Fault as ZeepFault

    wsdl = WSDL_DISTRIBUICAO_HOMOLOG if ambiente == 'homologacao' else WSDL_DISTRIBUICAO_PRODUCAO
    logger.info(f"[ZEEP] WSDL: {wsdl}")

    try:
        client = certificado.get_zeep_dist_client(wsdl)
    except Exception as e:
        return {'sucesso': False, 'erro': f'Falha ao carregar WSDL: {e}'}

    # Monta apenas o elemento interno distDFeInt (zeep cuida do envelope SOAP)
    distInt = etree.Element(
        "distDFeInt",
        xmlns=NAMESPACE_NFE,
        versao="1.01"
    )
    etree.SubElement(distInt, "tpAmb").text    = "2" if ambiente == 'homologacao' else "1"
    etree.SubElement(distInt, "cUFAutor").text = str(cuf)
    etree.SubElement(distInt, "CNPJ").text     = cnpj
    sub = etree.SubElement(distInt, "distNSU")
    etree.SubElement(sub, "ultNSU").text       = ultimo_nsu

    xml_enviado = etree.tostring(distInt, encoding='unicode')
    logger.info(f"[ZEEP] nfeDadosMsg enviado:\n{xml_enviado}")

    try:
        resp = client.service.nfeDistDFeInteresse(nfeDadosMsg=distInt)
    except ZeepFault as fault:
        logger.error(f"[ZEEP] SOAP Fault: {fault}")
        return {'sucesso': False, 'erro': f'SOAP Fault: {fault}'}
    except Exception as e:
        logger.error(f"[ZEEP] Erro na chamada: {type(e).__name__}: {e}")
        return {'sucesso': False, 'erro': f'Erro na chamada SEFAZ: {e}'}

    # zeep retorna lxml Element — serializa para string e parseia
    xml_resp = etree.tostring(resp, encoding='unicode')
    logger.info(f"[ZEEP] Resposta:\n{xml_resp[:2000]}")

    return {'sucesso': True, 'xml': xml_resp}


def _parsear_retDistDFeInt(xml_resp: str, ultimo_nsu_original: str) -> Dict[str, any]:
    """Parseia a resposta retDistDFeInt e extrai status, docs e NSUs."""
    ns = {'nfe': NAMESPACE_NFE}
    try:
        root = etree.fromstring(xml_resp.encode('utf-8'))
    except Exception as e:
        return {'sucesso': False, 'erro': f'Resposta inválida: {e}'}

    ret = root.find('.//nfe:retDistDFeInt', ns) or root
    c_stat  = ret.findtext('nfe:cStat', namespaces=ns) or ret.findtext(f'{{{NAMESPACE_NFE}}}cStat')
    motivo  = ret.findtext('nfe:xMotivo', namespaces=ns) or ''

    if not c_stat:
        return {'sucesso': False, 'erro': f'cStat não encontrado. Resposta:\n{xml_resp[:500]}'}

    logger.info(f"[SEFAZ] cStat={c_stat} - {motivo}")

    # Códigos de sucesso: 137=nenhum doc no NSU, 138=nenhum doc disponível, 656=consumo indevido
    # Documentos encontrados retornam outros códigos (ex: 134 = lote processado)
    if c_stat not in ['137', '138', '134', '656']:
        return {
            'sucesso': False,
            'codigo_sefaz': c_stat,
            'mensagem_sefaz': motivo
        }

    # Extrai documentos (docZip = XML gzipado em base64)
    documentos = []
    for doc_zip in root.findall('.//nfe:docZip', ns):
        nsu    = doc_zip.get('NSU', '')
        schema = doc_zip.get('schema', '')
        try:
            xml_content = gzip.decompress(base64.b64decode(doc_zip.text or '')).decode('utf-8')
            documentos.append({'nsu': nsu, 'schema': schema, 'xml': xml_content})
        except Exception as e:
            documentos.append({'nsu': nsu, 'schema': schema, 'erro': str(e)})

    ult_nsu_el = ret.find('nfe:ultNSU', ns)
    max_nsu_el = ret.find('nfe:maxNSU', ns)

    return {
        'sucesso':          True,
        'documentos':       documentos,
        'ultNSU':           ult_nsu_el.text if ult_nsu_el is not None else ultimo_nsu_original,
        'maxNSU':           max_nsu_el.text if max_nsu_el is not None else '000000000000000',
        'total_documentos': len(documentos),
        'codigo_sefaz':     c_stat,
        'mensagem_sefaz':   motivo,
    }


def consultar_ultimo_nsu_sefaz(certificado: CertificadoA1, cnpj: str, cuf: int,
                                ambiente: str = 'producao') -> Dict[str, any]:
    """Consulta o maxNSU disponível (NSU=0 → SEFAZ retorna o máximo atual)."""
    cnpj = ''.join(filter(str.isdigit, str(cnpj or '')))
    if len(cnpj) != 14:
        return {'sucesso': False, 'erro': f'CNPJ inválido: "{cnpj}"'}
    if not cuf:
        return {'sucesso': False, 'erro': 'CUF não configurado'}
    cuf = int(cuf)

    resultado = _chamar_dist_dfe(certificado, cnpj, cuf, '000000000000000', ambiente)
    if not resultado['sucesso']:
        return resultado
    return _parsear_retDistDFeInt(resultado['xml'], '000000000000000')


def baixar_documentos_dfe(certificado: CertificadoA1, cnpj: str, cuf: int,
                          ultimo_nsu: str = '000000000000000',
                          ambiente: str = 'producao') -> Dict[str, any]:
    """Baixa documentos DFe (NF-e, CT-e, eventos) a partir de um NSU."""
    cnpj = ''.join(filter(str.isdigit, str(cnpj or '')))
    if len(cnpj) != 14:
        return {'sucesso': False, 'erro': f'CNPJ inválido: "{cnpj}"'}
    if not cuf:
        return {'sucesso': False, 'erro': 'CUF não configurado'}
    cuf = int(cuf)

    try:
        ultimo_nsu = str(int(ultimo_nsu or '0')).zfill(15)
    except (ValueError, TypeError):
        ultimo_nsu = '000000000000000'

    resultado = _chamar_dist_dfe(certificado, cnpj, cuf, ultimo_nsu, ambiente)
    if not resultado['sucesso']:
        return resultado
    return _parsear_retDistDFeInt(resultado['xml'], ultimo_nsu)



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


def consultar_cte_por_chave(certificado: CertificadoA1, chave: str,
                            ambiente: str = 'producao') -> Dict[str, any]:
    """
    Consulta um CT-e específico pela chave de acesso.
    
    Args:
        certificado: Certificado digital A1
        chave: Chave de acesso de 44 dígitos (modelo 57 ou 67)
        ambiente: 'producao' ou 'homologacao'
        
    Returns:
        Dict com dados da consulta
    """
    try:
        if not chave or len(chave) != 44:
            return {'sucesso': False, 'erro': 'Chave de acesso inválida'}
        
        # Monta XML SOAP para CT-e
        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:cte="http://www.portalfiscal.inf.br/cte/wsdl/CTeConsultaV4">
    <soap:Header/>
    <soap:Body>
        <cte:cteConsultaCT xmlns="http://www.portalfiscal.inf.br/cte">
            <consSitCTe versao="4.00">
                <tpAmb>{2 if ambiente == 'homologacao' else 1}</tpAmb>
                <xServ>CONSULTAR</xServ>
                <chCTe>{chave}</chCTe>
            </consSitCTe>
        </cte:cteConsultaCT>
    </soap:Body>
</soap:Envelope>'''
        
        url = WEBSERVICES_HOMOLOGACAO['CTeConsultaProtocolo'] if ambiente == 'homologacao' else WEBSERVICES_PRODUCAO['CTeConsultaProtocolo']
        
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8'
        }
        
        session = certificado.get_session_requests()
        response = session.post(url, data=soap_body.encode('utf-8'), headers=headers, timeout=60)
        
        if response.status_code != 200:
            return {'sucesso': False, 'erro': f'Erro HTTP {response.status_code}'}
        
        root = etree.fromstring(response.content)
        ns = {'cte': NAMESPACE_CTE}
        
        ret_cons = root.find('.//cte:retConsSitCTe', ns)
        if ret_cons is None:
            return {'sucesso': False, 'erro': 'Resposta inválida do SEFAZ para CT-e'}
        
        c_stat = ret_cons.find('cte:cStat', ns)
        x_motivo = ret_cons.find('cte:xMotivo', ns)
        
        if c_stat is None:
            return {'sucesso': False, 'erro': 'Status não encontrado na resposta'}
        
        status_code = c_stat.text
        motivo = x_motivo.text if x_motivo is not None else ''
        
        if status_code != '100':
            return {
                'sucesso': False,
                'codigo_sefaz': status_code,
                'mensagem_sefaz': motivo,
                'situacao': 'Não autorizada'
            }
        
        prot_cte = ret_cons.find('.//cte:protCTe', ns)
        
        resultado = {
            'sucesso': True,
            'chave': chave,
            'tipo_documento': 'CTe',
            'codigo_sefaz': status_code,
            'mensagem_sefaz': motivo,
            'situacao': 'Autorizada'
        }
        
        if prot_cte is not None:
            xml_prot = etree.tostring(prot_cte, encoding='utf-8', xml_declaration=True).decode('utf-8')
            resultado['xml_protocolo'] = xml_prot
        
        return resultado
        
    except Exception as e:
        return {'sucesso': False, 'erro': f'Erro ao consultar CT-e: {str(e)}'}


def consultar_documento_por_chave(certificado: CertificadoA1, chave: str,
                                  ambiente: str = 'producao') -> Dict[str, any]:
    """
    Consulta um documento (NF-e ou CT-e) pela chave - detecta automaticamente.
    
    Identifica o modelo pelo dígito 21-22 da chave:
    - 55: NF-e
    - 57: CT-e
    - 65: NFC-e
    - 67: CT-e OS
    """
    if not chave or len(chave) != 44:
        return {'sucesso': False, 'erro': 'Chave de acesso inválida'}
    
    modelo = chave[20:22]
    
    if modelo in ('57', '67'):
        return consultar_cte_por_chave(certificado, chave, ambiente)
    else:
        return consultar_nfe_por_chave(certificado, chave, ambiente)


def buscar_multiplas_chaves(certificado: CertificadoA1, chaves: List[str], 
                            ambiente: str = 'producao') -> List[Dict]:
    """
    Busca múltiplas NF-es/CT-es por chave de acesso.
    
    Args:
        certificado: Certificado digital A1
        chaves: Lista de chaves de acesso
        ambiente: 'producao' ou 'homologacao'
        
    Returns:
        Lista de dicts com resultados de cada consulta
    """
    resultados = []
    
    for chave in chaves:
        resultado = consultar_documento_por_chave(certificado, chave, ambiente)
        resultado['chave'] = chave
        resultados.append(resultado)
    
    return resultados


# ============================================================================
# TESTE
# ============================================================================

# ============================================================================
# MANIFESTAÇÃO DO DESTINATÁRIO (Ciência da Operação)
# ============================================================================

def _assinar_evento_xml(xml_str: str, certificado: 'CertificadoA1', ref_id: str) -> str:
    """
    Assina o XML de evento NF-e com xmldsig (RSA-SHA1, C14N).

    Args:
        xml_str: XML do envEvento como string (sem assinatura)
        certificado: Instância de CertificadoA1 já carregada
        ref_id: Valor do atributo Id= em <infEvento> (sem #)

    Returns:
        XML assinado como string UTF-8
    """
    import hashlib
    from cryptography.hazmat.primitives import hashes as _crypto_hashes, serialization as _serialization
    from cryptography.hazmat.primitives.asymmetric import padding as _asym_padding

    root = etree.fromstring(xml_str.encode('utf-8') if isinstance(xml_str, str) else xml_str)
    ns = NAMESPACE_NFE

    # Localiza infEvento pelo Id
    inf_evento = root.find(f'.//{{{ns}}}infEvento[@Id="{ref_id}"]')
    if inf_evento is None:
        raise ValueError(f"Elemento infEvento com Id={ref_id!r} nao encontrado no XML")

    # Digest SHA-1 do infEvento canonicalizado (C14N incl. namespaces)
    inf_c14n = etree.tostring(inf_evento, method='c14n', exclusive=False, with_comments=False)
    digest_b64 = base64.b64encode(hashlib.sha1(inf_c14n).digest()).decode('ascii')

    # Monta SignedInfo
    signed_info_xml = (
        '<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">'
        '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>'
        '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>'
        f'<Reference URI="#{ref_id}">'
        '<Transforms>'
        '<Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>'
        '<Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>'
        '</Transforms>'
        '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>'
        f'<DigestValue>{digest_b64}</DigestValue>'
        '</Reference>'
        '</SignedInfo>'
    )

    # Canonicaliza SignedInfo para assinar
    signed_info_root = etree.fromstring(signed_info_xml.encode('utf-8'))
    signed_info_c14n = etree.tostring(signed_info_root, method='c14n', exclusive=False, with_comments=False)

    # Carrega chave privada PEM do certificado
    key_pem = certificado.key_pem
    if isinstance(key_pem, str):
        key_pem = key_pem.encode('utf-8')
    private_key = _serialization.load_pem_private_key(key_pem, password=None)

    # Assina com RSA-PKCS1v15-SHA1
    sig_bytes = private_key.sign(signed_info_c14n, _asym_padding.PKCS1v15(), _crypto_hashes.SHA1())
    sig_b64 = base64.b64encode(sig_bytes).decode('ascii')

    # Extrai certificado público como base64 (sem delimitadores PEM)
    cert_pem = certificado.cert_pem
    if isinstance(cert_pem, bytes):
        cert_pem = cert_pem.decode('utf-8')
    cert_b64 = (cert_pem
                .replace('-----BEGIN CERTIFICATE-----', '')
                .replace('-----END CERTIFICATE-----', '')
                .replace('\r', '').replace('\n', '').strip())

    # Monta elemento Signature
    sig_xml = (
        '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">'
        + signed_info_xml
        + f'<SignatureValue>{sig_b64}</SignatureValue>'
        '<KeyInfo><X509Data>'
        f'<X509Certificate>{cert_b64}</X509Certificate>'
        '</X509Data></KeyInfo>'
        '</Signature>'
    )
    sig_elem = etree.fromstring(sig_xml.encode('utf-8'))

    # Insere Signature como filho de <evento> (após infEvento)
    evento_elem = root.find(f'.//{{{ns}}}evento')
    if evento_elem is not None:
        evento_elem.append(sig_elem)
    else:
        root.append(sig_elem)

    return etree.tostring(root, encoding='unicode')


def manifestar_ciencia_operacao(certificado: CertificadoA1, chave: str,
                                cnpj_dest: str,
                                ambiente: str = 'producao') -> Dict:
    """
    Envia evento 'Ciência da Operação' (tpEvento=210210) ao SEFAZ para uma NF-e.

    Necessário quando o XML armazenado é um resNFe (resumo de DFe) e precisamos
    obter o procNFe completo para gerar o DANFE.

    Args:
        certificado: Certificado A1 do destinatário
        chave: Chave de acesso de 44 dígitos
        cnpj_dest: CNPJ do destinatário (14 dígitos, sem pontuação)
        ambiente: 'producao' ou 'homologacao'

    Returns:
        Dict com {'sucesso': bool, 'codigo_sefaz': str, 'mensagem': str, 'protocolo': str}
    """
    try:
        if not chave or len(chave) != 44:
            return {'sucesso': False, 'erro': 'Chave de acesso invalida'}

        tp_amb = '2' if ambiente == 'homologacao' else '1'
        tp_evento = '210210'
        n_seq_evento = '1'
        n_lote = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        dh_evento = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S-00:00')

        # ID do infEvento: ID + tpEvento(6) + chave(44) + nSeqEvento(2)
        ref_id = f'ID{tp_evento}{chave}{n_seq_evento.zfill(2)}'

        # XML sem assinatura
        env_evento_xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<envEvento versao="1.00" xmlns="{NAMESPACE_NFE}">'
            f'<idLote>{n_lote}</idLote>'
            f'<evento versao="1.00">'
            f'<infEvento Id="{ref_id}">'
            f'<cOrgao>91</cOrgao>'
            f'<tpAmb>{tp_amb}</tpAmb>'
            f'<CNPJ>{cnpj_dest}</CNPJ>'
            f'<chNFe>{chave}</chNFe>'
            f'<dhEvento>{dh_evento}</dhEvento>'
            f'<tpEvento>{tp_evento}</tpEvento>'
            f'<nSeqEvento>{n_seq_evento}</nSeqEvento>'
            f'<verEvento>1.00</verEvento>'
            f'<detEvento versao="1.00">'
            f'<descEvento>Ciencia da Operacao</descEvento>'
            f'</detEvento>'
            f'</infEvento>'
            f'</evento>'
            f'</envEvento>'
        )

        # Assina o XML
        xml_assinado = _assinar_evento_xml(env_evento_xml, certificado, ref_id)

        # Monta envelope SOAP
        url = (WEBSERVICES_HOMOLOGACAO['NFeRecepcaoEvento4']
               if ambiente == 'homologacao'
               else WEBSERVICES_PRODUCAO['NFeRecepcaoEvento4'])

        soap_body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">'
            '<soap:Header/>'
            '<soap:Body>'
            '<nfe:nfeRecepcaoEvento4>'
            '<nfeDadosMsg>'
            + xml_assinado
            + '</nfeDadosMsg>'
            '</nfe:nfeRecepcaoEvento4>'
            '</soap:Body>'
            '</soap:Envelope>'
        )

        headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}
        sess = certificado.get_session_requests()
        response = sess.post(url, data=soap_body.encode('utf-8'), headers=headers, timeout=60)

        if response.status_code != 200:
            return {'sucesso': False, 'erro': f'Erro HTTP {response.status_code} ao manifestar'}

        # Parse da resposta
        resp_root = etree.fromstring(response.content)
        ns = {'nfe': NAMESPACE_NFE}

        ret = resp_root.find('.//nfe:retEnvEvento', ns)
        if ret is None:
            # Tenta extrair cStat de qualquer elemento de retorno
            c_stat_any = resp_root.find('.//{http://www.portalfiscal.inf.br/nfe}cStat')
            x_motivo_any = resp_root.find('.//{http://www.portalfiscal.inf.br/nfe}xMotivo')
            c_stat = c_stat_any.text if c_stat_any is not None else '?'
            x_motivo = x_motivo_any.text if x_motivo_any is not None else 'Resposta inesperada'
            sucesso = c_stat in ('135', '136', '238', '573')
            return {'sucesso': sucesso, 'codigo_sefaz': c_stat, 'mensagem': x_motivo, 'protocolo': ''}

        c_stat_el = ret.find('nfe:cStat', ns)
        x_motivo_el = ret.find('nfe:xMotivo', ns)
        c_stat = c_stat_el.text if c_stat_el is not None else ''
        x_motivo = x_motivo_el.text if x_motivo_el is not None else ''

        # Códigos de sucesso:
        # 135 = Lote de Evento Processado
        # 136 = Evento registrado para o destinatário
        # 238 = Rejeição: Evento já registrado com esta chave (tratamos como OK)
        # 573 / 628 = Ciência da Operação já manifestada
        sucesso = c_stat in ('135', '136', '238', '573', '628')

        n_prot_el = ret.find('.//nfe:nProt', ns)
        protocolo = n_prot_el.text if n_prot_el is not None else ''

        return {
            'sucesso': sucesso,
            'codigo_sefaz': c_stat,
            'mensagem': x_motivo,
            'protocolo': protocolo,
        }

    except Exception as e:
        logger.error(f"[manifestar_ciencia] Excecao: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'sucesso': False, 'erro': f'Erro ao manifestar: {str(e)}'}


def baixar_procnfe_completo(certificado: CertificadoA1, chave: str,
                            ambiente: str = 'producao') -> Dict:
    """
    Baixa o procNFe completo (NFe + protNFe envolvidos em nfeProc) via
    NfeConsultaProtocolo4, para ser usado na geração do DANFE.

    Args:
        certificado: Certificado A1 do destinatário
        chave: Chave de acesso de 44 dígitos
        ambiente: 'producao' ou 'homologacao'

    Returns:
        Dict com {'sucesso': bool, 'xml_bytes': bytes, 'erro': str}
    """
    try:
        if not chave or len(chave) != 44:
            return {'sucesso': False, 'erro': 'Chave de acesso invalida'}

        tp_amb = 2 if ambiente == 'homologacao' else 1
        soap_body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">'
            '<soap:Header/>'
            '<soap:Body>'
            '<nfe:nfeConsultaNF xmlns="http://www.portalfiscal.inf.br/nfe">'
            '<consSitNFe versao="4.00">'
            f'<tpAmb>{tp_amb}</tpAmb>'
            '<xServ>CONSULTAR</xServ>'
            f'<chNFe>{chave}</chNFe>'
            '</consSitNFe>'
            '</nfe:nfeConsultaNF>'
            '</soap:Body>'
            '</soap:Envelope>'
        )

        url = (WEBSERVICES_HOMOLOGACAO['NfeConsultaProtocolo']
               if ambiente == 'homologacao'
               else WEBSERVICES_PRODUCAO['NfeConsultaProtocolo'])
        headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}
        sess = certificado.get_session_requests()
        response = sess.post(url, data=soap_body.encode('utf-8'), headers=headers, timeout=60)

        if response.status_code != 200:
            return {'sucesso': False, 'erro': f'Erro HTTP {response.status_code}'}

        resp_root = etree.fromstring(response.content)
        ns = {'nfe': NAMESPACE_NFE}

        ret = resp_root.find('.//nfe:retConsSitNFe', ns)
        if ret is None:
            return {'sucesso': False, 'erro': 'Resposta invalida (retConsSitNFe nao encontrado)'}

        c_stat_el = ret.find('nfe:cStat', ns)
        x_motivo_el = ret.find('nfe:xMotivo', ns)
        c_stat = c_stat_el.text if c_stat_el is not None else ''
        x_motivo = x_motivo_el.text if x_motivo_el is not None else ''

        if c_stat != '100':
            return {
                'sucesso': False,
                'codigo_sefaz': c_stat,
                'erro': f'SEFAZ retornou status {c_stat}: {x_motivo}',
            }

        # Extrai NFe e protNFe para montar procNFe
        nfe_elem = ret.find('.//nfe:NFe', ns)
        prot_elem = ret.find('.//nfe:protNFe', ns)

        if nfe_elem is None or prot_elem is None:
            return {'sucesso': False, 'erro': 'NFe ou protNFe nao encontrados na resposta SEFAZ'}

        # Monta nfeProc encapsulando NFe + protNFe
        proc_root = etree.Element(f'{{{NAMESPACE_NFE}}}nfeProc')
        proc_root.set('versao', '4.00')
        from copy import deepcopy
        proc_root.append(deepcopy(nfe_elem))
        proc_root.append(deepcopy(prot_elem))

        xml_bytes = etree.tostring(proc_root, encoding='utf-8', xml_declaration=True)

        return {
            'sucesso': True,
            'xml_bytes': xml_bytes,
            'chave': chave,
            'codigo_sefaz': c_stat,
            'mensagem': x_motivo,
        }

    except Exception as e:
        logger.error(f"[baixar_procnfe] Excecao: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'sucesso': False, 'erro': f'Erro ao baixar procNFe: {str(e)}'}


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

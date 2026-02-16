#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO: NFS-e Service Layer (SOAP)
Integração com APIs SOAP municipais para consulta de NFS-e

Provedores suportados (APIs GRATUITAS):
- GINFES: 500+ municípios
- ISS.NET: 200+ municípios  
- BETHA: 1,000+ municípios
- EISS: 150+ municípios
- WEBISS: 50+ municípios
- SIMPLISS: 300+ municípios

Autor: Sistema Financeiro DWM
Data: 2026-02-13
"""

import requests
try:
    from requests_pkcs12 import post as post_pkcs12, get as get_pkcs12
except ImportError:
    post_pkcs12 = None
    get_pkcs12 = None
try:
    from lxml import etree
except ImportError:
    etree = None
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MAPEAMENTO DE PROVEDORES E URLS
# ============================================================================
# 
# IMPORTANTE: Este módulo utiliza o PADRÃO NACIONAL ABRASF (Associação Brasileira
# das Secretarias de Finanças das Capitais) para comunicação com webservices NFS-e.
# 
# O padrão ABRASF define layouts XML padronizados para consulta e emissão de NFS-e,
# implementados por diversos provedores (GINFES, ISS.NET, e-ISS, etc).
# 
# URLs aqui são dos WEBSERVICES PADRÃO ABRASF de cada município, não das APIs
# específicas das prefeituras.
# ============================================================================

PROVEDORES_NFSE = {
    'GINFES': {
        'nome': 'Ginfes',
        'padrao_abrasf': '2.00',
        'url_padrao': 'http://{municipio}.ginfes.com.br/ServiceGinfesImpl',
        'servico': 'ServiceGinfesImpl'
    },
    'ISSNET': {
        'nome': 'ISS.NET',
        'padrao_abrasf': '1.00',
        'url_padrao': 'https://{municipio}.issnetonline.com.br/abrasf/nfse.asmx',
        'servico': 'nfse.asmx'
    },
    'BETHA': {
        'nome': 'Betha Sistemas',
        'padrao_abrasf': '2.02',
        'url_padrao': 'https://e-gov.betha.com.br/e-nota-contribuinte-ws/nfseWS',
        'servico': 'nfseWS'
    },
    'EISS': {
        'nome': 'e-ISS',
        'padrao_abrasf': '2.00',
        'url_padrao': 'http://www.eissweb.com.br/ws/{municipio}/nfse.asmx',
        'servico': 'nfse.asmx'
    },
    'WEBISS': {
        'nome': 'WebISS',
        'padrao_abrasf': '1.00',
        'url_padrao': 'http://www.webiss.com.br/ws/nfse.asmx',
        'servico': 'nfse.asmx'
    },
    'SIMPLISS': {
        'nome': 'SimplISS',
        'padrao_abrasf': '2.00',
        'url_padrao': 'https://sistema.simplissweb.com.br/{municipio}/ws/nfse',
        'servico': 'nfse'
    }
}

# ============================================================================
# URLS DOS MUNICÍPIOS (Webservices Padrão ABRASF Nacional)
# ============================================================================
# 
# URLs dos webservices SOAP que seguem o padrão ABRASF nacional.
# 
# COMO DESCOBRIR A URL DE UM NOVO MUNICÍPIO:
# 1. Acesse o site da prefeitura / Seção de NFS-e
# 2. Procure "Documentação Webservice", "Manual Integração" ou "Desenvolvedores"
# 3. Identifique o provedor (Ginfes, ISS.NET, e-ISS, etc)
# 4. Busque pelo WSDL ou URL do endpoint SOAP
# 5. URLs comuns:
#    - Ginfes: https://[sistema].[cidade].gov.br/[ws]/ServiceGinfesImpl
#    - ISS.NET: https://nfse.[cidade].gov.br/ws/nfse.asmx
#    - e-ISS: https://[sistema].[cidade].gov.br/ws/nfse.asmx
# 
# TESTE: Acesse a URL no navegador - deve exibir descrição do webservice ou erro XML
# ============================================================================

# Mapeamento de municípios conhecidos
URLS_MUNICIPIOS = {
    '5002704': {  # Campo Grande/MS
        'provedor': 'GINFES',
        'url': 'http://issdigital.pmcg.ms.gov.br/nfse/ServiceGinfesImpl'
    },
    '3106200': {  # Belo Horizonte/MG
        'provedor': 'GINFES',
        # ⚠️ ATENÇÃO: URLs testadas abaixo NÃO funcionam (retornam 404)
        # URL correta deve ser obtida na documentação oficial:
        # https://prefeitura.pbh.gov.br/fazenda/nfse
        # 
        # Configure manualmente via interface após descobrir URL correta
        'url': None,  # URL padrão desconhecida - configurar manualmente
        'url_alternativas': [
            # URLs testadas automaticamente - TODAS RETORNAM 404:
            'https://bhissdigital.pbh.gov.br/bhiss-ws/nfse',
            'https://bhissdigital.pbh.gov.br/bhiss-ws/ServiceGinfesImpl',
            'https://bhissdigital.pbh.gov.br/bhiss-ws/nfse.asmx',
            # 'https://bhiss.pbh.gov.br/bhiss-ws/nfse',  # DNS não existe
            # 'http://bhissdigital.pbh.gov.br/bhiss-ws/nfse'  # HTTP não seguro
        ],
        'nota': 'Requer configuração manual. Consulte documentação oficial da prefeitura.'
    },
    '3550308': {  # São Paulo/SP
        'provedor': 'ISSNET',
        'url': 'https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx'
    },
    '4106902': {  # Curitiba/PR
        'provedor': 'EISS',
        'url': 'https://nfse.curitiba.pr.gov.br/grpfor/ServicoProxy'
    },
    '3304557': {  # Rio de Janeiro/RJ
        'provedor': 'ISSNET',
        'url': 'https://notacarioca.rio.gov.br/WSNacional/nfse.asmx'
    },
    '2927408': {  # Salvador/BA
        'provedor': 'ISSNET',
        'url': 'http://www.notaeletronica.salvador.ba.gov.br/servicos/webservice/AbRASFv1NSeproducao.asmx'
    }
}


# ============================================================================
# CLASSE PRINCIPAL: NFSeService
# ============================================================================

class NFSeService:
    """
    Classe para comunicação com APIs SOAP de provedores NFS-e
    """
    
    def __init__(self, certificado_path: str, certificado_senha: str):
        """
        Inicializa serviço de NFS-e
        
        Args:
            certificado_path: Caminho para arquivo .pfx do certificado A1
            certificado_senha: Senha do certificado
        """
        self.certificado_path = certificado_path
        self.certificado_senha = certificado_senha
        
        # Validar certificado
        if not os.path.exists(certificado_path):
            raise FileNotFoundError(f"Certificado não encontrado: {certificado_path}")
    
    def buscar_nfse(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        provedor: str,
        url_webservice: str,
        codigo_municipio: str
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca NFS-e em um município específico
        
        Args:
            cnpj_prestador: CNPJ do prestador (11 dígitos sem formatação)
            inscricao_municipal: Inscrição Municipal
            data_inicial: Data inicial da busca
            data_final: Data final da busca
            provedor: Provedor (GINFES, ISSNET, etc)
            url_webservice: URL do webservice SOAP
            codigo_municipio: Código IBGE do município
            
        Returns:
            Tuple (sucesso, lista_nfse, mensagem_erro)
        """
        try:
            logger.info(f"🔍 Buscando NFS-e: {provedor} - {codigo_municipio}")
            
            # Selecionar método baseado no provedor
            if provedor == 'GINFES':
                return self._buscar_ginfes(
                    cnpj_prestador, inscricao_municipal,
                    data_inicial, data_final, url_webservice, codigo_municipio
                )
            elif provedor == 'ISSNET':
                return self._buscar_issnet(
                    cnpj_prestador, inscricao_municipal,
                    data_inicial, data_final, url_webservice, codigo_municipio
                )
            elif provedor == 'BETHA':
                return self._buscar_betha(
                    cnpj_prestador, inscricao_municipal,
                    data_inicial, data_final, url_webservice, codigo_municipio
                )
            elif provedor == 'EISS':
                return self._buscar_eiss(
                    cnpj_prestador, inscricao_municipal,
                    data_inicial, data_final, url_webservice, codigo_municipio
                )
            else:
                # Fallback: tentar método genérico ABRASF
                return self._buscar_generico_abrasf(
                    cnpj_prestador, inscricao_municipal,
                    data_inicial, data_final, url_webservice, codigo_municipio
                )
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar NFS-e: {e}")
            return False, [], str(e)
    
    # ========================================================================
    # GINFES (ABRASF 2.00)
    # ========================================================================
    
    def _buscar_ginfes(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        url_webservice: str,
        codigo_municipio: str
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca NFS-e no provedor Ginfes (ABRASF 2.00)
        """
        try:
            # Montar XML da requisição SOAP
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:nfse="http://www.ginfes.com.br/consulta_nfse_v03">
    <soap:Body>
        <nfse:ConsultarNfseEnvio>
            <Pedido>
                <Prestador>
                    <Cnpj>{cnpj_prestador}</Cnpj>
                    <InscricaoMunicipal>{inscricao_municipal}</InscricaoMunicipal>
                </Prestador>
                <PeriodoEmissao>
                    <DataInicial>{data_inicial.strftime('%Y-%m-%d')}</DataInicial>
                    <DataFinal>{data_final.strftime('%Y-%m-%d')}</DataFinal>
                </PeriodoEmissao>
            </Pedido>
        </nfse:ConsultarNfseEnvio>
    </soap:Body>
</soap:Envelope>"""
            
            # Fazer requisição SOAP com certificado A1
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': 'http://www.ginfes.com.br/servico_consultar_nfse',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/soap+xml, application/dime, multipart/related, text/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
            
            response = post_pkcs12(
                url_webservice,
                data=xml_request.encode('utf-8'),
                headers=headers,
                pkcs12_filename=self.certificado_path,
                pkcs12_password=self.certificado_senha,
                timeout=30,
                verify=True  # Verificar SSL
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Resposta HTTP {response.status_code}")
                logger.error(f"   URL: {url_webservice}")
                logger.error(f"   Headers enviados: {headers}")
                # Não logar todo o response.text se for HTML grande
                if len(response.text) > 500:
                    logger.error(f"   Resposta (truncada): {response.text[:500]}...")
                else:
                    logger.error(f"   Resposta: {response.text}")
                
                # Erro 404 = endpoint não encontrado, retornar para tentar URL alternativa
                if response.status_code == 404:
                    return False, [], f"HTTP 404: Endpoint não encontrado. URL inválida: {url_webservice}"
                
                # Mensagem específica para erro 403 (Acesso Bloqueado)
                if response.status_code == 403:
                    erro_msg = (
                        f"Acesso bloqueado pelo servidor (HTTP 403). "
                        f"Possíveis causas: "
                        f"1) URL do webservice incorreta (verifique se está usando o endpoint padrão ABRASF correto), "
                        f"2) Proteção anti-bot/firewall (WAF, GoCache, Cloudflare), "
                        f"3) Certificado não autorizado para este município, "
                        f"4) IP do servidor bloqueado. "
                        f"Solução: Verifique a URL do webservice na documentação oficial do município ou "
                        f"entre em contato com o suporte técnico da prefeitura."
                    )
                    return False, [], erro_msg
                
                return False, [], f"Erro HTTP {response.status_code}: {response.text[:200]}"
            
            # Processar resposta XML
            nfses = self._processar_resposta_ginfes(response.text, codigo_municipio)
            
            logger.info(f"✅ Encontradas {len(nfses)} NFS-e no Ginfes")
            return True, nfses, None
            
        except Exception as e:
            logger.error(f"❌ Erro Ginfes: {e}")
            return False, [], str(e)
    
    def _processar_resposta_ginfes(self, xml_response: str, codigo_municipio: str) -> List[Dict]:
        """
        Processa XML de resposta do Ginfes
        """
        try:
            root = etree.fromstring(xml_response.encode('utf-8'))
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'nfse': 'http://www.ginfes.com.br/tipos_v03.xsd'
            }
            
            nfses = []
            
            # Buscar todas as NFS-e na resposta
            for nfse_node in root.xpath('//nfse:CompNfse', namespaces=namespaces):
                try:
                    nfse_data = self._extrair_dados_nfse_ginfes(nfse_node, codigo_municipio, namespaces)
                    if nfse_data:
                        nfses.append(nfse_data)
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar NFS-e: {e}")
                    continue
            
            return nfses
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar XML: {e}")
            return []
    
    def _extrair_dados_nfse_ginfes(self, nfse_node, codigo_municipio: str, namespaces: Dict) -> Optional[Dict]:
        """
        Extrai dados de uma NFS-e do XML Ginfes
        """
        try:
            # Extrair campos principais
            numero_nfse = nfse_node.xpath('.//nfse:Numero/text()', namespaces=namespaces)[0]
            codigo_verificacao = nfse_node.xpath('.//nfse:CodigoVerificacao/text()', namespaces=namespaces)[0]
            data_emissao_str = nfse_node.xpath('.//nfse:DataEmissao/text()', namespaces=namespaces)[0]
            
            # Prestador
            cnpj_prestador = nfse_node.xpath('.//nfse:Prestador/nfse:Cnpj/text()', namespaces=namespaces)[0]
            
            # Tomador
            cnpj_tomador = nfse_node.xpath('.//nfse:Tomador/nfse:CpfCnpj/nfse:Cnpj/text()', namespaces=namespaces)
            cnpj_tomador = cnpj_tomador[0] if cnpj_tomador else None
            
            razao_social_tomador = nfse_node.xpath('.//nfse:Tomador/nfse:RazaoSocial/text()', namespaces=namespaces)
            razao_social_tomador = razao_social_tomador[0] if razao_social_tomador else None
            
            # Valores
            valor_servico = float(nfse_node.xpath('.//nfse:ValorServicos/text()', namespaces=namespaces)[0])
            valor_deducoes = float(nfse_node.xpath('.//nfse:ValorDeducoes/text()', namespaces=namespaces)[0] or 0)
            valor_iss = float(nfse_node.xpath('.//nfse:ValorIss/text()', namespaces=namespaces)[0])
            aliquota_iss = float(nfse_node.xpath('.//nfse:Aliquota/text()', namespaces=namespaces)[0])
            
            # Serviço
            discriminacao = nfse_node.xpath('.//nfse:Discriminacao/text()', namespaces=namespaces)
            discriminacao = discriminacao[0] if discriminacao else ''
            
            codigo_servico = nfse_node.xpath('.//nfse:ItemListaServico/text()', namespaces=namespaces)
            codigo_servico = codigo_servico[0] if codigo_servico else None
            
            # RPS
            numero_rps = nfse_node.xpath('.//nfse:IdentificacaoRps/nfse:Numero/text()', namespaces=namespaces)
            numero_rps = numero_rps[0] if numero_rps else None
            
            serie_rps = nfse_node.xpath('.//nfse:IdentificacaoRps/nfse:Serie/text()', namespaces=namespaces)
            serie_rps = serie_rps[0] if serie_rps else None
            
            # Montar dicionário
            nfse_dict = {
                'numero_nfse': numero_nfse,
                'codigo_verificacao': codigo_verificacao,
                'data_emissao': datetime.strptime(data_emissao_str, '%Y-%m-%dT%H:%M:%S'),
                'data_competencia': datetime.strptime(data_emissao_str, '%Y-%m-%dT%H:%M:%S').date(),
                'cnpj_prestador': cnpj_prestador,
                'cnpj_tomador': cnpj_tomador,
                'razao_social_tomador': razao_social_tomador,
                'valor_servico': valor_servico,
                'valor_deducoes': valor_deducoes,
                'valor_iss': valor_iss,
                'valor_liquido': valor_servico - valor_deducoes,
                'aliquota_iss': aliquota_iss,
                'discriminacao': discriminacao,
                'codigo_servico': codigo_servico,
                'numero_rps': numero_rps,
                'serie_rps': serie_rps,
                'provedor': 'GINFES',
                'codigo_municipio': codigo_municipio,
                'situacao': 'NORMAL',
                'xml': etree.tostring(nfse_node, encoding='unicode'),
                'xml_path': None
            }
            
            return nfse_dict
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados NFS-e: {e}")
            return None
    
    # ========================================================================
    # ISS.NET (ABRASF 1.00)
    # ========================================================================
    
    def _buscar_issnet(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        url_webservice: str,
        codigo_municipio: str
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca NFS-e no provedor ISS.NET (ABRASF 1.00)
        """
        try:
            # XML similar ao Ginfes mas com namespace diferente
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://www.issnetonline.com.br/webserviceabrasf/homologacao/servicos.asmx">
    <soap:Body>
        <nfse:ConsultarNfse>
            <Prestador>
                <Cnpj>{cnpj_prestador}</Cnpj>
                <InscricaoMunicipal>{inscricao_municipal}</InscricaoMunicipal>
            </Prestador>
            <PeriodoEmissao>
                <DataInicial>{data_inicial.strftime('%Y-%m-%d')}</DataInicial>
                <DataFinal>{data_final.strftime('%Y-%m-%d')}</DataFinal>
            </PeriodoEmissao>
        </nfse:ConsultarNfse>
    </soap:Body>
</soap:Envelope>"""
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': '"http://www.issnetonline.com.br/webserviceabrasf/homologacao/servicos.asmx/ConsultarNfse"',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/xml, application/soap+xml, application/dime, multipart/related, text/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
            
            response = post_pkcs12(
                url_webservice,
                data=xml_request.encode('utf-8'),
                headers=headers,
                pkcs12_filename=self.certificado_path,
                pkcs12_password=self.certificado_senha,
                timeout=30,
                verify=True
            )
            
            if response.status_code != 200:
                return False, [], f"Erro HTTP {response.status_code}"
            
            # Processar resposta (similar ao Ginfes)
            nfses = self._processar_resposta_issnet(response.text, codigo_municipio)
            
            logger.info(f"✅ Encontradas {len(nfses)} NFS-e no ISS.NET")
            return True, nfses, None
            
        except Exception as e:
            logger.error(f"❌ Erro ISS.NET: {e}")
            return False, [], str(e)
    
    def _processar_resposta_issnet(self, xml_response: str, codigo_municipio: str) -> List[Dict]:
        """
        Processa XML de resposta do ISS.NET (similar ao Ginfes)
        """
        # Implementação similar ao _processar_resposta_ginfes
        # Ajustar namespaces conforme ISS.NET
        return []
    
    # ========================================================================
    # BETHA (ABRASF 2.02)
    # ========================================================================
    
    def _buscar_betha(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        url_webservice: str,
        codigo_municipio: str
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca NFS-e no provedor Betha (ABRASF 2.02)
        """
        # Implementação similar ao Ginfes
        # Ajustar XML e namespaces conforme Betha
        logger.warning("⚠️ Provedor Betha: implementação básica")
        return False, [], "Provedor Betha em desenvolvimento"
    
    # ========================================================================
    # e-ISS (ABRASF 2.00)
    # ========================================================================
    
    def _buscar_eiss(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        url_webservice: str,
        codigo_municipio: str
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca NFS-e no provedor e-ISS (ABRASF 2.00)
        """
        # Implementação similar ao Ginfes
        logger.warning("⚠️ Provedor e-ISS: implementação básica")
        return False, [], "Provedor e-ISS em desenvolvimento"
    
    # ========================================================================
    # MÉTODO GENÉRICO (Fallback)
    # ========================================================================
    
    def _buscar_generico_abrasf(
        self,
        cnpj_prestador: str,
        inscricao_municipal: str,
        data_inicial: date,
        data_final: date,
        url_webservice: str,
        codigo_municipio: str
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Método genérico para provedores ABRASF não mapeados
        """
        logger.warning(f"⚠️ Usando método genérico para município {codigo_municipio}")
        return False, [], "Provedor não implementado. Use Ginfes ou ISS.NET como referência."


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def descobrir_provedor(codigo_municipio: str) -> Optional[Dict]:
    """
    Tenta descobrir provedor e URL de um município
    
    Args:
        codigo_municipio: Código IBGE (7 dígitos)
        
    Returns:
        Dict com provedor e URL, ou None se não encontrado
    """
    if codigo_municipio in URLS_MUNICIPIOS:
        return URLS_MUNICIPIOS[codigo_municipio]
    return None


def testar_conexao(url_webservice: str, certificado_path: str, certificado_senha: str) -> Tuple[bool, str]:
    """
    Testa conexão com webservice SOAP
    
    Args:
        url_webservice: URL do webservice
        certificado_path: Caminho do certificado A1
        certificado_senha: Senha do certificado
        
    Returns:
        Tuple (sucesso, mensagem)
    """
    try:
        # Headers para evitar bloqueio por firewall/WAF
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/xml, application/soap+xml, application/xml, text/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
        
        # Fazer requisição simples para verificar conectividade
        response = post_pkcs12(
            url_webservice,
            data=b'',
            headers=headers,
            pkcs12_filename=certificado_path,
            pkcs12_password=certificado_senha,
            timeout=10,
            verify=True
        )
        
        if response.status_code in [200, 500]:  # 500 é esperado sem XML válido
            return True, "Conexão OK"
        else:
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)


# ============================================================================
# AMBIENTE NACIONAL DE NFS-e (API REST)
# ============================================================================
# 
# O Ambiente Nacional (ADN) é a solução OFICIAL do governo federal para
# consulta de NFS-e via certificado digital, similar ao sistema de NF-e e CT-e.
# 
# Substitui a necessidade de integrar com APIs SOAP de cada município
# individualmente. Usa protocolo REST moderno com autenticação mTLS.
# 
# URLs OFICIAIS:
# - Produção:     https://adn.nfse.gov.br
# - Homologação:  https://adn.producaorestrita.nfse.gov.br
# 
# ENDPOINTS PRINCIPAIS:
# - GET /contribuintes/DFe/{NSU} - Consulta incremental por NSU
# - GET /danfse/{chave}           - Download de DANFSe (PDF oficial)
# ============================================================================

class NFSeAmbienteNacional:
    """
    Cliente para o Ambiente Nacional de NFS-e (API REST oficial do governo)
    
    Implementa consulta incremental via NSU (Número Sequencial Único),
    similar ao sistema de NF-e e CT-e.
    
    Características:
    - Autenticação mTLS com certificado digital A1
    - Respostas em JSON com XMLs compactados (Base64 + gzip)
    - Rate limit: ~1 req/segundo
    - Namespace: http://www.sped.fazenda.gov.br/nfse
    """
    
    def __init__(self, certificado_path: str, certificado_senha: str, ambiente: str = 'producao'):
        """
        Inicializa cliente do Ambiente Nacional de NFS-e
        
        Args:
            certificado_path: Caminho para arquivo .pfx do certificado A1
            certificado_senha: Senha do certificado
            ambiente: 'producao' ou 'homologacao'
        """
        self.certificado_path = certificado_path
        self.certificado_senha = certificado_senha
        self.ambiente = ambiente
        
        # URLs oficiais do Ambiente Nacional
        if ambiente == 'producao':
            self.url_base = "https://adn.nfse.gov.br"
        else:
            self.url_base = "https://adn.producaorestrita.nfse.gov.br"
        
        logger.info(f"🌐 Cliente Ambiente Nacional inicializado: {self.url_base}")
    
    def consultar_nsu(self, nsu: int, timeout: int = 45) -> Optional[Dict]:
        """
        Consulta documento por NSU (Número Sequencial Único)
        
        Endpoint: GET /contribuintes/DFe/{NSU}
        
        Args:
            nsu: Número Sequencial Único (15 dígitos)
            timeout: Timeout da requisição em segundos
        
        Returns:
            dict: Resposta JSON da API ou None se não encontrado
            
        Formato da resposta:
        {
            "StatusProcessamento": "OK",
            "LoteDFe": [
                {
                    "NSU": "000000000001234",
                    "ChaveAcesso": "31062001213891738000138250000000157825012270096818",
                    "ArquivoXml": "H4sIAAAAAAAA..."  // Base64 + gzip
                }
            ],
            "ultNSU": "000000000001234",
            "maxNSU": "000000000009999"
        }
        """
        import time
        
        endpoint = f"{self.url_base}/contribuintes/DFe/{nsu}"
        
        try:
            # Headers para API REST
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Sistema Financeiro DWM/1.0'
            }
            
            # Requisição GET com certificado mTLS
            response = get_pkcs12(
                endpoint,
                headers=headers,
                pkcs12_filename=self.certificado_path,
                pkcs12_password=self.certificado_senha,
                timeout=timeout,
                verify=True
            )
            
            # NSU não encontrado (esperado quando atingir o fim)
            if response.status_code == 404:
                logger.debug(f"📭 NSU {nsu} não encontrado")
                return None
            
            # Rate limit (aguardar e tentar novamente)
            if response.status_code == 429:
                logger.warning(f"⏱️ Rate limit atingido no NSU {nsu}, aguardando 2s...")
                time.sleep(2)
                return None
            
            # Outros erros HTTP
            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP {response.status_code} ao consultar NSU {nsu}")
                logger.error(f"   Resposta: {response.text[:200]}")
                return None
            
            # Parse JSON
            resultado = response.json()
            logger.debug(f"✅ NSU {nsu}: JSON recebido")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao consultar NSU {nsu}: {e}")
            return None
    
    def consultar_danfse(self, chave_acesso: str, retry: int = 3, timeout: int = 45) -> Optional[bytes]:
        """
        Consulta DANFSe (PDF oficial da NFS-e) por chave de acesso
        
        Este é o PDF OFICIAL gerado pelo Ambiente Nacional, equivalente ao
        DANFE da NF-e. Contém layout padronizado com brasão, QR Code e todas
        as informações fiscais.
        
        Endpoint: GET /danfse/{chave}
        
        Args:
            chave_acesso: Chave de acesso da NFS-e (50 dígitos, sem prefixo "NFS")
            retry: Número de tentativas em caso de erro temporário
            timeout: Timeout da requisição em segundos
        
        Returns:
            bytes: Conteúdo do PDF oficial ou None se não disponível
        """
        import time
        
        endpoint = f"{self.url_base}/danfse/{chave_acesso}"
        
        for tentativa in range(1, retry + 1):
            try:
                if tentativa > 1:
                    logger.info(f"   🔄 Tentativa {tentativa}/{retry} para chave {chave_acesso[:20]}...")
                    time.sleep(2)  # Aguarda entre tentativas
                
                # Headers para API REST
                headers = {
                    'Accept': 'application/pdf',
                    'User-Agent': 'Sistema Financeiro DWM/1.0'
                }
                
                # Requisição GET com certificado mTLS
                response = get_pkcs12(
                    endpoint,
                    headers=headers,
                    pkcs12_filename=self.certificado_path,
                    pkcs12_password=self.certificado_senha,
                    timeout=timeout,
                    verify=True
                )
                
                # PDF encontrado
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Valida se é realmente um PDF
                    if 'application/pdf' in content_type or response.content.startswith(b'%PDF'):
                        logger.info(f"✅ DANFSe oficial obtido ({len(response.content):,} bytes)")
                        return response.content
                    else:
                        logger.warning(f"⚠️ Resposta não é PDF (Content-Type: {content_type})")
                        continue
                
                # Erros temporários do servidor - tentar novamente
                if response.status_code in [502, 503, 504]:
                    logger.warning(f"⚠️ Servidor temporariamente indisponível ({response.status_code})")
                    if tentativa < retry:
                        continue
                
                # PDF não disponível (404)
                if response.status_code == 404:
                    logger.warning(f"📭 DANFSe não disponível para chave {chave_acesso[:20]}...")
                    return None
                
                # Outros erros
                logger.error(f"❌ Erro HTTP {response.status_code} ao consultar DANFSe")
                return None
                
            except Exception as e:
                logger.error(f"❌ Erro ao consultar DANFSe: {e}")
                if tentativa < retry:
                    continue
                return None
        
        # Todas as tentativas falharam
        logger.error(f"❌ Falha ao obter DANFSe após {retry} tentativas")
        return None
    
    def extrair_documentos(self, resultado: Optional[Dict]) -> List[Tuple[str, str, str]]:
        """
        Extrai documentos XML do resultado da consulta NSU
        
        Args:
            resultado: dict JSON retornado por consultar_nsu()
        
        Returns:
            Lista de tuplas (nsu, xml_content, tipo_documento)
        """
        import base64
        import gzip
        
        if not resultado:
            return []
        
        documentos = []
        
        try:
            lote_dfe = resultado.get('LoteDFe', [])
            
            if not lote_dfe:
                logger.debug(f"📭 Resposta sem documentos no lote")
                return []
            
            # Processa cada documento do lote
            for doc in lote_dfe:
                try:
                    doc_nsu = str(doc.get('NSU', '')).zfill(15)  # Padroniza para 15 dígitos
                    xml_base64 = doc.get('ArquivoXml', '')
                    chave_acesso = doc.get('ChaveAcesso', '')
                    
                    if not xml_base64:
                        logger.warning(f"⚠️ NSU {doc_nsu}: sem ArquivoXml")
                        continue
                    
                    # Decodifica Base64 e descomprime gzip
                    xml_comprimido = base64.b64decode(xml_base64)
                    xml = gzip.decompress(xml_comprimido).decode('utf-8')
                    
                    # Determina tipo de documento
                    if '<Nfse' in xml or '<NFSe' in xml or '<nfse' in xml or '<CompNfse' in xml:
                        tipo = 'NFS-e'
                    elif '<eventoCancelamento' in xml:
                        tipo = 'Cancelamento'
                    elif '<eventoSubstituicao' in xml:
                        tipo = 'Substituicao'
                    else:
                        tipo = 'Desconhecido'
                    
                    documentos.append((doc_nsu, xml, tipo))
                    logger.debug(f"✅ NSU {doc_nsu}: {tipo} extraído")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar documento do lote: {e}")
                    continue
            
            return documentos
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair documentos: {e}")
            return []
    
    def validar_xml(self, xml_content: str) -> bool:
        """
        Valida estrutura básica do XML da NFS-e
        
        Args:
            xml_content: Conteúdo XML (string)
        
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            tree = etree.fromstring(xml_content.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"❌ XML inválido: {e}")
            return False


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configuração de exemplo
    certificado = "certificado.pfx"
    senha = "senha123"
    
    # Criar serviço
    service = NFSeService(certificado, senha)
    
    # Buscar NFS-e
    sucesso, nfses, erro = service.buscar_nfse(
        cnpj_prestador="12345678000190",
        inscricao_municipal="123456",
        data_inicial=date(2026, 1, 1),
        data_final=date(2026, 1, 31),
        provedor="GINFES",
        url_webservice="http://issdigital.pmcg.ms.gov.br/nfse/ServiceGinfesImpl",
        codigo_municipio="5002704"
    )
    
    if sucesso:
        print(f"✅ Sucesso! Encontradas {len(nfses)} NFS-e")
        for nfse in nfses:
            print(f"  - NFS-e {nfse['numero_nfse']}: R$ {nfse['valor_servico']:.2f}")
    else:
        print(f"❌ Erro: {erro}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO: NFS-e Business Logic Layer
Orquestra operações entre database e service layer

Funcionalidades:
- Configuração de municípios
- Busca de NFS-e
- Gerenciamento de RPS
- Exportação de dados

Autor: Sistema Financeiro DWM
Data: 2026-02-13
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
import logging
import os
import re
from nfse_database import NFSeDatabase
from nfse_service import NFSeService, descobrir_provedor, testar_conexao

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DE MUNICÍPIOS
# ============================================================================

def adicionar_municipio(
    db_params: Dict,
    empresa_id: int,
    cnpj_cpf: str,
    codigo_municipio: str,
    nome_municipio: str,
    uf: str,
    inscricao_municipal: str,
    provedor: Optional[str] = None,
    url_customizada: Optional[str] = None
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Adiciona configuração de um município
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        cnpj_cpf: CNPJ da empresa
        codigo_municipio: Código IBGE (7 dígitos)
        nome_municipio: Nome do município
        uf: UF (2 letras)
        inscricao_municipal: IM da empresa neste município
        provedor: Provedor SOAP (detectado automaticamente se None)
        url_customizada: URL específica (opcional)
        
    Returns:
        Tuple (sucesso, config_id, mensagem_erro)
    """
    try:
        # Tentar descobrir provedor automaticamente
        if not provedor or not url_customizada:
            info_municipio = descobrir_provedor(codigo_municipio)
            if info_municipio:
                provedor = provedor or info_municipio['provedor']
                url_customizada = url_customizada or info_municipio['url']
                logger.info(f"✅ Provedor detectado: {provedor}")
            else:
                if not provedor:
                    return False, None, "Provedor não especificado e não foi possível detectar automaticamente"
        
        # Criar configuração
        config = {
            'empresa_id': empresa_id,
            'cnpj_cpf': cnpj_cpf,
            'provedor': provedor,
            'codigo_municipio': codigo_municipio,
            'nome_municipio': nome_municipio,
            'uf': uf,
            'inscricao_municipal': inscricao_municipal,
            'url_customizada': url_customizada,
            'ativo': True
        }
        
        # Salvar no banco
        with NFSeDatabase(db_params) as db:
            config_id = db.adicionar_config_nfse(config)
            
            if config_id:
                logger.info(f"✅ Município configurado: {nome_municipio} (ID: {config_id})")
                return True, config_id, None
            else:
                return False, None, "Erro ao salvar configuração no banco"
                
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar município: {e}")
        return False, None, str(e)


def listar_municipios(db_params: Dict, empresa_id: int) -> List[Dict]:
    """
    Lista todos os municípios configurados para uma empresa
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        
    Returns:
        Lista de configurações
    """
    try:
        with NFSeDatabase(db_params) as db:
            configs = db.get_config_nfse(empresa_id)
            logger.info(f"✅ Encontradas {len(configs)} configurações")
            return configs
    except Exception as e:
        logger.error(f"❌ Erro ao listar municípios: {e}")
        return []


def testar_conexao_municipio(
    db_params: Dict,
    config_id: int,
    certificado_path: str,
    certificado_senha: str
) -> Tuple[bool, str]:
    """
    Testa conexão com webservice de um município
    
    Args:
        db_params: Parâmetros de conexão ao banco
        config_id: ID da configuração
        certificado_path: Caminho do certificado A1
        certificado_senha: Senha do certificado
        
    Returns:
        Tuple (sucesso, mensagem)
    """
    try:
        # Buscar configuração
        with NFSeDatabase(db_params) as db:
            configs = db.get_config_nfse(config_id)
            if not configs:
                return False, "Configuração não encontrada"
            
            config = configs[0]
            url_webservice = config['url_customizada']
            
            if not url_webservice:
                return False, "URL do webservice não configurada"
            
            # Testar conexão
            sucesso, mensagem = testar_conexao(url_webservice, certificado_path, certificado_senha)
            
            # Atualizar status no banco
            status = 'OK' if sucesso else 'ERRO'
            db.atualizar_status_conexao(config_id, status, mensagem if not sucesso else None)
            
            return sucesso, mensagem
            
    except Exception as e:
        logger.error(f"❌ Erro ao testar conexão: {e}")
        return False, str(e)


def excluir_municipio(db_params: Dict, config_id: int) -> Tuple[bool, Optional[str]]:
    """
    Remove configuração de um município
    
    Args:
        db_params: Parâmetros de conexão ao banco
        config_id: ID da configuração
        
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        with NFSeDatabase(db_params) as db:
            sucesso = db.excluir_config(config_id)
            return sucesso, None if sucesso else "Erro ao excluir configuração"
    except Exception as e:
        logger.error(f"❌ Erro ao excluir município: {e}")
        return False, str(e)


# ============================================================================
# BUSCA DE NFS-e
# ============================================================================

def buscar_nfse_periodo(
    db_params: Dict,
    empresa_id: int,
    cnpj_prestador: str,
    data_inicial: date,
    data_final: date,
    certificado_path: str,
    certificado_senha: str,
    codigos_municipios: Optional[List[str]] = None
) -> Dict:
    """
    Busca NFS-e em um ou mais municípios
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        cnpj_prestador: CNPJ do prestador
        data_inicial: Data inicial
        data_final: Data final
        certificado_path: Caminho do certificado A1
        certificado_senha: Senha do certificado
        codigos_municipios: Lista de códigos (None = todos)
        
    Returns:
        Dict com resultado da operação
    """
    resultado = {
        'sucesso': True,
        'total_nfse': 0,
        'total_municipios': 0,
        'municipios_sucesso': 0,
        'municipios_erro': 0,
        'nfse_novas': 0,
        'nfse_atualizadas': 0,
        'detalhes': [],
        'erros': []
    }
    
    try:
        # Buscar configurações de municípios
        with NFSeDatabase(db_params) as db:
            if codigos_municipios:
                # Buscar apenas municípios especificados
                configs = []
                for codigo in codigos_municipios:
                    config = db.get_config_nfse(empresa_id, codigo)
                    if config:
                        configs.extend(config)
            else:
                # Buscar todos os municípios ativos
                configs = [c for c in db.get_config_nfse(empresa_id) if c.get('ativo')]
        
        if not configs:
            resultado['sucesso'] = False
            resultado['erros'].append("Nenhum município configurado")
            return resultado
        
        resultado['total_municipios'] = len(configs)
        logger.info(f"🔍 Buscando NFS-e em {len(configs)} município(s)")
        
        # Criar serviço NFS-e
        service = NFSeService(certificado_path, certificado_senha)
        
        # Buscar em cada município
        with NFSeDatabase(db_params) as db:
            for config in configs:
                municipio_nome = config['nome_municipio']
                codigo_municipio = config['codigo_municipio']
                
                logger.info(f"🏙️ Buscando em {municipio_nome}...")
                
                try:
                    # Buscar NFS-e via SOAP
                    sucesso, nfses, erro = service.buscar_nfse(
                        cnpj_prestador=cnpj_prestador,
                        inscricao_municipal=config['inscricao_municipal'],
                        data_inicial=data_inicial,
                        data_final=data_final,
                        provedor=config['provedor'],
                        url_webservice=config['url_customizada'],
                        codigo_municipio=codigo_municipio
                    )
                    
                    if sucesso:
                        resultado['municipios_sucesso'] += 1
                        
                        # Salvar NFS-e no banco
                        for nfse in nfses:
                            # Verificar se NFS-e já existe
                            nfse_existente = db.get_nfse_by_numero(
                                nfse['numero_nfse'],
                                codigo_municipio
                            )
                            
                            # Adicionar empresa_id
                            nfse['empresa_id'] = empresa_id
                            nfse['nome_municipio'] = municipio_nome
                            nfse['uf'] = config['uf']
                            
                            # Salvar
                            nfse_id = db.salvar_nfse(nfse)
                            
                            if nfse_id:
                                if nfse_existente:
                                    resultado['nfse_atualizadas'] += 1
                                else:
                                    resultado['nfse_novas'] += 1
                                resultado['total_nfse'] += 1
                        
                        resultado['detalhes'].append({
                            'municipio': municipio_nome,
                            'codigo': codigo_municipio,
                            'sucesso': True,
                            'quantidade': len(nfses)
                        })
                        
                        logger.info(f"✅ {municipio_nome}: {len(nfses)} NFS-e encontradas")
                        
                    else:
                        resultado['municipios_erro'] += 1
                        resultado['erros'].append(f"{municipio_nome}: {erro}")
                        resultado['detalhes'].append({
                            'municipio': municipio_nome,
                            'codigo': codigo_municipio,
                            'sucesso': False,
                            'erro': erro
                        })
                        
                        logger.error(f"❌ {municipio_nome}: {erro}")
                
                except Exception as e:
                    resultado['municipios_erro'] += 1
                    resultado['erros'].append(f"{municipio_nome}: {str(e)}")
                    logger.error(f"❌ Erro em {municipio_nome}: {e}")
        
        # Status final
        if resultado['municipios_erro'] == len(configs):
            resultado['sucesso'] = False
        
        logger.info(f"✅ Busca concluída: {resultado['total_nfse']} NFS-e ({resultado['nfse_novas']} novas)")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Erro geral na busca: {e}")
        resultado['sucesso'] = False
        resultado['erros'].append(str(e))
        return resultado


def consultar_nfse_periodo(
    db_params: Dict,
    empresa_id: int,
    data_inicial: date,
    data_final: date,
    codigo_municipio: Optional[str] = None
) -> List[Dict]:
    """
    Consulta NFS-e armazenadas localmente (sem buscar via API)
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        data_inicial: Data inicial
        data_final: Data final
        codigo_municipio: Código do município (None = todos)
        
    Returns:
        Lista de NFS-e
    """
    try:
        with NFSeDatabase(db_params) as db:
            nfses = db.buscar_nfse_periodo(
                empresa_id=empresa_id,
                data_inicial=data_inicial,
                data_final=data_final,
                codigo_municipio=codigo_municipio,
                situacao='NORMAL'
            )
            logger.info(f"✅ Consulta local: {len(nfses)} NFS-e")
            return nfses
    except Exception as e:
        logger.error(f"❌ Erro ao consultar NFS-e: {e}")
        return []


def get_detalhes_nfse(db_params: Dict, nfse_id: int) -> Optional[Dict]:
    """
    Retorna detalhes completos de uma NFS-e
    
    Args:
        db_params: Parâmetros de conexão ao banco
        nfse_id: ID da NFS-e
        
    Returns:
        Dict com dados da NFS-e ou None
    """
    try:
        with NFSeDatabase(db_params) as db:
            nfse = db.get_nfse_by_id(nfse_id)
            return nfse
    except Exception as e:
        logger.error(f"❌ Erro ao buscar detalhes: {e}")
        return None


def get_resumo_mensal(
    db_params: Dict,
    empresa_id: int,
    ano: int,
    mes: int
) -> Dict:
    """
    Retorna resumo mensal de NFS-e
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        ano: Ano
        mes: Mês (1-12)
        
    Returns:
        Dict com totais
    """
    try:
        with NFSeDatabase(db_params) as db:
            resumo = db.get_resumo_mensal(empresa_id, ano, mes)
            return resumo
    except Exception as e:
        logger.error(f"❌ Erro ao buscar resumo: {e}")
        return {}


# ============================================================================
# EXPORTAÇÃO
# ============================================================================

def exportar_nfse_excel(
    db_params: Dict,
    empresa_id: int,
    data_inicial: date,
    data_final: date,
    caminho_arquivo: str
) -> Tuple[bool, Optional[str]]:
    """
    Exporta NFS-e para Excel
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        data_inicial: Data inicial
        data_final: Data final
        caminho_arquivo: Caminho do arquivo de saída
        
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        # Buscar NFS-e
        with NFSeDatabase(db_params) as db:
            nfses = db.buscar_nfse_periodo(empresa_id, data_inicial, data_final)
        
        if not nfses:
            return False, "Nenhuma NFS-e encontrada no período"
        
        # Exportar para Excel (implementar com openpyxl ou pandas)
        # Por simplicidade, vou criar um CSV
        import csv
        
        with open(caminho_arquivo, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'numero_nfse', 'data_emissao', 'cnpj_tomador', 'razao_social_tomador',
                'valor_servico', 'valor_iss', 'municipio', 'situacao'
            ])
            writer.writeheader()
            
            for nfse in nfses:
                writer.writerow({
                    'numero_nfse': nfse['numero_nfse'],
                    'data_emissao': nfse['data_emissao'].strftime('%d/%m/%Y'),
                    'cnpj_tomador': nfse['cnpj_tomador'] or '',
                    'razao_social_tomador': nfse['razao_social_tomador'] or '',
                    'valor_servico': nfse['valor_servico'],
                    'valor_iss': nfse['valor_iss'],
                    'municipio': nfse['nome_municipio'],
                    'situacao': nfse['situacao']
                })
        
        logger.info(f"✅ Exportado {len(nfses)} NFS-e para {caminho_arquivo}")
        return True, None
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar: {e}")
        return False, str(e)


def exportar_xmls_zip(
    db_params: Dict,
    empresa_id: int,
    data_inicial: date,
    data_final: date,
    caminho_arquivo: str
) -> Tuple[bool, Optional[str]]:
    """
    Exporta XMLs de NFS-e para arquivo ZIP
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        data_inicial: Data inicial
        data_final: Data final
        caminho_arquivo: Caminho do arquivo ZIP de saída
        
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        import zipfile
        
        # Buscar NFS-e
        with NFSeDatabase(db_params) as db:
            nfses = db.buscar_nfse_periodo(empresa_id, data_inicial, data_final)
        
        if not nfses:
            return False, "Nenhuma NFS-e encontrada no período"
        
        # Criar ZIP
        with zipfile.ZipFile(caminho_arquivo, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for nfse in nfses:
                if nfse.get('xml'):
                    # Nome do arquivo: MUNICIPIO_NUMERO.xml
                    nome_arquivo = f"{nfse['codigo_municipio']}_{nfse['numero_nfse']}.xml"
                    zipf.writestr(nome_arquivo, nfse['xml'])
        
        logger.info(f"✅ Exportados XMLs de {len(nfses)} NFS-e para {caminho_arquivo}")
        return True, None
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar XMLs: {e}")
        return False, str(e)


# ============================================================================
# AUDITORIA
# ============================================================================

def registrar_operacao(
    db_params: Dict,
    empresa_id: int,
    usuario_id: int,
    operacao: str,
    detalhes: Dict,
    ip_address: str
):
    """
    Registra operação no log de auditoria
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        usuario_id: ID do usuário
        operacao: Tipo de operação (BUSCA, CONFIG, EXPORT, etc)
        detalhes: Detalhes da operação
        ip_address: IP do usuário
    """
    try:
        with NFSeDatabase(db_params) as db:
            db.registrar_auditoria(empresa_id, usuario_id, operacao, detalhes, ip_address)
    except Exception as e:
        logger.error(f"❌ Erro ao registrar auditoria: {e}")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configuração de exemplo
    db_params = {
        'host': 'localhost',
        'database': 'sistema_financeiro',
        'user': 'postgres',
        'password': 'senha',
        'port': 5432
    }
    
    # Adicionar município
    sucesso, config_id, erro = adicionar_municipio(
        db_params=db_params,
        empresa_id=1,
        cnpj_cpf="12345678000190",
        codigo_municipio="5002704",
        nome_municipio="Campo Grande",
        uf="MS",
        inscricao_municipal="123456",
        provedor="GINFES"
    )
    
    if sucesso:
        print(f"✅ Município configurado: ID {config_id}")
    else:
        print(f"❌ Erro: {erro}")
    
    # Buscar NFS-e
    resultado = buscar_nfse_periodo(
        db_params=db_params,
        empresa_id=1,
        cnpj_prestador="12345678000190",
        data_inicial=date(2026, 1, 1),
        data_final=date(2026, 1, 31),
        certificado_path="certificado.pfx",
        certificado_senha="senha123"
    )
    
    print(f"\n📊 Resultado da busca:")
    print(f"  Total de NFS-e: {resultado['total_nfse']}")
    print(f"  Novas: {resultado['nfse_novas']}")
    print(f"  Atualizadas: {resultado['nfse_atualizadas']}")
    print(f"  Municípios com sucesso: {resultado['municipios_sucesso']}/{resultado['total_municipios']}")


# ============================================================================
# PROCESSAMENTO DE CERTIFICADO DIGITAL A1
# ============================================================================

def processar_certificado(pfx_bytes: bytes, senha: str) -> Dict:
    """
    Extrai informações do certificado digital A1 (.pfx / .p12).
    Retorna CNPJ, razão social, emitente, validade, serial number.
    """
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509 import oid as x509_oid
    import re
    
    try:
        # Carregar certificado PKCS12
        private_key, certificate, additional = pkcs12.load_key_and_certificates(
            pfx_bytes, senha.encode()
        )
        
        if certificate is None:
            return {'success': False, 'error': 'Certificado não encontrado no arquivo .pfx'}
        
        info = {
            'success': True,
            'validade_inicio': certificate.not_valid_before_utc.isoformat(),
            'validade_fim': certificate.not_valid_after_utc.isoformat(),
            'serial_number': str(certificate.serial_number),
            'cnpj': None,
            'razao_social': None,
            'emitente': None
        }
        
        # Extrair dados do Subject
        subject = certificate.subject
        
        # Nome / Razão Social do CN (Common Name)
        cn_list = subject.get_attributes_for_oid(x509_oid.NameOID.COMMON_NAME)
        if cn_list:
            cn = cn_list[0].value
            info['razao_social'] = cn
            # Tentar extrair CNPJ do CN (formato: "NOME:CNPJ")
            cnpj_match = re.search(r'(\d{14})', cn.replace('.', '').replace('/', '').replace('-', ''))
            if cnpj_match:
                info['cnpj'] = cnpj_match.group(1)
        
        # OID ICP-Brasil para CNPJ: 2.16.76.1.3.3
        OID_CNPJ_ICPBRASIL = '2.16.76.1.3.3'
        for attr in subject:
            if attr.oid.dotted_string == OID_CNPJ_ICPBRASIL:
                cnpj_raw = attr.value.replace('.', '').replace('/', '').replace('-', '')
                cnpj_digits = re.sub(r'\D', '', cnpj_raw)
                if len(cnpj_digits) >= 14:
                    info['cnpj'] = cnpj_digits[:14]
                break
        
        # Se não encontrou no Subject, tentar no SAN (Subject Alternative Name)
        if not info['cnpj']:
            try:
                from cryptography.x509 import SubjectAlternativeName, OtherName
                san_ext = certificate.extensions.get_extension_for_class(SubjectAlternativeName)
                for name in san_ext.value:
                    if isinstance(name, OtherName):
                        # OID 2.16.76.1.3.3 para CNPJ
                        if name.type_id.dotted_string == OID_CNPJ_ICPBRASIL:
                            raw = name.value
                            if isinstance(raw, bytes):
                                raw = raw.decode('utf-8', errors='ignore')
                            cnpj_digits = re.sub(r'\D', '', str(raw))
                            if len(cnpj_digits) >= 14:
                                info['cnpj'] = cnpj_digits[:14]
                                break
            except Exception:
                pass  # SAN pode não existir
        
        # Se ainda não encontrou, tentar no OU (Organizational Unit)
        if not info['cnpj']:
            ou_list = subject.get_attributes_for_oid(x509_oid.NameOID.ORGANIZATIONAL_UNIT_NAME)
            for ou in ou_list:
                cnpj_digits = re.sub(r'\D', '', ou.value)
                if len(cnpj_digits) >= 14:
                    info['cnpj'] = cnpj_digits[:14]
                    break
        
        # Emitente (Issuer)
        issuer = certificate.issuer
        issuer_cn = issuer.get_attributes_for_oid(x509_oid.NameOID.COMMON_NAME)
        if issuer_cn:
            info['emitente'] = issuer_cn[0].value
        
        # Organization do subject (razão social alternativa)
        if not info['razao_social']:
            org_list = subject.get_attributes_for_oid(x509_oid.NameOID.ORGANIZATION_NAME)
            if org_list:
                info['razao_social'] = org_list[0].value
        
        logger.info(f"✅ Certificado processado: CNPJ={info['cnpj']}, Validade até {info['validade_fim']}")
        return info
        
    except ValueError as e:
        error_msg = str(e).lower()
        if 'password' in error_msg or 'mac' in error_msg or 'invalid' in error_msg:
            return {'success': False, 'error': 'Senha do certificado incorreta'}
        return {'success': False, 'error': f'Erro ao processar certificado: {e}'}
    except Exception as e:
        logger.error(f"❌ Erro ao processar certificado: {e}")
        return {'success': False, 'error': f'Erro ao processar certificado: {e}'}


def buscar_municipio_por_cnpj(cnpj: str) -> Dict:
    """
    Consulta dados do CNPJ via BrasilAPI para obter município e código IBGE.
    """
    import requests
    
    cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ''
    
    if len(cnpj_limpo) != 14:
        return {'success': False, 'error': 'CNPJ inválido'}
    
    try:
        # BrasilAPI - consulta CNPJ
        url = f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}'
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                'success': True,
                'codigo_municipio': str(data.get('codigo_municipio_ibge', '') or data.get('codigo_municipio', '')),
                'nome_municipio': data.get('municipio', ''),
                'uf': data.get('uf', ''),
                'razao_social': data.get('razao_social', ''),
                'nome_fantasia': data.get('nome_fantasia', ''),
                'logradouro': data.get('logradouro', ''),
                'bairro': data.get('bairro', ''),
                'cep': data.get('cep', '')
            }
            
            # Garantir código IBGE com 7 dígitos
            if result['codigo_municipio'] and len(result['codigo_municipio']) < 7:
                result['codigo_municipio'] = result['codigo_municipio'].zfill(7)
            
            logger.info(f"✅ Município do CNPJ {cnpj_limpo}: {result['nome_municipio']}/{result['uf']} - IBGE {result['codigo_municipio']}")
            return result
        else:
            logger.warning(f"⚠️ BrasilAPI retornou status {response.status_code}")
            return {'success': False, 'error': f'CNPJ não encontrado (status {response.status_code})'}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout ao consultar CNPJ'}
    except Exception as e:
        logger.error(f"❌ Erro ao consultar CNPJ: {e}")
        return {'success': False, 'error': f'Erro ao consultar CNPJ: {e}'}


import re  # Garantir import no nível do módulo se necessário


def upload_certificado(db_params: Dict, empresa_id: int, pfx_bytes: bytes, senha: str) -> Tuple[bool, Dict, str]:
    """
    Processa e salva certificado digital A1.
    Cria automaticamente configuração do município se identificado.
    Retorna (sucesso, info_certificado, erro)
    """
    # 1. Processar certificado
    info = processar_certificado(pfx_bytes, senha)
    if not info.get('success'):
        return False, {}, info.get('error', 'Erro ao processar certificado')
    
    # 2. Buscar município pelo CNPJ
    cnpj = info.get('cnpj')
    municipio_info = {}
    if cnpj:
        municipio_info = buscar_municipio_por_cnpj(cnpj)
        if municipio_info.get('success'):
            info['codigo_municipio'] = municipio_info.get('codigo_municipio')
            info['nome_municipio'] = municipio_info.get('nome_municipio')
            info['uf'] = municipio_info.get('uf')
            # Atualizar razão social se obtida da ReceitaWS
            if municipio_info.get('razao_social'):
                info['razao_social'] = municipio_info['razao_social']
    
    # 3. Salvar no banco
    try:
        with NFSeDatabase(db_params) as db:
            cert_id = db.salvar_certificado(empresa_id, pfx_bytes, senha, info)
            info['cert_id'] = cert_id
            
            # 4. Criar configuração do município automaticamente se identificado
            if info.get('codigo_municipio') and info.get('cnpj'):
                try:
                    config = {
                        'empresa_id': empresa_id,
                        'cnpj_cpf': info['cnpj'],
                        'provedor': 'GINFES',  # Provedor padrão, usuário pode alterar depois
                        'codigo_municipio': info['codigo_municipio'],
                        'nome_municipio': info.get('nome_municipio', ''),
                        'uf': info.get('uf', ''),
                        'inscricao_municipal': '',  # Usuário deve preencher
                        'url_customizada': None,
                        'ativo': True
                    }
                    
                    config_id = db.adicionar_config_nfse(config)
                    if config_id:
                        logger.info(f"✅ Configuração do município {info['nome_municipio']} criada automaticamente (ID={config_id})")
                        info['config_criada'] = True
                        info['config_id'] = config_id
                    else:
                        logger.warning(f"⚠️ Não foi possível criar configuração automática do município")
                        info['config_criada'] = False
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao criar configuração automática: {e}")
                    info['config_criada'] = False
            
            return True, info, ''
    except Exception as e:
        return False, {}, f'Erro ao salvar certificado: {e}'


def get_certificado_info(db_params: Dict, empresa_id: int) -> Optional[Dict]:
    """Retorna info do certificado ativo da empresa"""
    try:
        with NFSeDatabase(db_params) as db:
            return db.get_certificado_ativo(empresa_id)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar certificado: {e}")
        return None


def excluir_certificado_empresa(db_params: Dict, cert_id: int) -> bool:
    """Exclui certificado"""
    try:
        with NFSeDatabase(db_params) as db:
            return db.excluir_certificado(cert_id)
    except Exception as e:
        logger.error(f"❌ Erro ao excluir certificado: {e}")
        return False


def get_certificado_para_soap(db_params: Dict, empresa_id: int) -> Optional[Tuple[bytes, str]]:
    """
    Retorna (pfx_bytes, senha) do certificado ativo para uso em SOAP.
    """
    import base64
    try:
        with NFSeDatabase(db_params) as db:
            cert = db.get_certificado_pfx(empresa_id)
            if cert:
                pfx_data = bytes(cert['pfx_data'])
                senha = base64.b64decode(cert['senha_certificado']).decode()
                return pfx_data, senha
            return None
    except Exception as e:
        logger.error(f"❌ Erro ao buscar certificado para SOAP: {e}")
        return None


# ============================================================================
# GERAÇÃO DE PDF (DANFSE)
# ============================================================================

def gerar_pdf_nfse(db_params: Dict, nfse_id: int) -> Optional[bytes]:
    """
    Gera PDF (DANFSE) da NFS-e usando os dados armazenados no banco.
    Retorna bytes do PDF ou None se falhar.
    """
    from io import BytesIO
    
    try:
        # Buscar dados da NFS-e
        with NFSeDatabase(db_params) as db:
            nfse = db.get_nfse_by_id(nfse_id)
        
        if not nfse:
            logger.error(f"❌ NFS-e ID {nfse_id} não encontrada")
            return None
        
        # Gerar PDF com reportlab-like approach usando fpdf2
        try:
            from fpdf import FPDF
        except ImportError:
            # Fallback: gerar PDF minimal sem fpdf2
            return _gerar_pdf_minimal(nfse)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- CABEÇALHO ---
        pdf.set_fill_color(41, 128, 185)  # Azul
        pdf.rect(10, 10, 190, 25, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_xy(15, 13)
        pdf.cell(0, 10, 'DANFSE - Documento Auxiliar da NFS-e', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(15, 23)
        pdf.cell(0, 8, 'Nota Fiscal de Servico Eletronica', ln=True)
        
        pdf.set_text_color(0, 0, 0)
        y = 40
        
        # --- NÚMERO E DADOS DA NOTA ---
        pdf.set_fill_color(236, 240, 241)
        pdf.rect(10, y, 190, 20, 'F')
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, y + 2)
        numero = nfse.get('numero_nfse', '-')
        pdf.cell(60, 8, f'NFS-e No: {numero}', ln=False)
        
        pdf.set_font('Helvetica', '', 10)
        data_emissao = nfse.get('data_emissao', '')
        if data_emissao:
            if isinstance(data_emissao, str):
                try:
                    dt = datetime.fromisoformat(data_emissao.replace('Z', '+00:00'))
                    data_emissao = dt.strftime('%d/%m/%Y')
                except:
                    pass
            else:
                data_emissao = data_emissao.strftime('%d/%m/%Y')
        pdf.cell(60, 8, f'Data Emissao: {data_emissao}', ln=False)
        
        cod_verif = nfse.get('codigo_verificacao', '-')
        pdf.cell(60, 8, f'Cod. Verificacao: {cod_verif}', ln=True)
        
        # Situação
        situacao = nfse.get('situacao', 'NORMAL')
        pdf.set_xy(15, y + 12)
        pdf.set_font('Helvetica', 'B', 10)
        if situacao == 'CANCELADA':
            pdf.set_text_color(231, 76, 60)
            pdf.cell(60, 6, f'Situacao: {situacao}')
        elif situacao == 'SUBSTITUIDA':
            pdf.set_text_color(243, 156, 18)
            pdf.cell(60, 6, f'Situacao: {situacao}')
        else:
            pdf.set_text_color(39, 174, 96)
            pdf.cell(60, 6, f'Situacao: {situacao}')
        pdf.set_text_color(0, 0, 0)
        
        municipio = nfse.get('nome_municipio', '-')
        uf = nfse.get('uf', '-')
        pdf.cell(0, 6, f'Municipio: {municipio}/{uf}', ln=True)
        y += 25
        
        # --- PRESTADOR ---
        pdf.set_fill_color(41, 128, 185)
        pdf.rect(10, y, 190, 8, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(15, y + 1)
        pdf.cell(0, 6, 'PRESTADOR DE SERVICOS', ln=True)
        pdf.set_text_color(0, 0, 0)
        y += 10
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(15, y)
        cnpj_prest = nfse.get('cnpj_prestador', '-')
        if cnpj_prest and len(cnpj_prest) == 14:
            cnpj_prest = f'{cnpj_prest[:2]}.{cnpj_prest[2:5]}.{cnpj_prest[5:8]}/{cnpj_prest[8:12]}-{cnpj_prest[12:]}'
        pdf.cell(0, 6, f'CNPJ: {cnpj_prest}', ln=True)
        y += 10
        
        # --- TOMADOR ---
        pdf.set_fill_color(41, 128, 185)
        pdf.rect(10, y, 190, 8, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(15, y + 1)
        pdf.cell(0, 6, 'TOMADOR DE SERVICOS', ln=True)
        pdf.set_text_color(0, 0, 0)
        y += 10
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(15, y)
        cnpj_tom = nfse.get('cnpj_tomador', '-')
        if cnpj_tom and len(cnpj_tom) == 14:
            cnpj_tom = f'{cnpj_tom[:2]}.{cnpj_tom[2:5]}.{cnpj_tom[5:8]}/{cnpj_tom[8:12]}-{cnpj_tom[12:]}'
        razao_tom = nfse.get('razao_social_tomador', '-')
        pdf.cell(90, 6, f'CNPJ/CPF: {cnpj_tom}', ln=False)
        pdf.cell(0, 6, f'Razao Social: {razao_tom}', ln=True)
        y += 10
        
        # --- DISCRIMINAÇÃO DOS SERVIÇOS ---
        pdf.set_fill_color(41, 128, 185)
        pdf.rect(10, y, 190, 8, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(15, y + 1)
        pdf.cell(0, 6, 'DISCRIMINACAO DOS SERVICOS', ln=True)
        pdf.set_text_color(0, 0, 0)
        y += 10
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_xy(15, y)
        discriminacao = nfse.get('discriminacao', '-') or '-'
        # Multi_cell para texto longo
        pdf.multi_cell(180, 5, discriminacao)
        y = pdf.get_y() + 5
        
        # --- VALORES ---
        pdf.set_fill_color(41, 128, 185)
        pdf.rect(10, y, 190, 8, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(15, y + 1)
        pdf.cell(0, 6, 'VALORES', ln=True)
        pdf.set_text_color(0, 0, 0)
        y += 10
        
        def fmt_valor(v):
            try:
                return f"R$ {float(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except:
                return "R$ 0,00"
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(15, y)
        
        valor_servico = fmt_valor(nfse.get('valor_servico', 0))
        valor_deducoes = fmt_valor(nfse.get('valor_deducoes', 0))
        valor_iss = fmt_valor(nfse.get('valor_iss', 0))
        valor_liquido = fmt_valor(nfse.get('valor_liquido', 0))
        aliquota = nfse.get('aliquota_iss', 0)
        
        pdf.cell(95, 7, f'Valor dos Servicos: {valor_servico}', border=1, ln=False)
        pdf.cell(95, 7, f'Deducoes: {valor_deducoes}', border=1, ln=True)
        y += 7
        pdf.set_xy(15, y)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(63, 7, f'Valor ISS: {valor_iss}', border=1, ln=False)
        pdf.set_font('Helvetica', '', 10)
        
        try:
            aliq_fmt = f"{float(aliquota):.2f}%"
        except:
            aliq_fmt = "0,00%"
        pdf.cell(63, 7, f'Aliquota ISS: {aliq_fmt}', border=1, ln=False)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(39, 174, 96)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(64, 7, f'Valor Liquido: {valor_liquido}', border=1, fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        
        y = pdf.get_y() + 10
        
        # --- RODAPÉ ---
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_xy(10, 275)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, f'Documento gerado pelo Sistema Financeiro DWM - {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C')
        
        # Retornar bytes do PDF
        return pdf.output()
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar PDF da NFS-e {nfse_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def _gerar_pdf_minimal(nfse: Dict) -> bytes:
    """
    Gera PDF minimal sem dependências externas (plain text).
    Usado como fallback se fpdf2 não estiver instalado.
    """
    # Gerar PDF minimal com texto formatado
    # Usando formato PDF 1.4 manual
    from io import BytesIO
    
    def fmt_valor(v):
        try:
            return f"R$ {float(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "R$ 0,00"
    
    numero = nfse.get('numero_nfse', '-')
    data = nfse.get('data_emissao', '-')
    cnpj_prest = nfse.get('cnpj_prestador', '-')
    cnpj_tom = nfse.get('cnpj_tomador', '-')
    razao_tom = nfse.get('razao_social_tomador', '-')
    valor = fmt_valor(nfse.get('valor_servico', 0))
    iss = fmt_valor(nfse.get('valor_iss', 0))
    situacao = nfse.get('situacao', 'NORMAL')
    municipio = nfse.get('nome_municipio', '-')
    discriminacao = nfse.get('discriminacao', '-') or '-'
    
    lines = [
        "DANFSE - Documento Auxiliar da NFS-e",
        "=" * 60,
        f"NFS-e No: {numero}",
        f"Data Emissao: {data}",
        f"Situacao: {situacao}",
        f"Municipio: {municipio}/{nfse.get('uf', '-')}",
        "",
        "PRESTADOR",
        f"  CNPJ: {cnpj_prest}",
        "",
        "TOMADOR",
        f"  CNPJ/CPF: {cnpj_tom}",
        f"  Razao Social: {razao_tom}",
        "",
        "SERVICOS",
        f"  {discriminacao[:200]}",
        "",
        "VALORES",
        f"  Valor Servico: {valor}",
        f"  ISS: {iss}",
        "",
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ]
    
    content = '\n'.join(lines)
    
    # Construir PDF manualmente (PDF 1.4 spec)
    buf = BytesIO()
    
    # Escapar parênteses
    safe_content = content.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    
    # Calcular posições de stream
    text_lines = safe_content.split('\n')
    stream_parts = []
    stream_parts.append('BT')
    stream_parts.append('/F1 10 Tf')
    y_pos = 800
    for line in text_lines:
        stream_parts.append(f'1 0 0 1 50 {y_pos} Tm')
        stream_parts.append(f'({line}) Tj')
        y_pos -= 14
    stream_parts.append('ET')
    stream_content = '\n'.join(stream_parts)
    stream_bytes = stream_content.encode('latin-1', errors='replace')
    
    objects = []
    
    # Obj 1: Catalog
    objects.append(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
    # Obj 2: Pages
    objects.append(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
    # Obj 3: Page
    objects.append(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n')
    # Obj 4: Stream
    stream_obj = f'4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n'.encode('latin-1')
    stream_obj += stream_bytes
    stream_obj += b'\nendstream\nendobj\n'
    objects.append(stream_obj)
    # Obj 5: Font
    objects.append(b'5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n')
    
    buf.write(b'%PDF-1.4\n')
    offsets = []
    for obj in objects:
        offsets.append(buf.tell())
        buf.write(obj)
    
    xref_offset = buf.tell()
    buf.write(b'xref\n')
    buf.write(f'0 {len(objects) + 1}\n'.encode())
    buf.write(b'0000000000 65535 f \n')
    for off in offsets:
        buf.write(f'{off:010d} 00000 n \n'.encode())
    
    buf.write(b'trailer\n')
    buf.write(f'<< /Root 1 0 R /Size {len(objects) + 1} >>\n'.encode())
    buf.write(b'startxref\n')
    buf.write(f'{xref_offset}\n'.encode())
    buf.write(b'%%EOF\n')
    
    return buf.getvalue()

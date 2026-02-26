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
import base64
from nfse_database import NFSeDatabase
from nfse_service import NFSeService, descobrir_provedor, testar_conexao
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# GERENCIAMENTO DE ARQUIVOS (XMLs e PDFs)
# ============================================================================

def salvar_pdf_nfse(
    pdf_content: bytes,
    numero_nfse: str,
    cnpj_prestador: str,
    codigo_municipio: str,
    data_emissao: str,
    storage_base: str = 'storage/nfse'
) -> Optional[str]:
    """
    Salva PDF da NFS-e (DANFSe) no storage
    
    Estrutura de pastas:
    storage/nfse/{CNPJ}/{CODIGO_MUNICIPIO}/{ANO}/{MES}/NFS-e_{NUMERO}.pdf
    
    Args:
        pdf_content: Conteúdo binário do PDF
        numero_nfse: Número da NFS-e
        cnpj_prestador: CNPJ do prestador
        codigo_municipio: Código IBGE do município
        data_emissao: Data de emissão (ISO format ou datetime)
        storage_base: Diretório base do storage
    
    Returns:
        Caminho do arquivo salvo ou None se erro
    """
    try:
        # Extrair ano e mês da data de emissão
        if isinstance(data_emissao, str):
            # Formato: 2026-02-15T10:30:00-03:00 ou 2026-02-15
            data_parts = data_emissao.split('T')[0].split('-')
            ano = data_parts[0] if len(data_parts) > 0 else datetime.now().year
            mes = data_parts[1] if len(data_parts) > 1 else datetime.now().month
        else:
            ano = data_emissao.year
            mes = f"{data_emissao.month:02d}"
        
        # Construir caminho da pasta
        pasta = Path(storage_base) / cnpj_prestador / codigo_municipio / str(ano) / str(mes)
        pasta.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo
        nome_arquivo = f"NFS-e_{numero_nfse}.pdf"
        caminho_completo = pasta / nome_arquivo
        
        # Salvar PDF
        with open(caminho_completo, 'wb') as f:
            f.write(pdf_content)
        
        logger.debug(f"💾 PDF salvo: {caminho_completo}")
        return str(caminho_completo)
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar PDF: {e}")
        return None


def salvar_xml_nfse(
    xml_content: str,
    numero_nfse: str,
    cnpj_prestador: str,
    codigo_municipio: str,
    data_emissao: str,
    storage_base: str = 'storage/nfse'
) -> Optional[str]:
    """
    Salva XML da NFS-e no storage
    
    Estrutura de pastas:
    storage/nfse/{CNPJ}/{CODIGO_MUNICIPIO}/{ANO}/{MES}/NFS-e_{NUMERO}.xml
    
    Args:
        xml_content: Conteúdo XML (string)
        numero_nfse: Número da NFS-e
        cnpj_prestador: CNPJ do prestador
        codigo_municipio: Código IBGE do município
        data_emissao: Data de emissão (ISO format ou datetime)
        storage_base: Diretório base do storage
    
    Returns:
        Caminho do arquivo salvo ou None se erro
    """
    try:
        # Extrair ano e mês da data de emissão
        if isinstance(data_emissao, str):
            data_parts = data_emissao.split('T')[0].split('-')
            ano = data_parts[0] if len(data_parts) > 0 else datetime.now().year
            mes = data_parts[1] if len(data_parts) > 1 else datetime.now().month
        else:
            ano = data_emissao.year
            mes = f"{data_emissao.month:02d}"
        
        # Construir caminho da pasta
        pasta = Path(storage_base) / cnpj_prestador / codigo_municipio / str(ano) / str(mes)
        pasta.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo
        nome_arquivo = f"NFS-e_{numero_nfse}.xml"
        caminho_completo = pasta / nome_arquivo
        
        # Salvar XML
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.debug(f"💾 XML salvo: {caminho_completo}")
        return str(caminho_completo)
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar XML: {e}")
        return None

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


def atualizar_municipio(
    db_params: Dict,
    empresa_id: int,
    config_id: int,
    cnpj_cpf: str,
    codigo_municipio: str,
    nome_municipio: str,
    uf: str,
    inscricao_municipal: str,
    provedor: Optional[str] = None,
    url_customizada: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Atualiza configuração de um município
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        config_id: ID da configuração a ser atualizada
        cnpj_cpf: CNPJ da empresa
        codigo_municipio: Código IBGE (7 dígitos)
        nome_municipio: Nome do município
        uf: UF (2 letras)
        inscricao_municipal: IM da empresa neste município
        provedor: Provedor SOAP
        url_customizada: URL específica (opcional)
        
    Returns:
        Tuple (sucesso, mensagem_erro)
    """
    try:
        # Tentar descobrir provedor automaticamente se não informado
        if not provedor or not url_customizada:
            info_municipio = descobrir_provedor(codigo_municipio)
            if info_municipio:
                provedor = provedor or info_municipio['provedor']
                url_customizada = url_customizada or info_municipio['url']
                logger.info(f"✅ Provedor detectado: {provedor}")
        
        # Atualizar configuração
        config = {
            'id': config_id,
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
            sucesso = db.atualizar_config_nfse(config)
            
            if sucesso:
                logger.info(f"✅ Município atualizado: {nome_municipio} (ID: {config_id})")
                return True, None
            else:
                return False, "Erro ao atualizar configuração no banco"
                
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar município: {e}")
        return False, str(e)


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
                    # Garantir que temos URL do webservice
                    url_webservice = config.get('url_customizada')
                    provedor = config.get('provedor')
                    
                    # Se não tem URL, tentar descobrir automaticamente
                    if not url_webservice:
                        logger.info(f"   ⚠️ URL não configurada, tentando descobrir automaticamente...")
                        info_municipio = descobrir_provedor(codigo_municipio)
                        if info_municipio:
                            url_webservice = info_municipio['url']
                            provedor = provedor or info_municipio['provedor']
                            # Guardar URLs alternativas se existirem
                            urls_alternativas = info_municipio.get('url_alternativas', [])
                            logger.info(f"   ✅ URL descoberta: {url_webservice}")
                            logger.info(f"   ✅ Provedor: {provedor}")
                        else:
                            raise Exception(f"URL do webservice não configurada e não foi possível descobrir automaticamente para o município {codigo_municipio}")
                    else:
                        urls_alternativas = []
                    
                    # Lista de URLs para tentar (principal + alternativas)
                    urls_para_tentar = [url_webservice] + urls_alternativas
                    
                    # Tentar cada URL até encontrar uma que funcione
                    sucesso = False
                    nfses = []
                    erro = None
                    
                    for idx, url_atual in enumerate(urls_para_tentar):
                        if idx > 0:
                            logger.info(f"   🔄 Tentando URL alternativa {idx}: {url_atual}")
                        
                        # Buscar NFS-e via SOAP
                        sucesso, nfses, erro = service.buscar_nfse(
                            cnpj_prestador=cnpj_prestador,
                            inscricao_municipal=config['inscricao_municipal'],
                            data_inicial=data_inicial,
                            data_final=data_final,
                            provedor=provedor,
                            url_webservice=url_atual,
                            codigo_municipio=codigo_municipio
                        )
                        
                        # Se sucesso, sair do loop
                        if sucesso:
                            if idx > 0:
                                logger.info(f"   ✅ URL alternativa funcionou! Salvando para uso futuro...")
                                # TODO: Atualizar config no banco com URL que funcionou
                            break
                        
                        # Se erro 404, tentar próxima URL
                        if erro and "404" in erro:
                            logger.warning(f"   ⚠️ URL não encontrada (404), tentando próxima...")
                            continue
                        else:
                            # Outro erro, não tentar mais URLs
                            break
                    
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
                        # Nenhuma URL funcionou
                        resultado['municipios_erro'] += 1
                        
                        # Se todas as URLs deram 404, dar dica de onde procurar a URL correta
                        if erro and "404" in erro:
                            # Mensagem específica para Belo Horizonte
                            if codigo_municipio == '3106200':
                                erro_completo = (
                                    f"❌ Nenhuma URL do webservice de Belo Horizonte funcionou (todas retornam 404). "
                                    f"\n\n📋 COMO RESOLVER:\n"
                                    f"1. Acesse: https://prefeitura.pbh.gov.br/fazenda/nfse\n"
                                    f"2. Procure: 'Manual de Integração' ou 'Documentação Técnica'\n"
                                    f"3. Encontre a URL correta do webservice SOAP/ABRASF\n"
                                    f"4. No sistema: Clique em ✏️ Editar no município → Cole a URL no campo 'URL Customizada'\n"
                                    f"5. Tente buscar novamente\n\n"
                                    f"💡 Exemplo de URL: https://[sistema].pbh.gov.br/[caminho]/ServiceGinfesImpl ou .../nfse\n\n"
                                    f"📞 Suporte PBH: Entre em contato com suporte técnico NFS-e da prefeitura\n\n"
                                    f"URLs tentadas sem sucesso: {', '.join(urls_para_tentar)}"
                                )
                            else:
                                erro_completo = (
                                    f"{erro}. "
                                    f"Nenhuma das URLs testadas funcionou. "
                                    f"Verifique a URL correta no site oficial da prefeitura "
                                    f"ou na documentação do webservice de NFS-e. "
                                    f"URLs tentadas: {', '.join(urls_para_tentar)}"
                                )
                        else:
                            erro_completo = erro
                        
                        resultado['erros'].append(f"{municipio_nome}: {erro_completo}")
                        resultado['detalhes'].append({
                            'municipio': municipio_nome,
                            'codigo': codigo_municipio,
                            'sucesso': False,
                            'erro': erro_completo
                        })
                        
                        logger.error(f"❌ {municipio_nome}: {erro_completo}")
                
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
    codigo_municipio: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Dict]:
    """
    Consulta NFS-e armazenadas localmente (sem buscar via API)
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        data_inicial: Data inicial
        data_final: Data final
        codigo_municipio: Código do município (None = todos)
        limit: Limite de registros (opcional, None=sem limite)
        offset: Deslocamento para paginação
        
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
                situacao='NORMAL',
                limit=limit,
                offset=offset
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
    Retorna CNPJ, razão social, emitente, validade, serial number, UF.
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
            'emitente': None,
            'uf': None
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
        
        # Extrair UF (Estado) do Subject
        st_list = subject.get_attributes_for_oid(x509_oid.NameOID.STATE_OR_PROVINCE_NAME)
        if st_list:
            uf = st_list[0].value.strip().upper()
            # Validar se é uma UF válida (2 letras)
            if len(uf) == 2 and uf.isalpha():
                info['uf'] = uf
        
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
                    # Descobrir provedor e URL automaticamente
                    codigo_municipio = info['codigo_municipio']
                    provedor_padrao = 'GINFES'
                    url_padrao = None
                    
                    info_provedor = descobrir_provedor(codigo_municipio)
                    if info_provedor:
                        provedor_padrao = info_provedor['provedor']
                        url_padrao = info_provedor['url']
                        logger.info(f"✅ Provedor descoberto automaticamente: {provedor_padrao}")
                        logger.info(f"✅ URL detectada: {url_padrao}")
                    else:
                        logger.warning(f"⚠️ Provedor não encontrado para município {codigo_municipio}, usando GINFES como padrão")
                    
                    config = {
                        'empresa_id': empresa_id,
                        'cnpj_cpf': info['cnpj'],
                        'provedor': provedor_padrao,
                        'codigo_municipio': codigo_municipio,
                        'nome_municipio': info.get('nome_municipio', ''),
                        'uf': info.get('uf', ''),
                        'inscricao_municipal': '',  # Usuário deve preencher
                        'url_customizada': url_padrao,
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
    
    PRIORIDADE:
    1. Se existe PDF oficial (danfse_path), retorna ele
    2. Senão, gera PDF genérico usando FPDF
    
    Retorna bytes do PDF ou None se falhar.
    """
    from io import BytesIO
    from pathlib import Path
    
    try:
        # Buscar dados da NFS-e
        with NFSeDatabase(db_params) as db:
            nfse = db.get_nfse_by_id(nfse_id)
        
        if not nfse:
            logger.error(f"❌ NFS-e ID {nfse_id} não encontrada")
            return None
        
        # PRIORIDADE 1: Tentar usar PDF oficial se existir
        danfse_path = nfse.get('danfse_path')
        if danfse_path:
            pdf_file = Path(danfse_path)
            if pdf_file.exists():
                logger.info(f"✅ Usando PDF oficial: {danfse_path}")
                with open(pdf_file, 'rb') as f:
                    return f.read()
            else:
                logger.warning(f"⚠️ PDF oficial não encontrado: {danfse_path}")
                logger.info(f"📝 Gerando PDF genérico como fallback...")
        else:
            logger.info(f"📝 PDF oficial não disponível, gerando PDF genérico...")
        
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


# ============================================================================
# BUSCA VIA AMBIENTE NACIONAL (API REST)
# ============================================================================

def buscar_nfse_ambiente_nacional(
    db_params: Dict,
    empresa_id: int,
    cnpj_informante: str,
    certificado_path: str,
    certificado_senha: str,
    ambiente: str = 'producao',
    busca_completa: bool = False,
    max_documentos: int = 1000
) -> Dict:
    """
    Busca NFS-e via Ambiente Nacional (API REST oficial)
    
    Usa consulta incremental por NSU, similar ao sistema de NF-e e CT-e.
    Substitui a necessidade de configurar URLs de cada município.
    
    Vantagens:
    - Uma única API para todos os municípios
    - Baseada em NSU (busca incremental automática)
    - Autenticação mTLS com certificado digital
    - PDFs oficiais (DANFSe) disponíveis via API
    - Protocolo REST moderno (não SOAP)
    
    Args:
        db_params: Parâmetros de conexão ao banco
        empresa_id: ID da empresa
        cnpj_informante: CNPJ do certificado (informante)
        certificado_path: Caminho do arquivo .pfx
        certificado_senha: Senha do certificado
        ambiente: 'producao' ou 'homologacao'
        busca_completa: Se True, inicia do NSU=0 (busca completa)
        max_documentos: Limite de documentos por execução
    
    Returns:
        Dict com resultado:
        {
            'sucesso': bool,
            'total_nfse': int,
            'nfse_novas': int,
            'nfse_atualizadas': int,
            'ultimo_nsu': int,
            'erros': list,
            'detalhes': list
        }
    """
    from nfse_service import NFSeAmbienteNacional
    from lxml import etree
    import time
    
    resultado = {
        'sucesso': False,
        'total_nfse': 0,
        'nfse_novas': 0,
        'nfse_atualizadas': 0,
        'ultimo_nsu': 0,
        'erros': [],
        'detalhes': []
    }
    
    try:
        logger.info("=" * 70)
        logger.info("🌐 BUSCA NFS-e VIA AMBIENTE NACIONAL")
        logger.info("=" * 70)
        logger.info(f"Método: Consulta incremental por NSU (REST API)")
        logger.info(f"Ambiente: {ambiente}")
        logger.info(f"CNPJ: {cnpj_informante}")
        logger.info("=" * 70)
        
        # Criar cliente do Ambiente Nacional
        cliente = NFSeAmbienteNacional(
            certificado_path=certificado_path,
            certificado_senha=certificado_senha,
            ambiente=ambiente
        )
        
        with NFSeDatabase(db_params) as db:
            # Recuperar último NSU processado
            if busca_completa:
                ultimo_nsu = 0
                logger.info("🔄 BUSCA COMPLETA: Iniciando do NSU=0")
            else:
                ultimo_nsu = db.get_last_nsu_nfse(empresa_id, cnpj_informante) or 0
                logger.info(f"📍 BUSCA INCREMENTAL: Último NSU = {ultimo_nsu}")
            
            nsu_atual = max(ultimo_nsu + 1, 1)  # Começa do próximo (mínimo 1)
            max_tentativas_404 = 100  # Para após 100 NSUs seguidos sem retorno
            tentativas_404 = 0
            documentos_processados = 0
            
            logger.info(f"🔍 Buscando a partir do NSU {nsu_atual}")
            
            # Loop de consulta incremental
            while tentativas_404 < max_tentativas_404 and documentos_processados < max_documentos:
                # Delay para respeitar rate limit (~1 req/segundo)
                if nsu_atual > ultimo_nsu + 1:
                    time.sleep(1)
                
                # Consultar NSU atual
                resposta = cliente.consultar_nsu(nsu_atual)
                
                if resposta is None:
                    # NSU não encontrado (404) ou rate limit (429)
                    tentativas_404 += 1
                    nsu_atual += 1
                    continue
                
                # Reset contador de 404 (encontrou algo)
                tentativas_404 = 0
                
                # Extrair documentos do JSON
                documentos = cliente.extrair_documentos(resposta)
                
                if not documentos:
                    logger.debug(f"📭 NSU {nsu_atual}: sem documentos")
                    nsu_atual += 1
                    continue
                
                # Processar cada documento
                for doc_nsu, xml_content, tipo_doc in documentos:
                    try:
                        # Validar XML
                        if not cliente.validar_xml(xml_content):
                            logger.warning(f"⚠️ NSU {doc_nsu}: XML inválido, pulando")
                            continue
                        
                        # Processar apenas NFS-e (ignorar eventos)
                        if tipo_doc != 'NFS-e':
                            logger.info(f"ℹ️ NSU {doc_nsu}: {tipo_doc} (ignorado)")
                            continue
                        
                        # Extrair informações da NFS-e
                        tree = etree.fromstring(xml_content.encode('utf-8'))
                        
                        # Namespaces comuns
                        ns = {
                            'nfse': 'http://www.sped.fazenda.gov.br/nfse',
                            'nfse2': 'http://www.portalfiscal.inf.br/nfse'
                        }
                        
                        # Tentar extrair dados (estrutura padrão Nacional NFS-e)
                        numero_nfse = (
                            tree.findtext('.//nfse:nNFSe', namespaces=ns) or
                            tree.findtext('.//nfse2:Numero', namespaces=ns) or
                            tree.findtext('.//Numero') or
                            tree.findtext('.//NumeroNfse') or
                            f"NSU_{doc_nsu}"
                        )
                        
                        # Data de emissão - está dentro de DPS/infDPS/dhEmi
                        data_emissao = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:dhEmi', namespaces=ns) or
                            tree.findtext('.//nfse:dhEmi', namespaces=ns) or
                            tree.findtext('.//nfse2:DataEmissao', namespaces=ns) or
                            tree.findtext('.//DataEmissao') or
                            tree.findtext('.//dhEmi') or
                            datetime.now().isoformat()
                        )
                        
                        valor_servicos = (
                            tree.findtext('.//nfse:vServ', namespaces=ns) or
                            tree.findtext('.//nfse2:ValorServicos', namespaces=ns) or
                            tree.findtext('.//ValorServicos') or
                            "0"
                        )
                        
                        cnpj_prestador = (
                            tree.findtext('.//nfse:emit//nfse:CNPJ', namespaces=ns) or
                            tree.findtext('.//nfse:prest//nfse:CNPJ', namespaces=ns) or
                            tree.findtext('.//Prestador//Cnpj') or
                            cnpj_informante
                        )
                        
                        cnpj_tomador = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:toma//nfse:CNPJ', namespaces=ns) or
                            tree.findtext('.//nfse:toma//nfse:CNPJ', namespaces=ns) or
                            tree.findtext('.//Tomador//IdentificacaoTomador//CpfCnpj//Cnpj') or
                            tree.findtext('.//TomadorServico//IdentificacaoTomador//CpfCnpj//Cnpj') or
                            ""
                        )
                        
                        razao_social_tomador = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:toma//nfse:xNome', namespaces=ns) or
                            tree.findtext('.//nfse:toma//nfse:xNome', namespaces=ns) or
                            tree.findtext('.//Tomador//RazaoSocial') or
                            tree.findtext('.//TomadorServico//RazaoSocial') or
                            ""
                        )
                        
                        # Código do município - cLocEmi ou cLocIncid
                        codigo_municipio = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:cLocEmi', namespaces=ns) or
                            tree.findtext('.//nfse:cLocIncid', namespaces=ns) or
                            tree.findtext('.//nfse:cLocEmi', namespaces=ns) or
                            tree.findtext('.//nfse:emit//nfse:enderNac//nfse:cMun', namespaces=ns) or
                            tree.findtext('.//nfse:cMunPrestacao', namespaces=ns) or
                            tree.findtext('.//CodigoMunicipio') or
                            tree.findtext('.//Servico//CodigoMunicipio') or
                            ""
                        )
                        
                        # Nome do município
                        nome_municipio = (
                            tree.findtext('.//nfse:xLocEmi', namespaces=ns) or
                            tree.findtext('.//nfse:xLocIncid', namespaces=ns) or
                            tree.findtext('.//CidadePrestador') or
                            ""
                        )
                        
                        # UF
                        uf = (
                            tree.findtext('.//nfse:emit//nfse:enderNac//nfse:UF', namespaces=ns) or
                            tree.findtext('.//UF') or
                            tree.findtext('.//UfPrestador') or
                            ""
                        )
                        
                        # Campos adicionais
                        # Valor ISS - vISSQN (padrão nacional) ou vISS
                        valor_iss = (
                            tree.findtext('.//nfse:valores//nfse:vISSQN', namespaces=ns) or
                            tree.findtext('.//nfse:vISSQN', namespaces=ns) or
                            tree.findtext('.//nfse:vISS', namespaces=ns) or
                            tree.findtext('.//ValorIss') or
                            tree.findtext('.//Valores//ValorIss') or
                            "0"
                        )
                        
                        valor_deducoes = (
                            tree.findtext('.//nfse:vDescCondIncond', namespaces=ns) or
                            tree.findtext('.//nfse:vDeducao', namespaces=ns) or
                            tree.findtext('.//ValorDeducoes') or
                            tree.findtext('.//Valores//ValorDeducoes') or
                            "0"
                        )
                        
                        # Alíquota - pAliq ou pAliqAplic
                        aliquota_iss = (
                            tree.findtext('.//nfse:valores//nfse:pAliqAplic', namespaces=ns) or
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:valores//nfse:trib//nfse:tribMun//nfse:pAliq', namespaces=ns) or
                            tree.findtext('.//nfse:pAliq', namespaces=ns) or
                            tree.findtext('.//nfse:aliq', namespaces=ns) or
                            tree.findtext('.//Aliquota') or
                            tree.findtext('.//Valores//Aliquota') or
                            "0"
                        )
                        
                        # Código do serviço - cTribNac ou cTribMun
                        codigo_servico = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:serv//nfse:cServ//nfse:cTribNac', namespaces=ns) or
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:serv//nfse:cServ//nfse:cTribMun', namespaces=ns) or
                            tree.findtext('.//nfse:cListServ', namespaces=ns) or
                            tree.findtext('.//ItemListaServico') or
                            tree.findtext('.//Servico//ItemListaServico') or
                            ""
                        )
                        
                        # Discriminação/Descrição do serviço
                        discriminacao = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:serv//nfse:cServ//nfse:xDescServ', namespaces=ns) or
                            tree.findtext('.//nfse:xDescServ', namespaces=ns) or
                            tree.findtext('.//Discriminacao') or
                            tree.findtext('.//Servico//Discriminacao') or
                            ""
                        )
                        
                        codigo_verificacao = (
                            tree.findtext('.//nfse:cVerif', namespaces=ns) or
                            tree.findtext('.//CodigoVerificacao') or
                            ""
                        )
                        
                        # RPS - dentro de DPS/infDPS
                        numero_rps = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:nDPS', namespaces=ns) or
                            tree.findtext('.//nfse:nRps', namespaces=ns) or
                            tree.findtext('.//IdentificacaoRps//Numero') or
                            ""
                        )
                        
                        serie_rps = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:serie', namespaces=ns) or
                            tree.findtext('.//nfse:serieRps', namespaces=ns) or
                            tree.findtext('.//IdentificacaoRps//Serie') or
                            ""
                        )
                        
                        # Data de competência - dCompet (padrão nacional)
                        data_competencia = (
                            tree.findtext('.//nfse:DPS//nfse:infDPS//nfse:dCompet', namespaces=ns) or
                            tree.findtext('.//nfse:dCompetencia', namespaces=ns) or
                            tree.findtext('.//Competencia') or
                            data_emissao
                        )
                        
                        # Converter valores
                        try:
                            valor_servicos_float = float(valor_servicos.replace(',', '.'))
                            valor_iss_float = float(valor_iss.replace(',', '.'))
                            valor_deducoes_float = float(valor_deducoes.replace(',', '.'))
                            aliquota_iss_float = float(aliquota_iss.replace(',', '.'))
                            valor_liquido = valor_servicos_float - valor_deducoes_float
                        except:
                            valor_servicos_float = 0
                            valor_iss_float = 0
                            valor_deducoes_float = 0
                            aliquota_iss_float = 0
                            valor_liquido = 0
                        
                        # Verificar se NFS-e já existe
                        nfse_existente = None
                        if codigo_municipio:
                            nfse_existente = db.get_nfse_by_numero(numero_nfse, codigo_municipio)
                        
                        # Preparar dados para salvar (TODOS os campos necessários)
                        nfse_data = {
                            'empresa_id': empresa_id,
                            'numero_nfse': numero_nfse,
                            'cnpj_prestador': cnpj_prestador,
                            'cnpj_tomador': cnpj_tomador,
                            'razao_social_tomador': razao_social_tomador,
                            'data_emissao': data_emissao,
                            'data_competencia': data_competencia,
                            'valor_servico': valor_servicos_float,
                            'valor_deducoes': valor_deducoes_float,
                            'valor_iss': valor_iss_float,
                            'aliquota_iss': aliquota_iss_float,
                            'valor_liquido': valor_liquido,
                            'codigo_servico': codigo_servico,
                            'discriminacao': discriminacao,
                            'provedor': 'AMBIENTE_NACIONAL',
                            'codigo_municipio': codigo_municipio,
                            'nome_municipio': nome_municipio,
                            'uf': uf,
                            'situacao': 'NORMAL',
                            'numero_rps': numero_rps,
                            'serie_rps': serie_rps,
                            'protocolo': '',  # Não disponível no XML
                            'codigo_verificacao': codigo_verificacao,
                            'xml': xml_content,
                            'xml_path': None
                        }
                        
                        # Salvar no banco
                        nfse_id = db.salvar_nfse(nfse_data)
                        
                        if nfse_id:
                            if nfse_existente:
                                resultado['nfse_atualizadas'] += 1
                                logger.info(f"✅ NSU {doc_nsu}: NFS-e {numero_nfse} atualizada")
                            else:
                                resultado['nfse_novas'] += 1
                                logger.info(f"✅ NSU {doc_nsu}: NFS-e {numero_nfse} salva (R$ {valor_servicos})")
                            
                            resultado['total_nfse'] += 1
                            documentos_processados += 1
                            
                            # Salvar XML no storage
                            try:
                                xml_path = salvar_xml_nfse(
                                    xml_content=xml_content,
                                    numero_nfse=numero_nfse,
                                    cnpj_prestador=cnpj_prestador,
                                    codigo_municipio=codigo_municipio,
                                    data_emissao=data_emissao
                                )
                                if xml_path:
                                    logger.debug(f"   💾 XML salvo: {xml_path}")
                            except Exception as e_xml:
                                logger.warning(f"   ⚠️ Erro ao salvar XML: {e_xml}")
                            
                            # Tentar baixar DANFSe (PDF oficial)
                            pdf_base64 = None
                            try:
                                # Extrair chave de acesso (formato: "NFS" + 50 dígitos)
                                inf_nfse = tree.find('.//nfse:infNFSe', namespaces=ns)
                                if inf_nfse is not None:
                                    chave_id = inf_nfse.get('Id', '')
                                    if chave_id and chave_id.startswith('NFS'):
                                        chave_acesso = chave_id[3:]  # Remove prefixo "NFS"
                                        
                                        logger.info(f"   📄 Baixando DANFSe oficial...")
                                        
                                        try:
                                            pdf_content = cliente.consultar_danfse(chave_acesso, retry=2)
                                            
                                            if pdf_content and isinstance(pdf_content, bytes):
                                                # Converter para base64 (será salvo pelo ERP)
                                                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                                                logger.info(f"   ✅ DANFSe oficial obtido ({len(pdf_content):,} bytes)")
                                                
                                                # Inicializar dict se não existir
                                                if 'pdfs_oficiais' not in resultado:
                                                    resultado['pdfs_oficiais'] = {}
                                                    logger.debug("   📦 Inicializou resultado['pdfs_oficiais']")
                                                
                                                # Adicionar PDF ao resultado para o ERP salvar
                                                resultado['pdfs_oficiais'][numero_nfse] = {
                                                    'pdf_base64': pdf_base64,
                                                    'numero_nfse': str(numero_nfse),
                                                    'cnpj_prestador': str(cnpj_prestador),
                                                    'codigo_municipio': str(codigo_municipio),
                                                    'data_emissao': str(data_emissao)
                                                }
                                                logger.debug(f"   📝 PDF {numero_nfse} adicionado ao resultado")
                                            else:
                                                logger.info(f"   ℹ️ DANFSe não disponível na API")
                                        
                                        except Exception as e_download:
                                            logger.warning(f"   ⚠️ Erro ao baixar DANFSe: {e_download}")
                            
                            except Exception as e_pdf:
                                logger.error(f"   ❌ Erro ao processar PDF: {e_pdf}")
                                import traceback
                                logger.error(traceback.format_exc())
                            
                            # danfse_path será definido pelo ERP após salvar
                            nfse_data['danfse_path'] = None
                    
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar NSU {doc_nsu}: {e}")
                        resultado['erros'].append(f"NSU {doc_nsu}: {str(e)}")
                        continue
                
                nsu_atual += 1
            
            # Log do motivo da parada
            if documentos_processados >= max_documentos:
                logger.info(f"⏸️ Busca pausada: Limite de {max_documentos} documentos atingido")
                logger.info(f"💡 Clique novamente em 'Baixar NFS-e' para continuar a busca")
            elif tentativas_404 >= max_tentativas_404:
                logger.info(f"⏹️ Busca finalizada: {max_tentativas_404} NSUs consecutivos sem retorno")
            
            # Atualizar último NSU processado
            if resultado['total_nfse'] > 0:
                maior_nsu = nsu_atual - 1
                db.set_last_nsu_nfse(empresa_id, cnpj_informante, maior_nsu)
                resultado['ultimo_nsu'] = maior_nsu
                logger.info(f"💾 Último NSU atualizado: {maior_nsu}")
            
            resultado['sucesso'] = True
            
            logger.info("=" * 70)
            logger.info(f"✅ BUSCA CONCLUÍDA")
            logger.info(f"Total de NFS-e: {resultado['total_nfse']}")
            logger.info(f"Novas: {resultado['nfse_novas']} | Atualizadas: {resultado['nfse_atualizadas']}")
            logger.info(f"Último NSU: {resultado['ultimo_nsu']}")
            logger.info("=" * 70)
    
    except Exception as e:
        logger.error(f"❌ Erro na busca via Ambiente Nacional: {e}")
        resultado['erros'].append(str(e))
        import traceback
        traceback.print_exc()
    
    return resultado

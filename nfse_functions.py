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

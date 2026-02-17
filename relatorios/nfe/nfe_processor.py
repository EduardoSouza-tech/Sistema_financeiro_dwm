"""
Módulo de processamento de XMLs de NF-e

Este módulo é responsável por:
- Detectar o tipo/schema do XML (procNFe, resNFe, evento)
- Extrair dados completos de NF-e
- Validar chave de acesso
- Determinar direção (ENTRADA/SAIDA)
- Parse estruturado de XMLs fiscais

Autor: Sistema Financeiro DWM
Data: Janeiro 2026
"""

from lxml import etree
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import re


# ============================================================================
# NAMESPACES NFe
# ============================================================================

NAMESPACES = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
    'cte': 'http://www.portalfiscal.inf.br/cte',
}


# ============================================================================
# VALIDAÇÃO DE CHAVE DE ACESSO
# ============================================================================

def validar_chave_nfe(chave: str) -> Tuple[bool, str]:
    """
    Valida chave de acesso de NF-e (44 dígitos).
    
    Estrutura da chave (44 dígitos):
    - Posições 0-1: cUF (código UF)
    - Posições 2-7: AAMM (ano e mês de emissão)
    - Posições 8-21: CNPJ do emitente
    - Posições 22-23: mod (modelo do documento - 55 para NFe)
    - Posições 24-26: série
    - Posições 27-35: nNF (número da nota)
    - Posições 36-36: tpEmis (forma de emissão)
    - Posições 37-42: cNF (código numérico)
    - Posições 43-43: cDV (dígito verificador)
    
    Args:
        chave: Chave de acesso (string de 44 dígitos)
        
    Returns:
        Tuple (válido: bool, mensagem: str)
    """
    # Verifica formato básico
    if not chave or not isinstance(chave, str):
        return False, "Chave inválida: valor vazio ou não é string"
    
    chave = chave.strip()
    
    if len(chave) != 44:
        return False, f"Chave inválida: deve ter 44 dígitos, tem {len(chave)}"
    
    if not chave.isdigit():
        return False, "Chave inválida: deve conter apenas dígitos"
    
    # Calcula dígito verificador
    chave_sem_dv = chave[:43]
    dv_informado = int(chave[43])
    
    # Cálculo do DV usando módulo 11
    soma = 0
    multiplicador = 2
    
    for i in range(42, -1, -1):  # Da direita para esquerda
        soma += int(chave_sem_dv[i]) * multiplicador
        multiplicador += 1
        if multiplicador > 9:
            multiplicador = 2
    
    resto = soma % 11
    dv_calculado = 0 if resto in (0, 1) else 11 - resto
    
    if dv_calculado != dv_informado:
        return False, f"Chave inválida: DV incorreto (esperado {dv_calculado}, informado {dv_informado})"
    
    # Valida código UF (posições 0-1)
    cuf = int(chave[:2])
    ufs_validas = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 
                   29, 31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53]
    if cuf not in ufs_validas:
        return False, f"Chave inválida: código UF {cuf} não existe"
    
    # Valida ano/mês (posições 2-5)
    try:
        ano = int(chave[2:4])
        mes = int(chave[4:6])
        if mes < 1 or mes > 12:
            return False, f"Chave inválida: mês {mes} inválido"
        if ano < 6 or ano > 99:
            return False, f"Chave inválida: ano {ano} inválido"
    except ValueError:
        return False, "Chave inválida: formato de data incorreto"
    
    # Valida modelo (posições 20-21, deve ser 55 para NFe ou 65 para NFCe)
    modelo = chave[20:22]
    if modelo not in ['55', '65']:
        return False, f"Chave inválida: modelo {modelo} não é NFe (55) ou NFCe (65)"
    
    return True, "Chave válida"


# ============================================================================
# DETECÇÃO DE SCHEMA/TIPO DE XML
# ============================================================================

def detectar_schema_nfe(xml_content: str) -> Dict[str, any]:
    """
    Detecta o tipo/schema do XML de NF-e.
    
    Tipos possíveis:
    - procNFe: NF-e completa processada (com protocolo de autorização)
    - resNFe: Resumo de NF-e (retornado pela Distribuição DFe)
    - evento: Evento de NF-e (cancelamento, carta de correção, etc)
    - resEvento: Resumo de evento
    - procEventoNFe: Evento processado
    
    Args:
        xml_content: Conteúdo XML como string
        
    Returns:
        Dict com tipo, schema, namespace e root element
    """
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        # Verifica tag raiz
        tag_raiz = etree.QName(root.tag).localname
        namespace = etree.QName(root.tag).namespace
        
        # Identifica o tipo
        tipo = None
        categoria = None
        
        if tag_raiz == 'nfeProc':
            tipo = 'procNFe'
            categoria = 'NFe'
        elif tag_raiz == 'resNFe':
            tipo = 'resNFe'
            categoria = 'NFe'
        elif tag_raiz == 'procEventoNFe':
            tipo = 'procEvento'
            categoria = 'Evento'
        elif tag_raiz == 'evento':
            tipo = 'evento'
            categoria = 'Evento'
        elif tag_raiz == 'resEvento':
            tipo = 'resEvento'
            categoria = 'Evento'
        elif 'NFe' in tag_raiz:
            tipo = 'NFe'
            categoria = 'NFe'
        else:
            tipo = 'desconhecido'
            categoria = 'desconhecido'
        
        return {
            'sucesso': True,
            'tipo': tipo,
            'categoria': categoria,
            'tag_raiz': tag_raiz,
            'namespace': namespace,
            'versao': root.get('versao', 'N/A')
        }
        
    except etree.XMLSyntaxError as e:
        return {
            'sucesso': False,
            'erro': f'Erro de parser XML: {str(e)}',
            'tipo': None,
            'categoria': None
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao detectar schema: {str(e)}',
            'tipo': None,
            'categoria': None
        }


# ============================================================================
# EXTRAÇÃO DE DADOS - procNFe (XML COMPLETO)
# ============================================================================

def extrair_dados_nfe(xml_content: str, cnpj_empresa: str) -> Dict[str, any]:
    """
    Extrai dados completos de uma NF-e processada (procNFe).
    
    Args:
        xml_content: Conteúdo XML da NF-e
        cnpj_empresa: CNPJ da empresa para determinar direção
        
    Returns:
        Dict com todos os dados extraídos
    """
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        # Detecta schema primeiro
        schema_info = detectar_schema_nfe(xml_content)
        if not schema_info['sucesso']:
            return {'sucesso': False, 'erro': schema_info['erro']}
        
        tipo_xml = schema_info['tipo']
        
        # Roteamento para função específica
        if tipo_xml == 'procNFe':
            return _extrair_procnfe(root, cnpj_empresa)
        elif tipo_xml == 'resNFe':
            return _extrair_resnfe(root, cnpj_empresa)
        elif tipo_xml in ['procEvento', 'evento', 'resEvento']:
            return _extrair_evento(root, cnpj_empresa)
        else:
            return {
                'sucesso': False,
                'erro': f'Tipo de XML não suportado: {tipo_xml}'
            }
            
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao extrair dados: {str(e)}'
        }


def _extrair_procnfe(root: etree._Element, cnpj_empresa: str) -> Dict[str, any]:
    """Extrai dados de procNFe (NF-e completa com protocolo)"""
    try:
        # Namespace
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Localiza elementos principais
        nfe = root.find('.//nfe:NFe', ns)
        infnfe = nfe.find('.//nfe:infNFe', ns) if nfe is not None else None
        
        if infnfe is None:
            return {'sucesso': False, 'erro': 'Elemento infNFe não encontrado'}
        
        # Identificação
        ide = infnfe.find('nfe:ide', ns)
        
        # Emitente
        emit = infnfe.find('nfe:emit', ns)
        emit_cnpj = emit.find('nfe:CNPJ', ns).text if emit is not None and emit.find('nfe:CNPJ', ns) is not None else None
        emit_nome = emit.find('nfe:xNome', ns).text if emit is not None and emit.find('nfe:xNome', ns) is not None else None
        emit_uf = emit.find('.//nfe:UF', ns).text if emit is not None and emit.find('.//nfe:UF', ns) is not None else None
        
        # Destinatário
        dest = infnfe.find('nfe:dest', ns)
        dest_cnpj = None
        if dest is not None:
            dest_cnpj = dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else None
            if not dest_cnpj:
                dest_cnpj = dest.find('nfe:CPF', ns).text if dest.find('nfe:CPF', ns) is not None else None
        dest_nome = dest.find('nfe:xNome', ns).text if dest is not None and dest.find('nfe:xNome', ns) is not None else None
        dest_uf = dest.find('.//nfe:UF', ns).text if dest is not None and dest.find('.//nfe:UF', ns) is not None else None
        
        # Totais
        total = infnfe.find('.//nfe:total/nfe:ICMSTot', ns)
        
        # ICMS
        valor_total = float(total.find('nfe:vNF', ns).text) if total is not None and total.find('nfe:vNF', ns) is not None else 0.0
        base_icms = float(total.find('nfe:vBC', ns).text) if total is not None and total.find('nfe:vBC', ns) is not None else 0.0
        valor_icms = float(total.find('nfe:vICMS', ns).text) if total is not None and total.find('nfe:vICMS', ns) is not None else 0.0
        
        # PIS/COFINS
        valor_pis = float(total.find('nfe:vPIS', ns).text) if total is not None and total.find('nfe:vPIS', ns) is not None else 0.0
        valor_cofins = float(total.find('nfe:vCOFINS', ns).text) if total is not None and total.find('nfe:vCOFINS', ns) is not None else 0.0
        
        # Produtos
        valor_produtos = float(total.find('nfe:vProd', ns).text) if total is not None and total.find('nfe:vProd', ns) is not None else 0.0
        valor_frete = float(total.find('nfe:vFrete', ns).text) if total is not None and total.find('nfe:vFrete', ns) is not None else 0.0
        valor_desconto = float(total.find('nfe:vDesc', ns).text) if total is not None and total.find('nfe:vDesc', ns) is not None else 0.0
        
        # Protocolo
        prot_inf = root.find('.//nfe:protNFe/nfe:infProt', ns)
        numero_protocolo = prot_inf.find('nfe:nProt', ns).text if prot_inf is not None and prot_inf.find('nfe:nProt', ns) is not None else None
        
        # Data de autorização
        data_autorizacao = None
        if prot_inf is not None and prot_inf.find('nfe:dhRecbto', ns) is not None:
            try:
                data_autorizacao = datetime.fromisoformat(prot_inf.find('nfe:dhRecbto', ns).text.replace('Z', '+00:00'))
            except:
                pass
        
        # Chave de acesso
        chave = infnfe.get('Id', '').replace('NFe', '')
        
        # Validar chave
        valido, msg_validacao = validar_chave_nfe(chave)
        if not valido:
            return {'sucesso': False, 'erro': msg_validacao}
        
        # Identificação da nota
        numero = ide.find('nfe:nNF', ns).text if ide is not None and ide.find('nfe:nNF', ns) is not None else None
        serie = ide.find('nfe:serie', ns).text if ide is not None and ide.find('nfe:serie', ns) is not None else None
        modelo = ide.find('nfe:mod', ns).text if ide is not None and ide.find('nfe:mod', ns) is not None else '55'
        natureza = ide.find('nfe:natOp', ns).text if ide is not None and ide.find('nfe:natOp', ns) is not None else None
        
        # CFOP (pega do primeiro item)
        cfop = None
        det = infnfe.find('.//nfe:det/nfe:prod/nfe:CFOP', ns)
        if det is not None:
            cfop = det.text
        
        # Datas
        data_emissao = None
        if ide is not None and ide.find('nfe:dhEmi', ns) is not None:
            try:
                data_emissao = datetime.fromisoformat(ide.find('nfe:dhEmi', ns).text.replace('Z', '+00:00'))
            except:
                pass
        
        data_entrada_saida = None
        if ide is not None and ide.find('nfe:dhSaiEnt', ns) is not None:
            try:
                data_entrada_saida = datetime.fromisoformat(ide.find('nfe:dhSaiEnt', ns).text.replace('Z', '+00:00'))
            except:
                pass
        
        # Determinar direção (ENTRADA ou SAIDA)
        direcao = determinar_direcao_nfe(emit_cnpj, dest_cnpj, cnpj_empresa)
        
        # Monta resultado
        resultado = {
            'sucesso': True,
            'tipo_xml': 'procNFe',
            'chave': chave,
            'chave_valida': valido,
            'numero': numero,
            'serie': serie,
            'modelo': modelo,
            'tipo_documento': 'NFe',
            'natureza_operacao': natureza,
            'cfop': cfop,
            
            # Emitente
            'cnpj_emitente': emit_cnpj,
            'nome_emitente': emit_nome,
            'uf_emitente': emit_uf,
            
            # Destinatário
            'cnpj_destinatario': dest_cnpj,
            'nome_destinatario': dest_nome,
            'uf_destinatario': dest_uf,
            
            # Valores
            'valor_total': valor_total,
            'valor_produtos': valor_produtos,
            'valor_frete': valor_frete,
            'valor_desconto': valor_desconto,
            'base_calculo_icms': base_icms,
            'valor_icms': valor_icms,
            'valor_pis': valor_pis,
            'valor_cofins': valor_cofins,
            
            # Datas
            'data_emissao': data_emissao,
            'data_entrada_saida': data_entrada_saida,
            'data_autorizacao': data_autorizacao,
            
            # Protocolo
            'numero_protocolo': numero_protocolo,
            'situacao': 'Autorizada',
            
            # Direção
            'direcao': direcao,
        }
        
        return resultado
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao extrair procNFe: {str(e)}'
        }


def _extrair_resnfe(root: etree._Element, cnpj_empresa: str) -> Dict[str, any]:
    """Extrai dados de resNFe (resumo da Distribuição DFe)"""
    try:
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # No resNFe, os dados estão diretamente na raiz
        chave = root.find('nfe:chNFe', ns).text if root.find('nfe:chNFe', ns) is not None else None
        
        if not chave:
            return {'sucesso': False, 'erro': 'Chave não encontrada no resNFe'}
        
        # Validar chave
        valido, msg_validacao = validar_chave_nfe(chave)
        if not valido:
            return {'sucesso': False, 'erro': msg_validacao}
        
        # Dados limitados do resumo
        cnpj_emitente = root.find('nfe:CNPJ', ns).text if root.find('nfe:CNPJ', ns) is not None else None
        nome_emitente = root.find('nfe:xNome', ns).text if root.find('nfe:xNome', ns) is not None else None
        
        valor_total = None
        if root.find('nfe:vNF', ns) is not None:
            valor_total = float(root.find('nfe:vNF', ns).text)
        
        # Data
        data_emissao = None
        if root.find('nfe:dhEmi', ns) is not None:
            try:
                data_emissao = datetime.fromisoformat(root.find('nfe:dhEmi', ns).text.replace('Z', '+00:00'))
            except:
                pass
        
        # Situação
        situacao_elem = root.find('nfe:cSitNFe', ns)
        situacao = 'Autorizada' if situacao_elem is not None and situacao_elem.text == '1' else 'Cancelada'
        
        # Protocolo
        numero_protocolo = root.find('nfe:nProt', ns).text if root.find('nfe:nProt', ns) is not None else None
        
        # Direção (só temos emitente no resumo)
        direcao = 'ENTRADA' if cnpj_emitente != cnpj_empresa else 'SAIDA'
        
        resultado = {
            'sucesso': True,
            'tipo_xml': 'resNFe',
            'chave': chave,
            'chave_valida': valido,
            'tipo_documento': 'NFe',
            
            # Emitente (dados limitados)
            'cnpj_emitente': cnpj_emitente,
            'nome_emitente': nome_emitente,
            
            # Destinatário (não disponível no resumo)
            'cnpj_destinatario': None,
            'nome_destinatario': None,
            
            # Valores (limitados)
            'valor_total': valor_total,
            
            # Data
            'data_emissao': data_emissao,
            
            # Protocolo
            'numero_protocolo': numero_protocolo,
            'situacao': situacao,
            
            # Direção
            'direcao': direcao,
            
            # Aviso
            'aviso': 'Dados limitados - XML é um resumo (resNFe)',
        }
        
        return resultado
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao extrair resNFe: {str(e)}'
        }


def _extrair_evento(root: etree._Element, cnpj_empresa: str) -> Dict[str, any]:
    """Extrai dados de evento de NF-e"""
    try:
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Busca info do evento
        inf_evento = root.find('.//nfe:infEvento', ns)
        
        if inf_evento is None:
            return {'sucesso': False, 'erro': 'Elemento infEvento não encontrado'}
        
        chave = inf_evento.find('nfe:chNFe', ns).text if inf_evento.find('nfe:chNFe', ns) is not None else None
        
        if not chave:
            return {'sucesso': False, 'erro': 'Chave não encontrada no evento'}
        
        # Tipo de evento
        tipo_evento = inf_evento.find('nfe:tpEvento', ns).text if inf_evento.find('nfe:tpEvento', ns) is not None else None
        desc_evento = inf_evento.find('nfe:xEvento', ns).text if inf_evento.find('nfe:xEvento', ns) is not None else None
        
        # Mapear tipo de evento
        eventos_conhecidos = {
            '110110': 'Carta de Correção',
            '110111': 'Cancelamento',
            '110140': 'Confirmação da Operação',
            '110150': 'Desconhecimento da Operação',
            '110151': 'Operação não Realizada',
        }
        
        nome_evento = eventos_conhecidos.get(tipo_evento, desc_evento or 'Evento Desconhecido')
        
        # Protocolo
        numero_protocolo = inf_evento.find('nfe:nProt', ns).text if inf_evento.find('nfe:nProt', ns) is not None else None
        
        # Data
        data_evento = None
        if inf_evento.find('nfe:dhEvento', ns) is not None:
            try:
                data_evento = datetime.fromisoformat(inf_evento.find('nfe:dhEvento', ns).text.replace('Z', '+00:00'))
            except:
                pass
        
        resultado = {
            'sucesso': True,
            'tipo_xml': 'evento',
            'chave': chave,
            'tipo_documento': 'Evento',
            'tipo_evento': tipo_evento,
            'nome_evento': nome_evento,
            'descricao_evento': desc_evento,
            'numero_protocolo': numero_protocolo,
            'data_evento': data_evento,
        }
        
        return resultado
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao extrair evento: {str(e)}'
        }


# ============================================================================
# DETERMINAR DIREÇÃO (ENTRADA/SAIDA)
# ============================================================================

def determinar_direcao_nfe(cnpj_emitente: str, cnpj_destinatario: str, cnpj_empresa: str) -> str:
    """
    Determina se a NF-e é de ENTRADA ou SAIDA.
    
    Regra:
    - Se CNPJ da empresa = CNPJ do emitente → SAIDA
    - Se CNPJ da empresa = CNPJ do destinatário → ENTRADA
    - Caso contrário → TERCEIROS (nota que não é da empresa)
    
    Args:
        cnpj_emitente: CNPJ do emitente da nota
        cnpj_destinatario: CNPJ do destinatário da nota
        cnpj_empresa: CNPJ da empresa do sistema
        
    Returns:
        'SAIDA', 'ENTRADA' ou 'TERCEIROS'
    """
    # Limpa CNPJs (remove pontuação)
    def limpar_cnpj(cnpj):
        if not cnpj:
            return ''
        return re.sub(r'[^\d]', '', cnpj)
    
    cnpj_emit = limpar_cnpj(cnpj_emitente)
    cnpj_dest = limpar_cnpj(cnpj_destinatario)
    cnpj_emp = limpar_cnpj(cnpj_empresa)
    
    if cnpj_emit == cnpj_emp:
        return 'SAIDA'
    elif cnpj_dest == cnpj_emp:
        return 'ENTRADA'
    else:
        return 'TERCEIROS'


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def extrair_resumo_nfe(xml_content: str) -> Dict[str, any]:
    """
    Extrai apenas resumo básico da NF-e (para listagens).
    
    Args:
        xml_content: Conteúdo XML
        
    Returns:
        Dict com apenas chave, número, valor, emitente, data
    """
    try:
        schema_info = detectar_schema_nfe(xml_content)
        
        if not schema_info['sucesso']:
            return {'sucesso': False, 'erro': schema_info['erro']}
        
        root = etree.fromstring(xml_content.encode('utf-8'))
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Busca elementos básicos
        if schema_info['tipo'] == 'procNFe':
            infnfe = root.find('.//nfe:infNFe', ns)
            chave = infnfe.get('Id', '').replace('NFe', '') if infnfe is not None else None
            
            ide = root.find('.//nfe:ide', ns)
            numero = ide.find('nfe:nNF', ns).text if ide is not None and ide.find('nfe:nNF', ns) is not None else None
            
            total = root.find('.//nfe:ICMSTot/nfe:vNF', ns)
            valor = float(total.text) if total is not None else 0.0
            
            emit = root.find('.//nfe:emit', ns)
            emitente = emit.find('nfe:xNome', ns).text if emit is not None and emit.find('nfe:xNome', ns) is not None else None
            
            data_elem = ide.find('nfe:dhEmi', ns) if ide is not None else None
            data = datetime.fromisoformat(data_elem.text.replace('Z', '+00:00')) if data_elem is not None else None
            
        elif schema_info['tipo'] == 'resNFe':
            chave = root.find('nfe:chNFe', ns).text if root.find('nfe:chNFe', ns) is not None else None
            numero = chave[25:34] if chave and len(chave) == 44 else None  # Extrai do chave
            
            valor_elem = root.find('nfe:vNF', ns)
            valor = float(valor_elem.text) if valor_elem is not None else 0.0
            
            emitente = root.find('nfe:xNome', ns).text if root.find('nfe:xNome', ns) is not None else None
            
            data_elem = root.find('nfe:dhEmi', ns)
            data = datetime.fromisoformat(data_elem.text.replace('Z', '+00:00')) if data_elem is not None else None
        
        else:
            return {'sucesso': False, 'erro': 'Tipo de XML não suportado para resumo'}
        
        return {
            'sucesso': True,
            'chave': chave,
            'numero': numero,
            'valor': valor,
            'emitente': emitente,
            'data_emissao': data,
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao extrair resumo: {str(e)}'
        }


# ============================================================================
# TESTE
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("TESTE: Módulo NF-e Processor")
    print("=" * 70)
    
    # Função auxiliar para calcular DV correto
    def calcular_dv_chave(chave_sem_dv: str) -> str:
        """Calcula o dígito verificador de uma chave de 43 dígitos"""
        soma = 0
        multiplicador = 2
        
        for i in range(42, -1, -1):
            soma += int(chave_sem_dv[i]) * multiplicador
            multiplicador += 1
            if multiplicador > 9:
                multiplicador = 2
        
        resto = soma % 11
        dv = 0 if resto in (0, 1) else 11 - resto
        return str(dv)
    
    # Teste 1: Validação de chave com DV correto
    print("\n1. Teste de validação de chave:")
    # Chave: 35(cUF) + 2601(AAMM) + 12345678000190(CNPJ) + 55(mod) + 001(serie) + 000000100(nNF) + 1(tpEmis) + 12345678(cNF)
    chave_sem_dv = "3526011234567800019055001000000100112345678"
    dv_correto = calcular_dv_chave(chave_sem_dv)
    chave_teste = chave_sem_dv + dv_correto
    
    valida, msg = validar_chave_nfe(chave_teste)
    print(f"   Chave: {chave_teste}")
    print(f"   DV calculado: {dv_correto}")
    print(f"   Válida: {valida}")
    print(f"   Mensagem: {msg}")
    
    # Teste 2: Chave inválida (DV errado)
    print("\n2. Teste com chave inválida (DV errado):")
    chave_invalida = chave_sem_dv + "9"  # DV errado propositalmente
    valida, msg = validar_chave_nfe(chave_invalida)
    print(f"   Chave: {chave_invalida}")
    print(f"   Válida: {valida}")
    print(f"   Mensagem: {msg}")
    
    # Teste 3: Detecção de schema
    print("\n3. Teste de detecção de schema:")
    xml_procnfe = f'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe{chave_teste}" versao="4.00">
            <ide>
                <cUF>35</cUF>
                <nNF>100</nNF>
                <serie>1</serie>
                <dhEmi>2026-01-15T10:30:00-03:00</dhEmi>
            </ide>
        </infNFe>
    </NFe>
</nfeProc>'''
    
    schema_info = detectar_schema_nfe(xml_procnfe)
    print(f"   Tipo: {schema_info['tipo']}")
    print(f"   Categoria: {schema_info['categoria']}")
    print(f"   Tag Raiz: {schema_info['tag_raiz']}")
    
    # Teste 4: Determinar direção
    print("\n4. Teste de determinação de direção:")
    cnpj_empresa = "12345678000190"
    cnpj_emit = "12345678000190"
    cnpj_dest = "98765432000195"
    
    direcao = determinar_direcao_nfe(cnpj_emit, cnpj_dest, cnpj_empresa)
    print(f"   Empresa: {cnpj_empresa}")
    print(f"   Emitente: {cnpj_emit}")
    print(f"   Destinatário: {cnpj_dest}")
    print(f"   Direção: {direcao}")
    
    direcao2 = determinar_direcao_nfe(cnpj_dest, cnpj_empresa, cnpj_empresa)
    print(f"\n   Emitente: {cnpj_dest}")
    print(f"   Destinatário: {cnpj_empresa}")
    print(f"   Direção: {direcao2}")
    
    print("\n" + "=" * 70)
    print("✓ Testes concluídos!")
    print("=" * 70)

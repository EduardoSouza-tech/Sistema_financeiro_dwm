# -*- coding: utf-8 -*-
"""
Funções de Importação de NF-e e NFS-e
Suporta importação de XML de notas fiscais eletrônicas

Layouts suportados:
- NF-e versão 4.0 (Layout nacional)
- NFS-e (diversos layouts municipais - simplificado)
- NFC-e (Nota Fiscal de Consumidor Eletrônica)
- CT-e (Conhecimento de Transporte Eletrônico - básico)
"""

import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import datetime
import re
import hashlib
from database_postgresql import get_connection, executar_query
from logger_config import logger


# ===== NAMESPACE NF-e =====
NAMESPACES = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
}


# ===== FUNÇÕES AUXILIARES =====

def extrair_texto(element, caminho, namespace='nfe', default=''):
    """
    Extrai texto de um elemento XML
    
    Args:
        element: Elemento XML pai
        caminho: Caminho XPath do elemento
        namespace: Namespace do XML (default: 'nfe')
        default: Valor padrão se não encontrado
        
    Returns:
        Texto extraído ou valor padrão
    """
    try:
        if namespace and namespace in NAMESPACES:
            # Adicionar namespace ao caminho
            partes = caminho.split('/')
            caminho_ns = '/'.join([f'{namespace}:{p}' if p else p for p in partes])
            elem = element.find(caminho_ns, NAMESPACES)
        else:
            elem = element.find(caminho)
            
        if elem is not None and elem.text:
            return elem.text.strip()
        return default
    except Exception as e:
        logger.warning(f"Erro ao extrair {caminho}: {e}")
        return default


def extrair_decimal(element, caminho, namespace='nfe', default=0):
    """
    Extrai valor decimal de um elemento XML
    
    Returns:
        Decimal ou valor padrão
    """
    texto = extrair_texto(element, caminho, namespace, str(default))
    try:
        return Decimal(texto.replace(',', '.'))
    except:
        return Decimal(default)


def extrair_data(element, caminho, namespace='nfe', formato='%Y-%m-%d'):
    """
    Extrai data de um elemento XML
    
    Args:
        element: Elemento XML pai
        caminho: Caminho do elemento
        namespace: Namespace
        formato: Formato da data (default: ISO)
        
    Returns:
        datetime.date ou None
    """
    texto = extrair_texto(element, caminho, namespace)
    if not texto:
        return None
        
    try:
        # Tentar formato ISO com timezone (2025-01-15T10:30:00-03:00)
        if 'T' in texto:
            texto = texto.split('T')[0]
        
        # Tentar formatos comuns
        for fmt in [formato, '%Y-%m-%d', '%d/%m/%Y', '%d%m%Y']:
            try:
                return datetime.strptime(texto, fmt).date()
            except:
                continue
                
        logger.warning(f"Formato de data não reconhecido: {texto}")
        return None
    except Exception as e:
        logger.warning(f"Erro ao extrair data {caminho}: {e}")
        return None


def validar_chave_acesso(chave):
    """
    Valida formato da chave de acesso (44 dígitos)
    
    Returns:
        bool: True se válida
    """
    if not chave or len(chave) != 44:
        return False
    return chave.isdigit()


def calcular_hash_xml(xml_content):
    """
    Calcula hash MD5 do conteúdo XML
    """
    return hashlib.md5(xml_content.encode('utf-8')).hexdigest()


def formatar_cnpj_cpf(documento):
    """
    Formata CNPJ/CPF com pontuação
    """
    if not documento:
        return ''
    
    documento = re.sub(r'\D', '', documento)
    
    if len(documento) == 11:  # CPF
        return f"{documento[:3]}.{documento[3:6]}.{documento[6:9]}-{documento[9:]}"
    elif len(documento) == 14:  # CNPJ
        return f"{documento[:2]}.{documento[2:5]}.{documento[5:8]}/{documento[8:12]}-{documento[12:]}"
    
    return documento


# ===== IMPORTAÇÃO NF-e (versão 4.0) =====

def importar_xml_nfe(empresa_id, xml_content, usuario_id=None):
    """
    Importa XML de NF-e (versão 4.0)
    
    Args:
        empresa_id: ID da empresa
        xml_content: Conteúdo XML completo
        usuario_id: ID do usuário que importou
        
    Returns:
        dict com resultado da importação
    """
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Identificar tipo de nota (NF-e, NFC-e)
        nfe = root.find('.//nfe:NFe', NAMESPACES)
        if nfe is None:
            nfe = root.find('.//NFe')  # Sem namespace
            
        if nfe is None:
            return {
                'success': False,
                'error': 'XML inválido - elemento NFe não encontrado'
            }
        
        # Elemento infNFe
        inf_nfe = nfe.find('.//nfe:infNFe', NAMESPACES)
        if inf_nfe is None:
            inf_nfe = nfe.find('.//infNFe')
            
        if inf_nfe is None:
            return {
                'success': False,
                'error': 'XML inválido - elemento infNFe não encontrado'
            }
        
        # Extrair chave de acesso
        chave_acesso = inf_nfe.get('Id', '').replace('NFe', '')
        
        if not validar_chave_acesso(chave_acesso):
            return {
                'success': False,
                'error': f'Chave de acesso inválida: {chave_acesso}'
            }
        
        # Verificar se já foi importada
        nota_existente = executar_query(
            """
            SELECT id FROM notas_fiscais 
            WHERE empresa_id = %s AND chave_acesso = %s
            """,
            (empresa_id, chave_acesso)
        )
        
        if nota_existente:
            return {
                'success': False,
                'error': f'Nota fiscal já importada (ID: {nota_existente[0]["id"]})',
                'nota_id': nota_existente[0]['id']
            }
        
        # ===== EXTRAIR DADOS DA NOTA =====
        
        # Identificação
        ide = inf_nfe.find('.//nfe:ide', NAMESPACES) or inf_nfe.find('.//ide')
        numero = extrair_texto(ide, 'nNF')
        serie = extrair_texto(ide, 'serie', default='1')
        modelo = extrair_texto(ide, 'mod', default='55')  # 55=NF-e, 65=NFC-e
        data_emissao = extrair_data(ide, 'dhEmi')
        data_entrada_saida = extrair_data(ide, 'dhSaiEnt')
        tipo_operacao = extrair_texto(ide, 'tpNF')  # 0=Entrada, 1=Saída
        cfop_principal = extrair_texto(ide, 'CFOP')
        natureza_operacao = extrair_texto(ide, 'natOp')
        
        # Emitente
        emit = inf_nfe.find('.//nfe:emit', NAMESPACES) or inf_nfe.find('.//emit')
        emit_cnpj = extrair_texto(emit, 'CNPJ')
        emit_nome = extrair_texto(emit, 'xNome')
        
        # Destinatário
        dest = inf_nfe.find('.//nfe:dest', NAMESPACES) or inf_nfe.find('.//dest')
        dest_cnpj = extrair_texto(dest, 'CNPJ') or extrair_texto(dest, 'CPF')
        dest_nome = extrair_texto(dest, 'xNome')
        dest_ie = extrair_texto(dest, 'IE')
        dest_endereco = dest.find('.//nfe:enderDest', NAMESPACES) or dest.find('.//enderDest')
        dest_uf = extrair_texto(dest_endereco, 'UF') if dest_endereco is not None else ''
        dest_municipio = extrair_texto(dest_endereco, 'xMun') if dest_endereco is not None else ''
        
        # Totais
        total = inf_nfe.find('.//nfe:total', NAMESPACES) or inf_nfe.find('.//total')
        icms_total = total.find('.//nfe:ICMSTot', NAMESPACES) or total.find('.//ICMSTot')
        
        valor_nota = extrair_decimal(icms_total, 'vNF')
        valor_produtos = extrair_decimal(icms_total, 'vProd')
        valor_desconto = extrair_decimal(icms_total, 'vDesc')
        valor_frete = extrair_decimal(icms_total, 'vFrete')
        valor_seguro = extrair_decimal(icms_total, 'vSeg')
        valor_outras = extrair_decimal(icms_total, 'vOutro')
        
        bc_icms = extrair_decimal(icms_total, 'vBC')
        v_icms = extrair_decimal(icms_total, 'vICMS')
        bc_icms_st = extrair_decimal(icms_total, 'vBCST')
        v_icms_st = extrair_decimal(icms_total, 'vST')
        v_ipi = extrair_decimal(icms_total, 'vIPI')
        v_pis = extrair_decimal(icms_total, 'vPIS')
        v_cofins = extrair_decimal(icms_total, 'vCOFINS')
        
        # Determinar direção (ENTRADA ou SAÍDA)
        # Se somos o destinatário, é entrada; se somos o emitente, é saída
        direcao = 'ENTRADA' if tipo_operacao == '0' else 'SAIDA'
        
        # Participante (fornecedor ou cliente)
        if direcao == 'ENTRADA':
            participante_cnpj = emit_cnpj
            participante_nome = emit_nome
            participante_tipo = 'FORNECEDOR'
        else:
            participante_cnpj = dest_cnpj
            participante_nome = dest_nome
            participante_tipo = 'CLIENTE'
        
        # Informações complementares
        inf_adic = inf_nfe.find('.//nfe:infAdic', NAMESPACES) or inf_nfe.find('.//infAdic')
        info_complementar = extrair_texto(inf_adic, 'infCpl') if inf_adic is not None else ''
        
        # ===== INSERIR NOTA NO BANCO =====
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Inserir nota fiscal
            cursor.execute("""
                INSERT INTO notas_fiscais (
                    empresa_id, tipo, numero, serie, modelo, chave_acesso,
                    data_emissao, data_entrada_saida, direcao, natureza_operacao, cfop,
                    participante_tipo, participante_cnpj_cpf, participante_nome,
                    participante_ie, participante_uf, participante_municipio,
                    valor_total, valor_produtos, valor_desconto, valor_frete,
                    valor_seguro, valor_outras_despesas,
                    base_calculo_icms, valor_icms, base_calculo_icms_st, valor_icms_st,
                    valor_ipi, base_calculo_pis, valor_pis, base_calculo_cofins, valor_cofins,
                    informacoes_complementares, xml_completo, xml_importado, data_importacao
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                RETURNING id
            """, (
                empresa_id, 'NFE', numero, serie, modelo, chave_acesso,
                data_emissao, data_entrada_saida, direcao, natureza_operacao, cfop_principal,
                participante_tipo, formatar_cnpj_cpf(participante_cnpj), participante_nome,
                dest_ie, dest_uf, dest_municipio,
                valor_nota, valor_produtos, valor_desconto, valor_frete,
                valor_seguro, valor_outras,
                bc_icms, v_icms, bc_icms_st, v_icms_st,
                v_ipi, bc_icms, v_pis, bc_icms, v_cofins,
                info_complementar, xml_content, True, datetime.now()
            ))
            
            nota_id = cursor.fetchone()[0]
            
            # ===== EXTRAIR E INSERIR ITENS =====
            
            det_list = inf_nfe.findall('.//nfe:det', NAMESPACES)
            if not det_list:
                det_list = inf_nfe.findall('.//det')
            
            itens_importados = 0
            
            for det in det_list:
                numero_item = int(det.get('nItem', 0))
                
                # Produto
                prod = det.find('.//nfe:prod', NAMESPACES) or det.find('.//prod')
                
                codigo_produto = extrair_texto(prod, 'cProd')
                codigo_ean = extrair_texto(prod, 'cEAN')
                codigo_ncm = extrair_texto(prod, 'NCM')
                descricao = extrair_texto(prod, 'xProd')
                cfop_item = extrair_texto(prod, 'CFOP')
                quantidade = extrair_decimal(prod, 'qCom', default=1)
                unidade = extrair_texto(prod, 'uCom', default='UN')
                valor_unitario = extrair_decimal(prod, 'vUnCom')
                valor_total_item = extrair_decimal(prod, 'vProd')
                valor_desc_item = extrair_decimal(prod, 'vDesc')
                valor_frete_item = extrair_decimal(prod, 'vFrete')
                valor_seg_item = extrair_decimal(prod, 'vSeg')
                valor_outras_item = extrair_decimal(prod, 'vOutro')
                
                # Impostos
                imposto = det.find('.//nfe:imposto', NAMESPACES) or det.find('.//imposto')
                
                # ICMS
                icms = imposto.find('.//nfe:ICMS', NAMESPACES) or imposto.find('.//ICMS')
                icms_grupo = None
                if icms is not None:
                    # Pode ser ICMS00, ICMS10, ICMS20, etc.
                    for child in icms:
                        if 'ICMS' in child.tag:
                            icms_grupo = child
                            break
                
                cst_icms = ''
                origem = ''
                bc_icms_item = Decimal(0)
                aliq_icms = Decimal(0)
                v_icms_item = Decimal(0)
                
                if icms_grupo is not None:
                    origem = extrair_texto(icms_grupo, 'orig')
                    cst_icms = extrair_texto(icms_grupo, 'CST') or extrair_texto(icms_grupo, 'CSOSN')
                    bc_icms_item = extrair_decimal(icms_grupo, 'vBC')
                    aliq_icms = extrair_decimal(icms_grupo, 'pICMS')
                    v_icms_item = extrair_decimal(icms_grupo, 'vICMS')
                
                # IPI
                ipi = imposto.find('.//nfe:IPI', NAMESPACES) or imposto.find('.//IPI')
                cst_ipi = ''
                bc_ipi = Decimal(0)
                aliq_ipi = Decimal(0)
                v_ipi_item = Decimal(0)
                
                if ipi is not None:
                    ipi_trib = ipi.find('.//nfe:IPITrib', NAMESPACES) or ipi.find('.//IPITrib')
                    if ipi_trib is not None:
                        cst_ipi = extrair_texto(ipi_trib, 'CST')
                        bc_ipi = extrair_decimal(ipi_trib, 'vBC')
                        aliq_ipi = extrair_decimal(ipi_trib, 'pIPI')
                        v_ipi_item = extrair_decimal(ipi_trib, 'vIPI')
                
                # PIS
                pis = imposto.find('.//nfe:PIS', NAMESPACES) or imposto.find('.//PIS')
                cst_pis = ''
                bc_pis = Decimal(0)
                aliq_pis = Decimal(0)
                v_pis_item = Decimal(0)
                
                if pis is not None:
                    pis_grupo = None
                    for child in pis:
                        if 'PIS' in child.tag:
                            pis_grupo = child
                            break
                    
                    if pis_grupo is not None:
                        cst_pis = extrair_texto(pis_grupo, 'CST')
                        bc_pis = extrair_decimal(pis_grupo, 'vBC')
                        aliq_pis = extrair_decimal(pis_grupo, 'pPIS')
                        v_pis_item = extrair_decimal(pis_grupo, 'vPIS')
                
                # COFINS
                cofins = imposto.find('.//nfe:COFINS', NAMESPACES) or imposto.find('.//COFINS')
                cst_cofins = ''
                bc_cofins = Decimal(0)
                aliq_cofins = Decimal(0)
                v_cofins_item = Decimal(0)
                
                if cofins is not None:
                    cofins_grupo = None
                    for child in cofins:
                        if 'COFINS' in child.tag:
                            cofins_grupo = child
                            break
                    
                    if cofins_grupo is not None:
                        cst_cofins = extrair_texto(cofins_grupo, 'CST')
                        bc_cofins = extrair_decimal(cofins_grupo, 'vBC')
                        aliq_cofins = extrair_decimal(cofins_grupo, 'pCOFINS')
                        v_cofins_item = extrair_decimal(cofins_grupo, 'vCOFINS')
                
                # Inserir item
                cursor.execute("""
                    INSERT INTO notas_fiscais_itens (
                        nota_fiscal_id, numero_item,
                        codigo_produto, codigo_ean, codigo_ncm, descricao,
                        quantidade, unidade, valor_unitario, valor_total,
                        valor_desconto, valor_frete, valor_seguro, valor_outras_despesas,
                        cfop,
                        cst_icms, origem_mercadoria, base_calculo_icms, aliquota_icms, valor_icms,
                        cst_ipi, base_calculo_ipi, aliquota_ipi, valor_ipi,
                        cst_pis, base_calculo_pis, aliquota_pis, valor_pis,
                        cst_cofins, base_calculo_cofins, aliquota_cofins, valor_cofins
                    )
                    VALUES (
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """, (
                    nota_id, numero_item,
                    codigo_produto, codigo_ean, codigo_ncm, descricao,
                    quantidade, unidade, valor_unitario, valor_total_item,
                    valor_desc_item, valor_frete_item, valor_seg_item, valor_outras_item,
                    cfop_item,
                    cst_icms, origem, bc_icms_item, aliq_icms, v_icms_item,
                    cst_ipi, bc_ipi, aliq_ipi, v_ipi_item,
                    cst_pis, bc_pis, aliq_pis, v_pis_item,
                    cst_cofins, bc_cofins, aliq_cofins, v_cofins_item
                ))
                
                itens_importados += 1
            
            conn.commit()
            
            logger.info(f"✅ NF-e importada: {chave_acesso} - {itens_importados} itens")
            
            return {
                'success': True,
                'nota_id': nota_id,
                'chave_acesso': chave_acesso,
                'numero': numero,
                'serie': serie,
                'valor_total': float(valor_nota),
                'itens_importados': itens_importados,
                'mensagem': f'NF-e {numero}/{serie} importada com sucesso'
            }
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    except ET.ParseError as e:
        return {
            'success': False,
            'error': f'Erro ao fazer parse do XML: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Erro ao importar NF-e: {e}")
        return {
            'success': False,
            'error': f'Erro ao importar NF-e: {str(e)}'
        }


# ===== IMPORTAÇÃO NFS-e (Simplificado) =====

def importar_xml_nfse(empresa_id, xml_content, usuario_id=None):
    """
    Importa XML de NFS-e (Nota Fiscal de Serviço Eletrônica)
    
    ATENÇÃO: Cada prefeitura tem um layout diferente!
    Esta é uma implementação simplificada que tenta extrair dados comuns.
    
    Args:
        empresa_id: ID da empresa
        xml_content: Conteúdo XML completo
        usuario_id: ID do usuário que importou
        
    Returns:
        dict com resultado da importação
    """
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Tentar localizar elementos comuns
        # (varia muito por prefeitura)
        
        # Número da NFS-e
        numero = (
            extrair_texto(root, './/Numero', namespace=None) or
            extrair_texto(root, './/NumeroNfse', namespace=None) or
            extrair_texto(root, './/IdentificacaoNfse/Numero', namespace=None)
        )
        
        if not numero:
            return {
                'success': False,
                'error': 'Número da NFS-e não encontrado no XML'
            }
        
        # Verificar se já foi importada
        nota_existente = executar_query(
            """
            SELECT id FROM notas_fiscais 
            WHERE empresa_id = %s AND tipo = 'NFSE' AND numero = %s
            """,
            (empresa_id, numero)
        )
        
        if nota_existente:
            return {
                'success': False,
                'error': f'NFS-e já importada (ID: {nota_existente[0]["id"]})',
                'nota_id': nota_existente[0]['id']
            }
        
        # Data de emissão
        data_emissao_str = (
            extrair_texto(root, './/DataEmissao', namespace=None) or
            extrair_texto(root, './/DataEmissaoNfse', namespace=None)
        )
        
        data_emissao = None
        if data_emissao_str:
            data_emissao = extrair_data(root, './/DataEmissao', namespace=None)
        
        # Tomador do serviço (cliente)
        tomador_cnpj = extrair_texto(root, './/TomadorServico/IdentificacaoTomador/CpfCnpj/Cnpj', namespace=None)
        if not tomador_cnpj:
            tomador_cnpj = extrair_texto(root, './/TomadorServico/IdentificacaoTomador/CpfCnpj/Cpf', namespace=None)
        
        tomador_nome = extrair_texto(root, './/TomadorServico/RazaoSocial', namespace=None)
        tomador_municipio = extrair_texto(root, './/TomadorServico/Endereco/Cidade', namespace=None)
        tomador_uf = extrair_texto(root, './/TomadorServico/Endereco/Uf', namespace=None)
        
        # Valores
        valor_servicos = extrair_decimal(root, './/Servico/Valores/ValorServicos', namespace=None)
        valor_deducoes = extrair_decimal(root, './/Servico/Valores/ValorDeducoes', namespace=None)
        valor_pis = extrair_decimal(root, './/Servico/Valores/ValorPis', namespace=None)
        valor_cofins = extrair_decimal(root, './/Servico/Valores/ValorCofins', namespace=None)
        valor_iss = extrair_decimal(root, './/Servico/Valores/ValorIss', namespace=None)
        valor_liquido = extrair_decimal(root, './/Servico/Valores/ValorLiquidoNfse', namespace=None)
        
        if valor_liquido == 0 and valor_servicos > 0:
            valor_liquido = valor_servicos - valor_deducoes
        
        # Alíquotas
        aliquota_pis = extrair_decimal(root, './/Servico/Valores/AliquotaPis', namespace=None)
        aliquota_cofins = extrair_decimal(root, './/Servico/Valores/AliquotaCofins', namespace=None)
        
        # Discriminação do serviço
        discriminacao = extrair_texto(root, './/Servico/Discriminacao', namespace=None)
        
        # ===== INSERIR NOTA NO BANCO =====
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO notas_fiscais (
                    empresa_id, tipo, numero, data_emissao, direcao,
                    participante_tipo, participante_cnpj_cpf, participante_nome,
                    participante_uf, participante_municipio,
                    valor_total, valor_servicos,
                    valor_pis, valor_cofins, valor_iss,
                    aliquota_pis, aliquota_cofins,
                    informacoes_complementares, xml_completo, xml_importado, data_importacao
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s
                )
                RETURNING id
            """, (
                empresa_id, 'NFSE', numero, data_emissao, 'SAIDA',
                'CLIENTE', formatar_cnpj_cpf(tomador_cnpj), tomador_nome,
                tomador_uf, tomador_municipio,
                valor_liquido, valor_servicos,
                valor_pis, valor_cofins, valor_iss,
                aliquota_pis, aliquota_cofins,
                discriminacao, xml_content, True, datetime.now()
            ))
            
            nota_id = cursor.fetchone()[0]
            
            # Inserir item único (serviço)
            cursor.execute("""
                INSERT INTO notas_fiscais_itens (
                    nota_fiscal_id, numero_item,
                    descricao, quantidade, unidade, valor_unitario, valor_total,
                    base_calculo_pis, aliquota_pis, valor_pis,
                    base_calculo_cofins, aliquota_cofins, valor_cofins
                )
                VALUES (
                    %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                nota_id, 1,
                discriminacao or 'Prestação de serviços', 1, 'SV', valor_servicos, valor_servicos,
                valor_servicos, aliquota_pis, valor_pis,
                valor_servicos, aliquota_cofins, valor_cofins
            ))
            
            conn.commit()
            
            logger.info(f"✅ NFS-e importada: {numero}")
            
            return {
                'success': True,
                'nota_id': nota_id,
                'numero': numero,
                'valor_total': float(valor_liquido),
                'itens_importados': 1,
                'mensagem': f'NFS-e {numero} importada com sucesso'
            }
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    except ET.ParseError as e:
        return {
            'success': False,
            'error': f'Erro ao fazer parse do XML: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Erro ao importar NFS-e: {e}")
        return {
            'success': False,
            'error': f'Erro ao importar NFS-e: {str(e)}'
        }


# ===== FUNÇÕES DE VALIDAÇÃO E CONSULTA =====

def listar_notas_fiscais(empresa_id, tipo=None, data_inicio=None, data_fim=None, limit=100):
    """
    Lista notas fiscais da empresa
    
    Args:
        empresa_id: ID da empresa
        tipo: Filtrar por tipo (NFE, NFSE, etc.) - opcional
        data_inicio: Data inicial - opcional
        data_fim: Data final - opcional
        limit: Limite de registros
        
    Returns:
        list: Lista de notas fiscais
    """
    filtros = ["empresa_id = %s"]
    parametros = [empresa_id]
    
    if tipo:
        filtros.append("tipo = %s")
        parametros.append(tipo)
    
    if data_inicio:
        filtros.append("data_emissao >= %s")
        parametros.append(data_inicio)
    
    if data_fim:
        filtros.append("data_emissao <= %s")
        parametros.append(data_fim)
    
    where_clause = " AND ".join(filtros)
    
    notas = executar_query(
        f"""
        SELECT 
            id, tipo, numero, serie, chave_acesso,
            data_emissao, direcao, valor_total,
            participante_nome, situacao
        FROM notas_fiscais
        WHERE {where_clause}
        ORDER BY data_emissao DESC, numero DESC
        LIMIT %s
        """,
        parametros + [limit]
    )
    
    return notas


def obter_detalhes_nota_fiscal(nota_id):
    """
    Obtém detalhes completos de uma nota fiscal
    
    Returns:
        dict: Dados da nota + lista de itens
    """
    nota = executar_query(
        """
        SELECT * FROM notas_fiscais WHERE id = %s
        """,
        (nota_id,)
    )
    
    if not nota:
        return None
    
    itens = executar_query(
        """
        SELECT * FROM notas_fiscais_itens
        WHERE nota_fiscal_id = %s
        ORDER BY numero_item
        """,
        (nota_id,)
    )
    
    return {
        'nota': nota[0],
        'itens': itens
    }


def calcular_totais_periodo(empresa_id, data_inicio, data_fim):
    """
    Calcula totais de notas fiscais no período
    
    Returns:
        dict: Totais de entrada e saída, PIS, COFINS
    """
    totais = executar_query(
        """
        SELECT 
            direcao,
            COUNT(*) as quantidade,
            SUM(valor_total) as valor_total,
            SUM(valor_pis) as total_pis,
            SUM(valor_cofins) as total_cofins
        FROM notas_fiscais
        WHERE empresa_id = %s
        AND data_emissao BETWEEN %s AND %s
        AND situacao = 'NORMAL'
        GROUP BY direcao
        """,
        (empresa_id, data_inicio, data_fim)
    )
    
    resultado = {
        'ENTRADA': {'quantidade': 0, 'valor_total': 0, 'total_pis': 0, 'total_cofins': 0},
        'SAIDA': {'quantidade': 0, 'valor_total': 0, 'total_pis': 0, 'total_cofins': 0}
    }
    
    for total in totais:
        resultado[total['direcao']] = total
    
    return resultado

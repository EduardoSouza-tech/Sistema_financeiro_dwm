# -*- coding: utf-8 -*-
"""
MÓDULO: NF-e Storage
Gerenciamento de armazenamento de XMLs de NF-e no filesystem

Estrutura de pastas:
storage/nfe/{CNPJ}/{ANO}/{MES}/[tipo]_{CHAVE}.xml

Tipos de arquivo:
- procNFe_{CHAVE}.xml: NF-e completa com protocolo
- resNFe_{CHAVE}.xml: Resumo da NF-e  
- evento_{TIPO}_{CHAVE}.xml: Eventos (cancelamento, corr, etc)

Autor: Sistema Financeiro DWM
Data: 2026-02-17
"""

import os
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple
import hashlib

# Configurar logging
logger = logging.getLogger(__name__)

# Diretório base para storage
STORAGE_BASE = Path(__file__).parent.parent.parent / 'storage' / 'nfe'


def _garantir_pasta_existe(caminho: Path) -> None:
    """
    Garante que a pasta existe, criando se necessário
    
    Args:
        caminho: Path da pasta
    """
    caminho.mkdir(parents=True, exist_ok=True)


def _extrair_ano_mes_da_chave(chave: str) -> Tuple[str, str]:
    """
    Extrai ano e mês da chave de acesso da NF-e
    
    Estrutura da chave (44 dígitos):
    UF (2) + AAMM (4) + CNPJ (14) + Modelo (2) + Série (3) + Número (9) + Tipo (1) + Código (8) + DV (1)
    Posição 2-3: AA (ano)
    Posição 4-5: MM (mês)
    
    Args:
        chave: Chave de acesso (44 dígitos)
    
    Returns:
        Tuple (ano, mes) ambos como strings
    """
    if not chave or len(chave) < 6:
        # Se chave inválida, usar data atual
        hoje = datetime.now()
        return str(hoje.year), f"{hoje.month:02d}"
    
    try:
        aa = chave[2:4]  # Ano (últimos 2 dígitos)
        mm = chave[4:6]  # Mês
        
        # Converter AA para AAAA (assumir 2000+)
        ano_completo = f"20{aa}"
        
        return ano_completo, mm
    except:
        hoje = datetime.now()
        return str(hoje.year), f"{hoje.month:02d}"


def _calcular_hash_md5(conteudo: str) -> str:
    """
    Calcula hash MD5 do conteúdo XML
    
    Args:
        conteudo: String do XML
    
    Returns:
        Hash MD5 em hexadecimal
    """
    return hashlib.md5(conteudo.encode('utf-8')).hexdigest()


def salvar_xml_nfe(
    cnpj_certificado: str,
    chave: str,
    xml_content: str,
    tipo_xml: str = 'procNFe',
    data_emissao: Optional[datetime] = None
) -> Dict[str, any]:
    """
    Salva XML da NF-e no filesystem
    
    Args:
        cnpj_certificado: CNPJ do certificado (usado para organização)
        chave: Chave de acesso da NF-e (44 dígitos)
        xml_content: Conteúdo do XML
        tipo_xml: Tipo do XML ('procNFe', 'resNFe', 'evento')
        data_emissao: Data de emissão (opcional, extrai da chave se não informado)
    
    Returns:
        Dict com:
            - success: bool
            - caminho: str (caminho completo do arquivo)
            - tamanho: int (bytes)
            - hash_md5: str
            - erro: str (se houver)
    """
    try:
        # Validar chave
        if not chave or len(chave) != 44:
            return {
                'success': False,
                'erro': f'Chave inválida: {chave}'
            }
        
        # Extrair ano e mês
        if data_emissao:
            ano = str(data_emissao.year)
            mes = f"{data_emissao.month:02d}"
        else:
            ano, mes = _extrair_ano_mes_da_chave(chave)
        
        # Montar caminho da pasta
        pasta = STORAGE_BASE / cnpj_certificado / ano / mes
        _garantir_pasta_existe(pasta)
        
        # Nome do arquivo
        nome_arquivo = f"{tipo_xml}_{chave}.xml"
        caminho_completo = pasta / nome_arquivo
        
        # Calcular hash antes de salvar
        hash_md5 = _calcular_hash_md5(xml_content)
        
        # Salvar arquivo
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Obter tamanho do arquivo
        tamanho = caminho_completo.stat().st_size
        
        logger.info(f"✓ XML salvo: {nome_arquivo} ({tamanho} bytes)")
        
        return {
            'success': True,
            'caminho': str(caminho_completo),
            'tamanho': tamanho,
            'hash_md5': hash_md5
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar XML {chave}: {e}")
        return {
            'success': False,
            'erro': str(e)
        }


def recuperar_xml_nfe(
    chave: str,
    cnpj_certificado: Optional[str] = None,
    tipo_xml: str = 'procNFe'
) -> Optional[str]:
    """
    Recupera XML da NF-e do filesystem
    
    Args:
        chave: Chave de acesso da NF-e (44 dígitos)
        cnpj_certificado: CNPJ do certificado (se None, busca em todos)
        tipo_xml: Tipo do XML ('procNFe', 'resNFe', 'evento')
    
    Returns:
        Conteúdo do XML ou None se não encontrado
    """
    try:
        # Se CNPJ especificado, busca direta
        if cnpj_certificado:
            ano, mes = _extrair_ano_mes_da_chave(chave)
            pasta = STORAGE_BASE / cnpj_certificado / ano / mes
            nome_arquivo = f"{tipo_xml}_{chave}.xml"
            caminho_completo = pasta / nome_arquivo
            
            if caminho_completo.exists():
                with open(caminho_completo, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        
        # Se CNPJ não especificado, busca em todos
        nome_arquivo = f"{tipo_xml}_{chave}.xml"
        
        # Percorrer todas as pastas procurando o arquivo
        for caminho in STORAGE_BASE.rglob(nome_arquivo):
            if caminho.is_file():
                with open(caminho, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao recuperar XML {chave}: {e}")
        return None


def existe_xml_nfe(
    chave: str,
    cnpj_certificado: Optional[str] = None,
    tipo_xml: str = 'procNFe'
) -> bool:
    """
    Verifica se XML da NF-e existe no filesystem
    
    Args:
        chave: Chave de acesso da NF-e (44 dígitos)
        cnpj_certificado: CNPJ do certificado (se None, busca em todos)
        tipo_xml: Tipo do XML ('procNFe', 'resNFe', 'evento')
    
    Returns:
        True se existe, False caso contrário
    """
    try:
        # Se CNPJ especificado,busca direta
        if cnpj_certificado:
            ano, mes = _extrair_ano_mes_da_chave(chave)
            pasta = STORAGE_BASE / cnpj_certificado / ano / mes
            nome_arquivo = f"{tipo_xml}_{chave}.xml"
            caminho_completo = pasta / nome_arquivo
            return caminho_completo.exists()
        
        # Se CNPJ não especificado, busca em todos
        nome_arquivo = f"{tipo_xml}_{chave}.xml"
        
        for caminho in STORAGE_BASE.rglob(nome_arquivo):
            if caminho.is_file():
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar XML {chave}: {e}")
        return False


def listar_xmls_periodo(
    cnpj_certificado: str,
    data_inicio: date,
    data_fim: date,
    tipo_xml: Optional[str] = None
) -> List[Dict[str, any]]:
    """
    Lista XMLs de um período específico
    
    Args:
        cnpj_certificado: CNPJ do certificado
        data_inicio: Data inicial do período
        data_fim: Data final do período
        tipo_xml: Tipo do XML (None = todos os tipos)
    
    Returns:
        Lista de dicionários com informações dos arquivos:
            - chave: str
            - tipo: str
            - caminho: str
            - tamanho: int
            - data_modificacao: datetime
    """
    try:
        resultado = []
        
        # Gerar lista de anos/meses no período
        atual = date(data_inicio.year, data_inicio.month, 1)
        fim = date(data_fim.year, data_fim.month, 1)
        
        meses = []
        while atual <= fim:
            meses.append((str(atual.year), f"{atual.month:02d}"))
            # Próximo mês
            if atual.month == 12:
                atual = date(atual.year + 1, 1, 1)
            else:
                atual = date(atual.year, atual.month + 1, 1)
        
        # Percorrer pastas e listar arquivos
        for ano, mes in meses:
            pasta = STORAGE_BASE / cnpj_certificado / ano / mes
            
            if not pasta.exists():
                continue
            
            # Padrão de busca
            if tipo_xml:
                padrao = f"{tipo_xml}_*.xml"
            else:
                padrao = "*.xml"
            
            for arquivo in pasta.glob(padrao):
                if arquivo.is_file():
                    # Extrair informações do nome do arquivo
                    nome = arquivo.stem  # Nome sem extensão
                    partes = nome.split('_', 1)
                    
                    if len(partes) == 2:
                        tipo_arquivo = partes[0]
                        chave_arquivo = partes[1]
                    else:
                        tipo_arquivo = 'unknown'
                        chave_arquivo = nome
                    
                    stat = arquivo.stat()
                    
                    resultado.append({
                        'chave': chave_arquivo,
                        'tipo': tipo_arquivo,
                        'caminho': str(arquivo),
                        'tamanho': stat.st_size,
                        'data_modificacao': datetime.fromtimestamp(stat.st_mtime)
                    })
        
        # Ordenar por data de modificação (mais recentes primeiro)
        resultado.sort(key=lambda x: x['data_modificacao'], reverse=True)
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar XMLs do período: {e}")
        return []


def obter_estatisticas_storage(cnpj_certificado: str) -> Dict[str, any]:
    """
    Obtém estatísticas de storage para um certificado
    
    Args:
        cnpj_certificado: CNPJ do certificado
    
    Returns:
        Dict com estatísticas:
            - total_arquivos: int
            - total_tamanho: int (bytes)
            - por_tipo: Dict[str, int]
            - por_ano: Dict[str, int]
    """
    try:
        pasta_cert = STORAGE_BASE / cnpj_certificado
        
        if not pasta_cert.exists():
            return {
                'total_arquivos': 0,
                'total_tamanho': 0,
                'por_tipo': {},
                'por_ano': {}
            }
        
        total_arquivos = 0
        total_tamanho = 0
        por_tipo = {}
        por_ano = {}
        
        # Percorrer todos os XMLs
        for arquivo in pasta_cert.rglob("*.xml"):
            if arquivo.is_file():
                total_arquivos += 1
                total_tamanho += arquivo.stat().st_size
                
                # Contar por tipo
                nome = arquivo.stem
                tipo = nome.split('_')[0] if '_' in nome else 'unknown'
                por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
                
                # Contar por ano
                ano = arquivo.parent.parent.name  # pasta do ano
                por_ano[ano] = por_ano.get(ano, 0) + 1
        
        return {
            'total_arquivos': total_arquivos,
            'total_tamanho': total_tamanho,
            'por_tipo': por_tipo,
            'por_ano': por_ano
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return {
            'total_arquivos': 0,
            'total_tamanho': 0,
            'por_tipo': {},
            'por_ano': {}
        }


def limpar_storage_antigo(cnpj_certificado: str, anos_manter: int = 7) -> Dict[str, any]:
    """
    Remove arquivos mais antigos que X anos (conforme legislação fiscal)
    
    Args:
        cnpj_certificado: CNPJ do certificado
        anos_manter: Número de anos a manter (padrão: 7 anos - obrigação fiscal)
    
    Returns:
        Dict com resultado da limpeza:
            - arquivos_removidos: int
            - espaço_liberado: int (bytes)
            -anos_removidos: List[str]
    """
    try:
        pasta_cert = STORAGE_BASE / cnpj_certificado
        
        if not pasta_cert.exists():
            return {
                'arquivos_removidos': 0,
                'espaço_liberado': 0,
                'anos_removidos': []
            }
        
        ano_atual = datetime.now().year
        ano_limite = ano_atual - anos_manter
        
        arquivos_removidos = 0
        espaço_liberado = 0
        anos_removidos = []
        
        # Percorrer pastas de anos
        for pasta_ano in pasta_cert.iterdir():
            if pasta_ano.is_dir():
                try:
                    ano = int(pasta_ano.name)
                    
                    if ano < ano_limite:
                        # Contar arquivos e tamanho antes de remover
                        for arquivo in pasta_ano.rglob("*.xml"):
                            if arquivo.is_file():
                                arquivos_removidos += 1
                                espaço_liberado += arquivo.stat().st_size
                        
                        # Remover pasta do ano inteiro
                        import shutil
                        shutil.rmtree(pasta_ano)
                        anos_removidos.append(str(ano))
                        
                        logger.info(f"✓ Removidos arquivos do ano {ano}")
                        
                except ValueError:
                    # Nome da pasta não é um ano válido, ignorar
                    pass
        
        return {
            'arquivos_removidos': arquivos_removidos,
            'espaço_liberado': espaço_liberado,
            'anos_removidos': anos_removidos
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar storage antigo: {e}")
        return {
            'arquivos_removidos': 0,
            'espaço_liberado': 0,
            'anos_removidos': []
        }


# Função para uso em testes
def _criar_estrutura_teste():
    """Cria estrutura de pastas para testes (uso interno)"""
    _garantir_pasta_existe(STORAGE_BASE)
    print(f"✓ Estrutura de storage criada em: {STORAGE_BASE}")


if __name__ == '__main__':
    # Teste básico
    print("=" * 70)
    print("TESTE: Módulo NF-e Storage")
    print("=" * 70)
    
    _criar_estrutura_teste()
    
    # Teste de salvamento
    chave_teste = "50260112345678000190550010000001001234567890"
    xml_teste = '<?xml version="1.0"?><NFe><infNFe>Teste</infNFe></NFe>'
    
    resultado = salvar_xml_nfe(
        cnpj_certificado="12345678000190",
        chave=chave_teste,
        xml_content=xml_teste,
        tipo_xml="procNFe"
    )
    
    print(f"\nResultado do salvamento:")
    print(f"  Success: {resultado['success']}")
    if resultado['success']:
        print(f"  Caminho: {resultado['caminho']}")
        print(f"  Tamanho: {resultado['tamanho']} bytes")
        print(f"  Hash MD5: {resultado['hash_md5']}")
    
    # Teste de recuperação
    xml_recuperado = recuperar_xml_nfe(chave_teste, "12345678000190")
    print(f"\nXML recuperado: {'✓' if xml_recuperado else '✗'}")
    
    # Teste de verificação
    existe = existe_xml_nfe(chave_teste, "12345678000190")
    print(f"Arquivo existe: {'✓' if existe else '✗'}")
    
    print("\n✓ Testes concluídos!")

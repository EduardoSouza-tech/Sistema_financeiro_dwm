# -*- coding: utf-8 -*-
"""
MÓDULO: NF-e (Nota Fiscal Eletrônica)
Sistema de busca, processamento e armazenamento de NF-e via API SEFAZ

Componentes:
- nfe_busca: Comunicação com SEFAZ (DFe Distribution, Consulta por Chave)
- nfe_processor: Extração e processamento de dados XML
- nfe_storage: Armazenamento de XMLs no filesystem
- nfe_api: Endpoints da API REST

Autor: Sistema Financeiro DWM
Data: 2026-02-17
"""

__version__ = '1.0.0'

from .nfe_busca import (
    consultar_ultimo_nsu_sefaz,
    baixar_documentos_dfe,
    consultar_nfe_por_chave,
    buscar_multiplas_chaves
)

from .nfe_processor import (
    extrair_dados_nfe,
    detectar_schema_nfe,
    validar_chave_nfe,
    extrair_resumo_nfe,
    determinar_direcao_nfe
)

from .nfe_storage import (
    salvar_xml_nfe,
    recuperar_xml_nfe,
    existe_xml_nfe,
    listar_xmls_periodo
)

__all__ = [
    # Busca
    'consultar_ultimo_nsu_sefaz',
    'baixar_documentos_dfe',
    'consultar_nfe_por_chave',
    'buscar_multiplas_chaves',
    
    # Processamento
    'extrair_dados_nfe',
    'detectar_schema_nfe',
    'validar_chave_nfe',
    'extrair_resumo_nfe',
    'determinar_direcao_nfe',
    
    # Armazenamento
    'salvar_xml_nfe',
    'recuperar_xml_nfe',
    'existe_xml_nfe',
    'listar_xmls_periodo'
]

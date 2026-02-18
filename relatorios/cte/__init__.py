# -*- coding: utf-8 -*-
"""
MÓDULO: CT-e (Conhecimento de Transporte Eletrônico)
Sistema de busca, processamento e armazenamento de CT-e via API SEFAZ

Componentes:
- cte_busca: Comunicação com SEFAZ (DFe Distribution, Consulta por Chave)
- cte_processor: Extração e processamento de dados XML
- cte_storage: Armazenamento de XMLs no filesystem
- cte_api: Endpoints da API REST

Autor: Sistema Financeiro DWM
Data: 2026-02-17

NOTA: Módulos comentados temporariamente até implementação dos arquivos .py
"""

__version__ = '1.0.0'

# TODO: Descomentar quando os módulos forem criados
# from .cte_busca import (
#     consultar_ultimo_nsu_sefaz_cte,
#     baixar_documentos_dfe_cte,
#     consultar_cte_por_chave,
#     buscar_multiplas_chaves_cte
# )

# from .cte_processor import (
#     extrair_dados_cte,
#     detectar_schema_cte,
#     validar_chave_cte,
#     extrair_resumo_cte,
#     determinar_direcao_cte
# )

# from .cte_storage import (
#     salvar_xml_cte,
#     recuperar_xml_cte,
#     existe_xml_cte,
#     listar_xmls_periodo_cte
# )

__all__ = []

# TODO: Descomentar quando os módulos forem criados
# __all__ = [
#     # Busca
#     'consultar_ultimo_nsu_sefaz_cte',
#     'baixar_documentos_dfe_cte',
#     'consultar_cte_por_chave',
#     'buscar_multiplas_chaves_cte',
#     
#     # Processamento
#     'extrair_dados_cte',
#     'detectar_schema_cte',
#     'validar_chave_cte',
#     'extrair_resumo_cte',
#     'determinar_direcao_cte',
#     
#     # Armazenamento
#     'salvar_xml_cte',
#     'recuperar_xml_cte',
#     'existe_xml_cte',
#     'listar_xmls_periodo_cte'
# ]

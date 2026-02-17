# -*- coding: utf-8 -*-
"""
MÓDULO: Relatórios Fiscais
Sistema de busca e processamento de documentos fiscais eletrônicos

Submódulos:
- nfe: NF-e (Nota Fiscal Eletrônica)
- cte: CT-e (Conhecimento de Transporte Eletrônico)

Autor: Sistema Financeiro DWM
Data: 2026-02-17
"""

__version__ = '1.0.0'
__author__ = 'Sistema Financeiro DWM'

from . import nfe
from . import cte

__all__ = ['nfe', 'cte']

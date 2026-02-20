"""
Módulo para exportação de relatórios em PDF
Utiliza ReportLab para geração de PDFs formatados
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def formatar_moeda_pdf(valor: float) -> str:
    """Formata valor para display em moeda brasileira"""
    if valor < 0:
        return f"(R$ {abs(valor):,.2f})".replace(',', '_').replace('.', ',').replace('_', '.')
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')


def formatar_percentual_pdf(valor: float) -> str:
    """Formata percentual para display"""
    return f"{valor:.2f}%"


def gerar_dre_pdf(
    dados_dre: Dict,
    nome_empresa: str = "Empresa",
    periodo: str = ""
) -> BytesIO:
    """
    Gera PDF da DRE (Demonstração do Resultado do Exercício)
    
    Args:
        dados_dre: Dicionário com dados da DRE retornados por gerar_dre()
        nome_empresa: Nome da empresa para o cabeçalho
        periodo: String com período (ex: "01/01/2026 a 31/01/2026")
    
    Returns:
        BytesIO com o PDF gerado
    """
    
    # Criar buffer para o PDF
    buffer = BytesIO()
    
    # Criar documento PDF (A4, margens)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulo
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Estilo para data de geração
    data_style = ParagraphStyle(
        'DataStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_RIGHT
    )
    
    # Elementos do documento
    elements = []
    
    # Cabeçalho
    elements.append(Paragraph(nome_empresa, titulo_style))
    elements.append(Paragraph("DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO", titulo_style))
    
    if periodo:
        elements.append(Paragraph(f"Período: {periodo}", subtitulo_style))
    
    elements.append(Spacer(1, 10*mm))
    
    # Extrair dados da DRE
    dre = dados_dre.get('dre', {})
    comparacao = dados_dre.get('dre_anterior')
    
    # Preparar dados da tabela
    dados_tabela = []
    
    # Cabeçalho da tabela
    if comparacao:
        dados_tabela.append([
            'DESCRIÇÃO',
            'VALOR ATUAL (R$)',
            '% RECEITA',
            'VALOR ANTERIOR (R$)',
            'VARIAÇÃO'
        ])
    else:
        dados_tabela.append([
            'DESCRIÇÃO',
            'VALOR (R$)',
            '% RECEITA'
        ])
    
    def adicionar_linha(descricao: str, valor: float, percentual: float, 
                       nivel: int = 0, negrito: bool = False, final: bool = False,
                       valor_anterior: Optional[float] = None, variacao: Optional[float] = None):
        """Adiciona linha na tabela com formatação"""
        # Indentação baseada no nível
        desc_formatada = "  " * nivel + descricao
        
        if comparacao and valor_anterior is not None:
            linha = [
                desc_formatada,
                formatar_moeda_pdf(valor),
                formatar_percentual_pdf(percentual),
                formatar_moeda_pdf(valor_anterior),
                f"{variacao:+.2f}%" if variacao is not None else "-"
            ]
        else:
            linha = [
                desc_formatada,
                formatar_moeda_pdf(valor),
                formatar_percentual_pdf(percentual)
            ]
        
        dados_tabela.append(linha)
        return len(dados_tabela) - 1  # Retorna índice da linha para formatação
    
    indices_formato = []
    
    # 1. RECEITA BRUTA
    receita_bruta = dre.get('receita_bruta', {})
    idx = adicionar_linha(
        "1. RECEITA BRUTA",
        receita_bruta.get('total', 0),
        receita_bruta.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('receita_bruta', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('receita_bruta') if comparacao else None
    )
    indices_formato.append(('subtotal', idx))
    
    # Sub-contas de receita bruta
    for item in receita_bruta.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,  # Percentual não exibido para sub-contas
            nivel=1
        )
    
    # 2. DEDUÇÕES
    deducoes = dre.get('deducoes', {})
    idx = adicionar_linha(
        "2. (-) DEDUÇÕES DA RECEITA",
        -abs(deducoes.get('total', 0)),
        deducoes.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=-abs(comparacao.get('deducoes', {}).get('total', 0)) if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('deducoes') if comparacao else None
    )
    indices_formato.append(('deducao', idx))
    
    # Sub-contas de deduções
    for item in deducoes.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            -abs(item.get('valor', 0)),
            0,
            nivel=1
        )
    
    # 3. RECEITA LÍQUIDA
    receita_liquida = dre.get('receita_liquida', {})
    idx = adicionar_linha(
        "3. = RECEITA LÍQUIDA",
        receita_liquida.get('total', 0),
        receita_liquida.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('receita_liquida', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('receita_liquida') if comparacao else None
    )
    indices_formato.append(('resultado', idx))
    
    # 4. CUSTOS
    custos = dre.get('custos', {})
    idx = adicionar_linha(
        "4. (-) CUSTOS",
        custos.get('total', 0),
        custos.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('custos', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('custos') if comparacao else None
    )
    indices_formato.append(('deducao', idx))
    
    # Sub-contas de custos
    for item in custos.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=1
        )
    
    # 5. LUCRO BRUTO
    lucro_bruto = dre.get('lucro_bruto', {})
    idx = adicionar_linha(
        "5. = LUCRO BRUTO",
        lucro_bruto.get('total', 0),
        lucro_bruto.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('lucro_bruto', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('lucro_bruto') if comparacao else None
    )
    indices_formato.append(('resultado', idx))
    
    # 6. DESPESAS OPERACIONAIS
    desp_op = dre.get('despesas_operacionais', {})
    idx = adicionar_linha(
        "6. (-) DESPESAS OPERACIONAIS",
        desp_op.get('total', 0),
        desp_op.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('despesas_operacionais', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('despesas_operacionais') if comparacao else None
    )
    indices_formato.append(('deducao', idx))
    
    # Sub-contas de despesas operacionais
    for item in desp_op.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=1
        )
    
    # 7. RESULTADO OPERACIONAL
    res_op = dre.get('resultado_operacional', {})
    idx = adicionar_linha(
        "7. = RESULTADO OPERACIONAL",
        res_op.get('total', 0),
        res_op.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('resultado_operacional', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('resultado_operacional') if comparacao else None
    )
    indices_formato.append(('resultado', idx))
    
    # 8. RESULTADO FINANCEIRO
    res_fin = dre.get('resultado_financeiro', {})
    
    # 8.1 Receitas Financeiras
    rec_fin = res_fin.get('receitas', {})
    adicionar_linha(
        "8.1 (+) Receitas Financeiras",
        rec_fin.get('total', 0),
        rec_fin.get('percentual', 0),
        nivel=1
    )
    for item in rec_fin.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=2
        )
    
    # 8.2 Despesas Financeiras
    desp_fin = res_fin.get('despesas', {})
    adicionar_linha(
        "8.2 (-) Despesas Financeiras",
        desp_fin.get('total', 0),
        desp_fin.get('percentual', 0),
        nivel=1
    )
    for item in desp_fin.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=2
        )
    
    # 8. Total Resultado Financeiro
    idx = adicionar_linha(
        "8. = RESULTADO FINANCEIRO",
        res_fin.get('total', 0),
        res_fin.get('percentual', 0),
        nivel=0,
        negrito=True,
        valor_anterior=comparacao.get('resultado_financeiro', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('resultado_financeiro') if comparacao else None
    )
    indices_formato.append(('resultado', idx))
    
    # 9. LUCRO LÍQUIDO DO EXERCÍCIO
    lucro_liq = dre.get('lucro_liquido', {})
    idx = adicionar_linha(
        "9. = LUCRO LÍQUIDO DO EXERCÍCIO",
        lucro_liq.get('total', 0),
        lucro_liq.get('percentual', 0),
        nivel=0,
        negrito=True,
        final=True,
        valor_anterior=comparacao.get('lucro_liquido', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('lucro_liquido') if comparacao else None
    )
    indices_formato.append(('final', idx))
    
    # Criar tabela
    if comparacao:
        col_widths = [100*mm, 30*mm, 20*mm, 30*mm, 20*mm]
    else:
        col_widths = [120*mm, 40*mm, 30*mm]
    
    tabela = Table(dados_tabela, colWidths=col_widths)
    
    # Estilo da tabela
    estilo_tabela = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Corpo da tabela
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ])
    
    # Aplicar formatação especial para linhas específicas
    for tipo, idx in indices_formato:
        if tipo == 'subtotal':
            estilo_tabela.add('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#e8f5e9'))
            estilo_tabela.add('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold')
            estilo_tabela.add('TEXTCOLOR', (0, idx), (-1, idx), colors.HexColor('#27ae60'))
        elif tipo == 'deducao':
            estilo_tabela.add('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#ffebee'))
            estilo_tabela.add('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold')
            estilo_tabela.add('TEXTCOLOR', (0, idx), (-1, idx), colors.HexColor('#e74c3c'))
        elif tipo == 'resultado':
            estilo_tabela.add('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#e3f2fd'))
            estilo_tabela.add('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold')
            estilo_tabela.add('TEXTCOLOR', (0, idx), (-1, idx), colors.HexColor('#3498db'))
        elif tipo == 'final':
            estilo_tabela.add('BACKGROUND', (0, idx), (-1, idx), colors.HexColor('#2c3e50'))
            estilo_tabela.add('FONTNAME', (0, idx), (-1, idx), 'Helvetica-Bold')
            estilo_tabela.add('TEXTCOLOR', (0, idx), (-1, idx), colors.white)
            estilo_tabela.add('FONTSIZE', (0, idx), (-1, idx), 11)
            estilo_tabela.add('TOPPADDING', (0, idx), (-1, idx), 8)
            estilo_tabela.add('BOTTOMPADDING', (0, idx), (-1, idx), 8)
    
    tabela.setStyle(estilo_tabela)
    elements.append(tabela)
    
    # Rodapé
    elements.append(Spacer(1, 10*mm))
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    elements.append(Paragraph(f"Relatório gerado em: {data_geracao}", data_style))
    
    # Gerar PDF
    doc.build(elements)
    
    # Resetar buffer para leitura
    buffer.seek(0)
    
    return buffer


def gerar_dashboard_pdf(
    dados_dashboard: Dict,
    nome_empresa: str = "Empresa",
    mes_referencia: str = ""
) -> BytesIO:
    """
    Gera PDF do Dashboard Gerencial
    (Implementação futura se necessário)
    """
    # TODO: Implementar se necessário
    pass

"""
Módulo para exportação de relatórios em PDF e Excel
Utiliza ReportLab para PDFs e openpyxl para Excel
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
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


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


def gerar_dre_excel(
    dados_dre: Dict,
    nome_empresa: str = "Empresa",
    periodo: str = ""
) -> BytesIO:
    """
    Gera Excel da DRE (Demonstração do Resultado do Exercício)
    
    Args:
        dados_dre: Dicionário com dados da DRE retornados por gerar_dre()
        nome_empresa: Nome da empresa para o cabeçalho
        periodo: String com período (ex: "01/01/2026 a 31/01/2026")
    
    Returns:
        BytesIO com o arquivo Excel gerado
    """
    
    # Criar workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "DRE"
    
    # Extrair dados
    dre = dados_dre.get('dre', {})
    comparacao = dados_dre.get('dre_anterior')
    
    # ===== ESTILOS =====
    
    # Fonte título
    font_titulo = Font(name='Arial', size=14, bold=True, color='2C3E50')
    
    # Fonte subtítulo
    font_subtitulo = Font(name='Arial', size=11, color='34495E')
    
    # Fonte cabeçalho tabela
    font_header = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    fill_header = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
    
    # Bordas
    borda_fina = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    borda_grossa = Border(
        left=Side(style='medium', color='2C3E50'),
        right=Side(style='medium', color='2C3E50'),
        top=Side(style='medium', color='2C3E50'),
        bottom=Side(style='medium', color='2C3E50')
    )
    
    # Cores de fundo por tipo
    fill_receita = PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid')
    fill_deducao = PatternFill(start_color='FFEBEE', end_color='FFEBEE', fill_type='solid')
    fill_resultado = PatternFill(start_color='E3F2FD', end_color='E3F2FD', fill_type='solid')
    fill_final = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
    fill_alternado = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
    
    # Fontes por tipo
    font_receita = Font(name='Arial', size=10, bold=True, color='27AE60')
    font_deducao = Font(name='Arial', size=10, bold=True, color='E74C3C')
    font_resultado = Font(name='Arial', size=10, bold=True, color='3498DB')
    font_final = Font(name='Arial', size=11, bold=True, color='FFFFFF')
    font_normal = Font(name='Arial', size=10, color='2C3E50')
    font_subconta = Font(name='Arial', size=9, color='34495E', italic=True)
    
    # Alinhamentos
    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')
    
    # ===== CABEÇALHO =====
    
    # Linha 1: Nome da empresa
    ws.merge_cells('A1:E1' if comparacao else 'A1:C1')
    cell_empresa = ws['A1']
    cell_empresa.value = nome_empresa
    cell_empresa.font = font_titulo
    cell_empresa.alignment = align_center
    
    # Linha 2: Título
    ws.merge_cells('A2:E2' if comparacao else 'A2:C2')
    cell_titulo = ws['A2']
    cell_titulo.value = "DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO"
    cell_titulo.font = font_titulo
    cell_titulo.alignment = align_center
    
    # Linha 3: Período
    if periodo:
        ws.merge_cells('A3:E3' if comparacao else 'A3:C3')
        cell_periodo = ws['A3']
        cell_periodo.value = f"Período: {periodo}"
        cell_periodo.font = font_subtitulo
        cell_periodo.alignment = align_center
    
    # Linha 4: Vazia
    linha_atual = 5
    
    # ===== CABEÇALHO DA TABELA =====
    
    if comparacao:
        headers = ['DESCRIÇÃO', 'VALOR ATUAL (R$)', '% RECEITA', 'VALOR ANTERIOR (R$)', 'VARIAÇÃO (%)']
        ws.column_dimensions['A'].width = 50
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 15
    else:
        headers = ['DESCRIÇÃO', 'VALOR (R$)', '% RECEITA']
        ws.column_dimensions['A'].width = 60
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 15
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=linha_atual, column=col_idx)
        cell.value = header
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = borda_fina
    
    linha_atual += 1
    linha_dados_inicio = linha_atual
    
    # ===== FUNÇÃO AUXILIAR PARA ADICIONAR LINHAS =====
    
    def adicionar_linha(descricao: str, valor: float, percentual: float,
                       nivel: int = 0, tipo: str = 'normal',
                       valor_anterior: Optional[float] = None,
                       variacao: Optional[float] = None):
        """Adiciona linha na planilha com formatação"""
        nonlocal linha_atual
        
        # Indentação
        desc_formatada = "  " * nivel + descricao
        
        # Coluna A: Descrição
        cell_desc = ws.cell(row=linha_atual, column=1)
        cell_desc.value = desc_formatada
        cell_desc.alignment = align_left
        cell_desc.border = borda_fina
        
        # Coluna B: Valor
        cell_valor = ws.cell(row=linha_atual, column=2)
        cell_valor.value = valor
        cell_valor.number_format = '#,##0.00'
        cell_valor.alignment = align_right
        cell_valor.border = borda_fina
        
        # Coluna C: Percentual
        cell_perc = ws.cell(row=linha_atual, column=3)
        cell_perc.value = percentual / 100  # Excel espera 0.1 para 10%
        cell_perc.number_format = '0.00%'
        cell_perc.alignment = align_right
        cell_perc.border = borda_fina
        
        # Colunas D e E: Comparação (se houver)
        if comparacao and valor_anterior is not None:
            cell_ant = ws.cell(row=linha_atual, column=4)
            cell_ant.value = valor_anterior
            cell_ant.number_format = '#,##0.00'
            cell_ant.alignment = align_right
            cell_ant.border = borda_fina
            
            cell_var = ws.cell(row=linha_atual, column=5)
            if variacao is not None:
                cell_var.value = variacao / 100
                cell_var.number_format = '+0.00%;-0.00%'
            else:
                cell_var.value = '-'
            cell_var.alignment = align_right
            cell_var.border = borda_fina
        
        # Aplicar formatação por tipo
        if tipo == 'receita':
            cell_desc.fill = fill_receita
            cell_valor.fill = fill_receita
            cell_perc.fill = fill_receita
            cell_desc.font = font_receita
            cell_valor.font = font_receita
            cell_perc.font = font_receita
            if comparacao:
                cell_ant.fill = fill_receita
                cell_var.fill = fill_receita
                cell_ant.font = font_receita
                cell_var.font = font_receita
        elif tipo == 'deducao':
            cell_desc.fill = fill_deducao
            cell_valor.fill = fill_deducao
            cell_perc.fill = fill_deducao
            cell_desc.font = font_deducao
            cell_valor.font = font_deducao
            cell_perc.font = font_deducao
            if comparacao:
                cell_ant.fill = fill_deducao
                cell_var.fill = fill_deducao
                cell_ant.font = font_deducao
                cell_var.font = font_deducao
        elif tipo == 'resultado':
            cell_desc.fill = fill_resultado
            cell_valor.fill = fill_resultado
            cell_perc.fill = fill_resultado
            cell_desc.font = font_resultado
            cell_valor.font = font_resultado
            cell_perc.font = font_resultado
            if comparacao:
                cell_ant.fill = fill_resultado
                cell_var.fill = fill_resultado
                cell_ant.font = font_resultado
                cell_var.font = font_resultado
        elif tipo == 'final':
            cell_desc.fill = fill_final
            cell_valor.fill = fill_final
            cell_perc.fill = fill_final
            cell_desc.font = font_final
            cell_valor.font = font_final
            cell_perc.font = font_final
            cell_desc.border = borda_grossa
            cell_valor.border = borda_grossa
            cell_perc.border = borda_grossa
            if comparacao:
                cell_ant.fill = fill_final
                cell_var.fill = fill_final
                cell_ant.font = font_final
                cell_var.font = font_final
                cell_ant.border = borda_grossa
                cell_var.border = borda_grossa
        elif tipo == 'subconta':
            cell_desc.font = font_subconta
            cell_valor.font = font_subconta
            cell_perc.font = font_subconta
            if linha_atual % 2 == 0:
                cell_desc.fill = fill_alternado
                cell_valor.fill = fill_alternado
                cell_perc.fill = fill_alternado
                if comparacao:
                    cell_ant.fill = fill_alternado
                    cell_var.fill = fill_alternado
        else:  # normal
            cell_desc.font = font_normal
            cell_valor.font = font_normal
            cell_perc.font = font_normal
            if linha_atual % 2 == 0:
                cell_desc.fill = fill_alternado
                cell_valor.fill = fill_alternado
                cell_perc.fill = fill_alternado
                if comparacao:
                    cell_ant.fill = fill_alternado
                    cell_var.fill = fill_alternado
        
        linha_atual += 1
    
    # ===== POPULAR DADOS DA DRE =====
    
    # 1. RECEITA BRUTA
    receita_bruta = dre.get('receita_bruta', {})
    adicionar_linha(
        "1. RECEITA BRUTA",
        receita_bruta.get('total', 0),
        receita_bruta.get('percentual', 0),
        nivel=0,
        tipo='receita',
        valor_anterior=comparacao.get('receita_bruta', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('receita_bruta') if comparacao else None
    )
    for item in receita_bruta.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=1,
            tipo='subconta'
        )
    
    # 2. DEDUÇÕES
    deducoes = dre.get('deducoes', {})
    adicionar_linha(
        "2. (-) DEDUÇÕES DA RECEITA",
        -abs(deducoes.get('total', 0)),
        deducoes.get('percentual', 0),
        nivel=0,
        tipo='deducao',
        valor_anterior=-abs(comparacao.get('deducoes', {}).get('total', 0)) if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('deducoes') if comparacao else None
    )
    for item in deducoes.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            -abs(item.get('valor', 0)),
            0,
            nivel=1,
            tipo='subconta'
        )
    
    # 3. RECEITA LÍQUIDA
    receita_liquida = dre.get('receita_liquida', {})
    adicionar_linha(
        "3. = RECEITA LÍQUIDA",
        receita_liquida.get('total', 0),
        receita_liquida.get('percentual', 0),
        nivel=0,
        tipo='resultado',
        valor_anterior=comparacao.get('receita_liquida', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('receita_liquida') if comparacao else None
    )
    
    # 4. CUSTOS
    custos = dre.get('custos', {})
    adicionar_linha(
        "4. (-) CUSTOS",
        custos.get('total', 0),
        custos.get('percentual', 0),
        nivel=0,
        tipo='deducao',
        valor_anterior=comparacao.get('custos', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('custos') if comparacao else None
    )
    for item in custos.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=1,
            tipo='subconta'
        )
    
    # 5. LUCRO BRUTO
    lucro_bruto = dre.get('lucro_bruto', {})
    adicionar_linha(
        "5. = LUCRO BRUTO",
        lucro_bruto.get('total', 0),
        lucro_bruto.get('percentual', 0),
        nivel=0,
        tipo='resultado',
        valor_anterior=comparacao.get('lucro_bruto', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('lucro_bruto') if comparacao else None
    )
    
    # 6. DESPESAS OPERACIONAIS
    desp_op = dre.get('despesas_operacionais', {})
    adicionar_linha(
        "6. (-) DESPESAS OPERACIONAIS",
        desp_op.get('total', 0),
        desp_op.get('percentual', 0),
        nivel=0,
        tipo='deducao',
        valor_anterior=comparacao.get('despesas_operacionais', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('despesas_operacionais') if comparacao else None
    )
    for item in desp_op.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=1,
            tipo='subconta'
        )
    
    # 7. RESULTADO OPERACIONAL
    res_op = dre.get('resultado_operacional', {})
    adicionar_linha(
        "7. = RESULTADO OPERACIONAL",
        res_op.get('total', 0),
        res_op.get('percentual', 0),
        nivel=0,
        tipo='resultado',
        valor_anterior=comparacao.get('resultado_operacional', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('resultado_operacional') if comparacao else None
    )
    
    # 8. RESULTADO FINANCEIRO
    res_fin = dre.get('resultado_financeiro', {})
    
    # 8.1 Receitas Financeiras
    rec_fin = res_fin.get('receitas', {})
    adicionar_linha(
        "8.1 (+) Receitas Financeiras",
        rec_fin.get('total', 0),
        rec_fin.get('percentual', 0),
        nivel=1,
        tipo='normal'
    )
    for item in rec_fin.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=2,
            tipo='subconta'
        )
    
    # 8.2 Despesas Financeiras
    desp_fin = res_fin.get('despesas', {})
    adicionar_linha(
        "8.2 (-) Despesas Financeiras",
        desp_fin.get('total', 0),
        desp_fin.get('percentual', 0),
        nivel=1,
        tipo='normal'
    )
    for item in desp_fin.get('itens', []):
        adicionar_linha(
            item.get('descricao', ''),
            item.get('valor', 0),
            0,
            nivel=2,
            tipo='subconta'
        )
    
    # 8. Total Resultado Financeiro
    adicionar_linha(
        "8. = RESULTADO FINANCEIRO",
        res_fin.get('total', 0),
        res_fin.get('percentual', 0),
        nivel=0,
        tipo='resultado',
        valor_anterior=comparacao.get('resultado_financeiro', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('resultado_financeiro') if comparacao else None
    )
    
    # 9. LUCRO LÍQUIDO DO EXERCÍCIO
    lucro_liq = dre.get('lucro_liquido', {})
    adicionar_linha(
        "9. = LUCRO LÍQUIDO DO EXERCÍCIO",
        lucro_liq.get('total', 0),
        lucro_liq.get('percentual', 0),
        nivel=0,
        tipo='final',
        valor_anterior=comparacao.get('lucro_liquido', {}).get('total') if comparacao else None,
        variacao=dados_dre.get('variacoes', {}).get('lucro_liquido') if comparacao else None
    )
    
    # ===== RODAPÉ =====
    linha_atual += 2
    ws.merge_cells(f'A{linha_atual}:E{linha_atual}' if comparacao else f'A{linha_atual}:C{linha_atual}')
    cell_rodape = ws[f'A{linha_atual}']
    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    cell_rodape.value = f"Relatório gerado em: {data_geracao}"
    cell_rodape.font = Font(name='Arial', size=8, color='7F8C8D', italic=True)
    cell_rodape.alignment = align_right
    
    # ===== SALVAR EM BUFFER =====
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer

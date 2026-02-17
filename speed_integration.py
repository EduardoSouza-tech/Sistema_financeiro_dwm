"""
Funções para exportação de dados contábeis para Sp Speed
Formatos compatíveis com Speed Contábil/Fiscal/Contribuições
"""

import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def exportar_plano_contas_speed(contas: List[Dict]) -> str:
    """
    Exporta plano de contas no formato TXT para Speed
    
    Formato: CODIGO|DESCRICAO|TIPO|NATUREZA|GRAU|SUPERIOR|CODIGO_REF|NAT_SPED
    
    Args:
        contas: Lista de dicionários com dados das contas
        
    Returns:
        String no formato TXT para importação no Speed
    """
    linhas = []
    
    # Cabeçalho
    linhas.append("CODIGO|DESCRICAO|TIPO|NATUREZA|GRAU|SUPERIOR|CODIGO_REFERENCIAL|NATUREZA_SPED")
    
    # Processar cada conta
    for conta in contas:
        # Determinar código superior (pai)
        codigo_superior = ""
        if conta.get('parent_id'):
            # Buscar código da conta pai na lista
            conta_pai = next((c for c in contas if c['id'] == conta['parent_id']), None)
            if conta_pai:
                codigo_superior = conta_pai.get('codigo_speed') or conta_pai.get('codigo', '')
        
        # Tipo: S=Sintética, A=Analítica
        tipo = "S" if conta.get('tipo_conta') == 'sintetica' else "A"
        
        # Natureza: D=Devedora, C=Credora
        natureza = "D" if conta.get('natureza') == 'devedora' else "C"
        
        # Grau: nível da conta (1, 2, 3, 4...)
        grau = conta.get('nivel', 1)
        
        # Campos
        codigo = conta.get('codigo_speed') or conta.get('codigo', '')
        descricao = conta.get('descricao', '').replace('|', '-')  # Remove | para não quebrar formato
        codigo_referencial = conta.get('codigo_referencial', '')
        natureza_sped = conta.get('natureza_sped', '01')
        
        linha = f"{codigo}|{descricao}|{tipo}|{natureza}|{grau}|{codigo_superior}|{codigo_referencial}|{natureza_sped}"
        linhas.append(linha)
    
    return "\n".join(linhas)


def exportar_plano_contas_referencial(contas: List[Dict]) -> str:
    """
    Exporta apenas mapeamento com Referencial Contábil (para SPED)
    
    Formato: CODIGO_INTERNO|CODIGO_REFERENCIAL|NATUREZA_SPED
    
    Args:
        contas: Lista de dicionários com dados das contas
        
    Returns:
        String no formato CSV para conferência
    """
    linhas = []
    
    # Cabeçalho
    linhas.append("CODIGO_INTERNO;DESCRICAO;CODIGO_SPEED;CODIGO_REFERENCIAL;NATUREZA_SPED")
    
    # Processar cada conta
    for conta in contas:
        if conta.get('codigo_referencial') or conta.get('codigo_speed'):
            codigo_interno = conta.get('codigo', '')
            descricao = conta.get('descricao', '').replace(';', ',')
            codigo_speed = conta.get('codigo_speed', '')
            codigo_referencial = conta.get('codigo_referencial', '')
            natureza_sped = conta.get('natureza_sped', '01')
            
            linha = f"{codigo_interno};{descricao};{codigo_speed};{codigo_referencial};{natureza_sped}"
            linhas.append(linha)
    
    return "\n".join(linhas)


def validar_codigo_speed(codigo: str) -> tuple:
    """
    Valida formato de código Speed
    
    Args:
        codigo: Código a validar
        
    Returns:
        (valido: bool, mensagem: str)
    """
    if not codigo:
        return True, "OK"
    
    # Validações básicas
    if not codigo.replace('.', '').replace('-', '').isdigit():
        return False, "Código deve conter apenas números, pontos e hífens"
    
    # Verificar estrutura hierárquica (ex: 1.1.01.001)
    partes = codigo.split('.')
    if len(partes) > 6:
        return False, "Máximo de 6 níveis hierárquicos"
    
    return True, "OK"


def validar_codigo_referencial(codigo: str) -> tuple:
    """
    Valida formato de código do Referencial Contábil RFB
    
    Args:
        codigo: Código a validar
        
    Returns:
        (valido: bool, mensagem: str)
    """
    if not codigo:
        return True, "OK"
    
    # Formato esperado: X.XX.XX.XX.XX (5 níveis)
    partes = codigo.split('.')
    
    if len(partes) != 5:
        return False, "Referencial deve ter 5 níveis (ex: 1.01.01.01.01)"
    
    # Primeiro nível: 1 dígito
    if len(partes[0]) != 1 or not partes[0].isdigit():
        return False, "Primeiro nível deve ser 1 dígito (1-7)"
    
    # Demais níveis: 2 dígitos
    for i in range(1, 5):
        if len(partes[i]) != 2 or not partes[i].isdigit():
            return False, f"Nível {i+1} deve ter 2 dígitos"
    
    return True, "OK"


def gerar_mapeamento_automatico(conta: Dict) -> Dict:
    """
    Sugere códigos Speed e Referencial baseado no código e classificação
    
    Args:
        conta: Dicionário com dados da conta
        
    Returns:
        Dicionário com sugestões: {codigo_speed, codigo_referencial, natureza_sped}
    """
    codigo = conta.get('codigo', '')
    classificacao = conta.get('classificacao', '')
    
    sugestao = {
        'codigo_speed': codigo,  # Por padrão, usa o mesmo código
        'codigo_referencial': '',
        'natureza_sped': '01'  # Padrão: Ativo
    }
    
    # Determinar natureza_sped baseada na classificação
    mapeamento_natureza = {
        'ativo': '01',
        'passivo': '02',
        'patrimonio_liquido': '03',
        'receita': '04',
        'despesa': '05',
        'compensacao': '09'
    }
    
    sugestao['natureza_sped'] = mapeamento_natureza.get(classificacao, '09')
    
    # Tentar mapear para Referencial Contábil (exemplos básicos)
    if codigo.startswith('1.1.01'):  # Caixa e Bancos
        sugestao['codigo_referencial'] = '1.01.01.01.00'
    elif codigo.startswith('1.1.02'):  # Clientes
        sugestao['codigo_referencial'] = '1.01.03.01.00'
    elif codigo.startswith('2.1.01'):  # Fornecedores
        sugestao['codigo_referencial'] = '2.01.04.01.00'
    elif codigo.startswith('3'):  # Patrimônio Líquido
        sugestao['codigo_referencial'] = '3.01.01.00.00'
    elif codigo.startswith('4'):  # Receitas
        sugestao['codigo_referencial'] = '4.01.01.00.00'
    elif codigo.startswith('5') or codigo.startswith('6'):  # Custos/Despesas
        sugestao['codigo_referencial'] = '5.01.01.00.00'
    
    return sugestao


def estatisticas_mapeamento(contas: List[Dict]) -> Dict:
    """
    Retorna estatísticas do mapeamento Speed/Referencial
    
    Args:
        contas: Lista de contas
        
    Returns:
        Dicionário com estatísticas
    """
    total = len(contas)
    com_speed = sum(1 for c in contas if c.get('codigo_speed'))
    com_referencial = sum(1 for c in contas if c.get('codigo_referencial'))
    completo = sum(1 for c in contas if c.get('codigo_speed') and c.get('codigo_referencial'))
    
    return {
        'total_contas': total,
        'com_codigo_speed': com_speed,
        'percentual_speed': round((com_speed / total * 100) if total > 0 else 0, 1),
        'com_codigo_referencial': com_referencial,
        'percentual_referencial': round((com_referencial / total * 100) if total > 0 else 0, 1),
        'mapeamento_completo': completo,
        'percentual_completo': round((completo / total * 100) if total > 0 else 0, 1)
    }


# ============================================================================
# EXPORTAÇÃO DE LANÇAMENTOS CONTÁBEIS - FASE 2
# ============================================================================

def exportar_lancamentos_speed(lancamentos: List[Dict]) -> str:
    """
    Exporta lançamentos contábeis no formato TXT para Speed Contábil
    
    Formato: TIPO|DATA|NUMERO|HISTORICO|CONTA_DEBITO|VALOR_DEBITO|CONTA_CREDITO|VALOR_CREDITO
    
    Args:
        lancamentos: Lista de dicionários com lançamentos e seus itens
        
    Returns:
        String no formato TXT para importação no Speed
    """
    linhas = []
    
    # Cabeçalho
    linhas.append("TIPO|DATA|NUMERO|HISTORICO|CONTA_DEBITO|VALOR_DEBITO|CONTA_CREDITO|VALOR_CREDITO")
    
    # Processar cada lançamento
    for lanc in lancamentos:
        # Agrupar itens por tipo
        debitos = [i for i in lanc.get('itens', []) if i['tipo'] == 'debito']
        creditos = [i for i in lanc.get('itens', []) if i['tipo'] == 'credito']
        
        # Formatar data
        data_lancamento = lanc.get('data_lancamento', '')
        if isinstance(data_lancamento, str):
            try:
                data_obj = datetime.fromisoformat(data_lancamento.split('T')[0])
                data_formatada = data_obj.strftime('%d/%m/%Y')
            except:
                data_formatada = data_lancamento
        else:
            data_formatada = data_lancamento.strftime('%d/%m/%Y') if data_lancamento else ''
        
        numero = lanc.get('numero_lancamento', '')
        historico = lanc.get('historico', '').replace('|', '-').replace('\n', ' ')
        
        # Se houver apenas 1 débito e 1 crédito (lançamento simples)
        if len(debitos) == 1 and len(creditos) == 1:
            deb = debitos[0]
            cred = creditos[0]
            
            linha = (
                f"L|{data_formatada}|{numero}|{historico}|"
                f"{deb['conta_codigo']}|{deb['valor']:.2f}|"
                f"{cred['conta_codigo']}|{cred['valor']:.2f}"
            )
            linhas.append(linha)
        
        # Lançamento composto (múltiplos débitos ou créditos)
        else:
            # Linha principal com totais
            total_debito = sum(d['valor'] for d in debitos)
            total_credito = sum(c['valor'] for c in creditos)
            
            linha_principal = (
                f"LC|{data_formatada}|{numero}|{historico}|"
                f"DIVERSOS|{total_debito:.2f}|DIVERSOS|{total_credito:.2f}"
            )
            linhas.append(linha_principal)
            
            # Linhas de detalhamento (débitos)
            for deb in debitos:
                hist_complementar = deb.get('historico_complementar', '')
                hist_item = f"{historico} - {hist_complementar}" if hist_complementar else historico
                hist_item = hist_item.replace('|', '-').replace('\n', ' ')
                
                linha_deb = (
                    f"D|{data_formatada}|{numero}|{hist_item}|"
                    f"{deb['conta_codigo']}|{deb['valor']:.2f}||"
                )
                linhas.append(linha_deb)
            
            # Linhas de detalhamento (créditos)
            for cred in creditos:
                hist_complementar = cred.get('historico_complementar', '')
                hist_item = f"{historico} - {hist_complementar}" if hist_complementar else historico
                hist_item = hist_item.replace('|', '-').replace('\n', ' ')
                
                linha_cred = (
                    f"C|{data_formatada}|{numero}|{hist_item}|"
                    f"||{cred['conta_codigo']}|{cred['valor']:.2f}"
                )
                linhas.append(linha_cred)
    
    return "\n".join(linhas)


def exportar_lancamentos_speed_xml(lancamentos: List[Dict]) -> str:
    """
    Exporta lançamentos no formato XML para Speed (alternativa ao TXT)
    
    Args:
        lancamentos: Lista de dicionários com lançamentos e seus itens
        
    Returns:
        String no formato XML para importação no Speed
    """
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<LancamentosContabeis>')
    
    for lanc in lancamentos:
        data_lancamento = lanc.get('data_lancamento', '')
        if isinstance(data_lancamento, str):
            try:
                data_obj = datetime.fromisoformat(data_lancamento.split('T')[0])
                data_formatada = data_obj.strftime('%d/%m/%Y')
            except:
                data_formatada = data_lancamento
        else:
            data_formatada = data_lancamento.strftime('%d/%m/%Y') if data_lancamento else ''
        
        numero = lanc.get('numero_lancamento', '')
        historico = lanc.get('historico', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        valor_total = lanc.get('valor_total', 0)
        
        xml_lines.append(f'  <Lancamento>')
        xml_lines.append(f'    <Numero>{numero}</Numero>')
        xml_lines.append(f'    <Data>{data_formatada}</Data>')
        xml_lines.append(f'    <Historico>{historico}</Historico>')
        xml_lines.append(f'    <ValorTotal>{valor_total:.2f}</ValorTotal>')
        xml_lines.append(f'    <Itens>')
        
        for item in lanc.get('itens', []):
            tipo = item['tipo'].upper()
            conta_codigo = item['conta_codigo']
            conta_nome = item.get('conta_nome', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            valor = item['valor']
            hist_comp = item.get('historico_complementar', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            xml_lines.append(f'      <Item>')
            xml_lines.append(f'        <Tipo>{tipo}</Tipo>')
            xml_lines.append(f'        <ContaCodigo>{conta_codigo}</ContaCodigo>')
            xml_lines.append(f'        <ContaNome>{conta_nome}</ContaNome>')
            xml_lines.append(f'        <Valor>{valor:.2f}</Valor>')
            if hist_comp:
                xml_lines.append(f'        <HistoricoComplementar>{hist_comp}</HistoricoComplementar>')
            xml_lines.append(f'      </Item>')
        
        xml_lines.append(f'    </Itens>')
        xml_lines.append(f'  </Lancamento>')
    
    xml_lines.append('</LancamentosContabeis>')
    
    return '\n'.join(xml_lines)


def validar_lancamentos_exportacao(lancamentos: List[Dict]) -> Dict:
    """
    Valida lançamentos antes da exportação para Speed
    
    Args:
        lancamentos: Lista de lançamentos a validar
        
    Returns:
        Dicionário com resultado da validação e erros encontrados
    """
    erros = []
    avisos = []
    
    for idx, lanc in enumerate(lancamentos):
        num_lanc = lanc.get('numero_lancamento', f'#{idx+1}')
        
        # Validar partidas dobradas
        itens = lanc.get('itens', [])
        if not itens or len(itens) < 2:
            erros.append(f"{num_lanc}: Lançamento deve ter pelo menos 2 itens")
            continue
        
        total_debito = sum(i['valor'] for i in itens if i['tipo'] == 'debito')
        total_credito = sum(i['valor'] for i in itens if i['tipo'] == 'credito')
        
        if abs(total_debito - total_credito) > 0.01:  # Tolerância de 1 centavo
            erros.append(
                f"{num_lanc}: Partidas não estão dobradas - "
                f"Débito: {total_debito:.2f}, Crédito: {total_credito:.2f}"
            )
        
        # Validar códigos das contas
        for item in itens:
            if not item.get('conta_codigo'):
                avisos.append(f"{num_lanc}: Item sem código de conta")
            
            # Avisar se não tem código Speed mapeado
            conta_codigo = item.get('conta_codigo', '')
            if not conta_codigo or conta_codigo == 'N/A':
                avisos.append(
                    f"{num_lanc}: Conta '{item.get('conta_nome', '...')}' "
                    f"não possui código Speed mapeado"
                )
        
        # Validar data
        if not lanc.get('data_lancamento'):
            erros.append(f"{num_lanc}: Data do lançamento não informada")
        
        # Validar histórico
        if not lanc.get('historico'):
            avisos.append(f"{num_lanc}: Histórico vazio")
    
    total = len(lancamentos)
    validos = total - len([e for e in erros if ':' in e])
    
    return {
        'valido': len(erros) == 0,
        'total_lancamentos': total,
        'lancamentos_validos': validos,
        'total_erros': len(erros),
        'total_avisos': len(avisos),
        'erros': erros,
        'avisos': avisos
    }


# ============================================================================
# EXPORTAÇÃO DE RELATÓRIOS CONTÁBEIS - FASE 3
# ============================================================================

def exportar_balancete_speed_txt(balancete_data: Dict) -> str:
    """
    Exporta Balancete de Verificação no formato TXT para Speed
    
    Formato: CODIGO|DESCRICAO|SALDO_ANT|TIPO_SALDO_ANT|DEBITO|CREDITO|SALDO_ATUAL|TIPO_SALDO_ATUAL
    
    Args:
        balancete_data: Dicionário com dados do balancete
        
    Returns:
        String no formato TXT para importação no Speed
    """
    linhas = []
    
    # Cabeçalho
    periodo = balancete_data.get('periodo', {})
    linhas.append(f"# BALANCETE DE VERIFICAÇÃO")
    linhas.append(f"# Período: {periodo.get('data_inicio')} a {periodo.get('data_fim')}")
    linhas.append(f"# Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    linhas.append("")
    linhas.append("CODIGO|DESCRICAO|SALDO_ANTERIOR|TIPO_SALDO_ANT|DEBITO_PERIODO|CREDITO_PERIODO|SALDO_ATUAL|TIPO_SALDO_ATUAL")
    
    # Itens do balancete
    for item in balancete_data.get('balancete', []):
        linha = (
            f"{item['codigo']}|"
            f"{item['descricao']}|"
            f"{item['saldo_anterior']:.2f}|"
            f"{item['tipo_saldo_anterior'][0].upper()}|"  # D ou C
            f"{item['debito_periodo']:.2f}|"
            f"{item['credito_periodo']:.2f}|"
            f"{item['saldo_atual']:.2f}|"
            f"{item['tipo_saldo_atual'][0].upper()}"
        )
        linhas.append(linha)
    
    # Totais
    totais = balancete_data.get('totais', {})
    linhas.append("")
    linhas.append(f"TOTAL DÉBITOS|{totais.get('total_debito_periodo', 0):.2f}")
    linhas.append(f"TOTAL CRÉDITOS|{totais.get('total_credito_periodo', 0):.2f}")
    linhas.append(f"TOTAL SALDO DEVEDOR|{totais.get('total_saldo_devedor', 0):.2f}")
    linhas.append(f"TOTAL SALDO CREDOR|{totais.get('total_saldo_credor', 0):.2f}")
    
    return "\n".join(linhas)


def exportar_balancete_speed_csv(balancete_data: Dict) -> str:
    """
    Exporta Balancete em formato CSV (Excel)
    
    Args:
        balancete_data: Dicionário com dados do balancete
        
    Returns:
        String no formato CSV
    """
    linhas = []
    
    # Cabeçalho CSV
    linhas.append("Código;Descrição;Saldo Anterior;Tipo;Débito Período;Crédito Período;Saldo Atual;Tipo")
    
    # Itens
    for item in balancete_data.get('balancete', []):
        linha = (
            f"{item['codigo']};"
            f"{item['descricao']};"
            f"{item['saldo_anterior']:.2f};"
            f"{item['tipo_saldo_anterior']};"
            f"{item['debito_periodo']:.2f};"
            f"{item['credito_periodo']:.2f};"
            f"{item['saldo_atual']:.2f};"
            f"{item['tipo_saldo_atual']}"
        )
        linhas.append(linha)
    
    # Totais
    totais = balancete_data.get('totais', {})
    linhas.append("")
    linhas.append(f"TOTAL DÉBITOS;;;{totais.get('total_debito_periodo', 0):.2f};;;")
    linhas.append(f"TOTAL CRÉDITOS;;;;{totais.get('total_credito_periodo', 0):.2f};;")
    
    return "\n".join(linhas)


def exportar_dre_speed_txt(dre_data: Dict) -> str:
    """
    Exporta DRE no formato TXT para Speed
    
    Args:
        dre_data: Dicionário com dados da DRE
        
    Returns:
        String no formato TXT estruturado
    """
    linhas = []
    dre = dre_data.get('dre', {})
    periodo = dre_data.get('periodo', {})
    indicadores = dre_data.get('indicadores', {})
    
    # Cabeçalho
    linhas.append("=" * 80)
    linhas.append("DEMONSTRATIVO DE RESULTADO DO EXERCÍCIO - DRE")
    linhas.append(f"Período: {periodo.get('data_inicio')} a {periodo.get('data_fim')}")
    linhas.append("=" * 80)
    linhas.append("")
    
    # RECEITAS
    linhas.append("RECEITA BRUTA")
    for item in dre.get('receitas', {}).get('itens', []):
        linhas.append(f"  {item['codigo']} - {item['descricao']}: R$ {item['valor']:,.2f}")
    linhas.append(f"TOTAL RECEITA BRUTA: R$ {dre.get('receitas', {}).get('total', 0):,.2f}")
    linhas.append("")
    
    # CUSTOS
    linhas.append("(-) CUSTOS DOS SERVIÇOS/PRODUTOS")
    for item in dre.get('custos', {}).get('itens', []):
        linhas.append(f"  {item['codigo']} - {item['descricao']}: R$ ({item['valor']:,.2f})")
    linhas.append(f"TOTAL CUSTOS: R$ ({dre.get('custos', {}).get('total', 0):,.2f})")
    linhas.append("")
    
    # LUCRO BRUTO
    linhas.append("=" * 80)
    linhas.append(f"LUCRO BRUTO: R$ {dre.get('lucro_bruto', 0):,.2f}")
    linhas.append(f"Margem Bruta: {indicadores.get('margem_bruta', 0):.2f}%")
    linhas.append("=" * 80)
    linhas.append("")
    
    # DESPESAS OPERACIONAIS
    linhas.append("(-) DESPESAS OPERACIONAIS")
    for item in dre.get('despesas_operacionais', {}).get('itens', []):
        linhas.append(f"  {item['codigo']} - {item['descricao']}: R$ ({item['valor']:,.2f})")
    linhas.append(f"TOTAL DESPESAS OPERACIONAIS: R$ ({dre.get('despesas_operacionais', {}).get('total', 0):,.2f})")
    linhas.append("")
    
    # RESULTADO OPERACIONAL
    linhas.append("=" * 80)
    linhas.append(f"RESULTADO OPERACIONAL: R$ {dre.get('resultado_operacional', 0):,.2f}")
    linhas.append(f"Margem Operacional: {indicadores.get('margem_operacional', 0):.2f}%")
    linhas.append("=" * 80)
    linhas.append("")
    
    # OUTRAS RECEITAS/DESPESAS
    if dre.get('outras_receitas_despesas', {}).get('itens'):
        linhas.append("(-) OUTRAS RECEITAS/DESPESAS")
        for item in dre.get('outras_receitas_despesas', {}).get('itens', []):
            linhas.append(f"  {item['codigo']} - {item['descricao']}: R$ ({item['valor']:,.2f})")
        linhas.append(f"TOTAL OUTRAS: R$ ({dre.get('outras_receitas_despesas', {}).get('total', 0):,.2f})")
        linhas.append("")
    
    # RESULTADO LÍQUIDO
    linhas.append("=" * 80)
    linhas.append(f"RESULTADO LÍQUIDO DO PERÍODO: R$ {dre.get('resultado_liquido', 0):,.2f}")
    linhas.append(f"Margem Líquida: {indicadores.get('margem_liquida', 0):.2f}%")
    linhas.append("=" * 80)
    
    return "\n".join(linhas)


def exportar_balanco_patrimonial_speed_txt(balanco_data: Dict) -> str:
    """
    Exporta Balanço Patrimonial no formato TXT para Speed
    
    Args:
        balanco_data: Dicionário com dados do balanço
        
    Returns:
        String no formato TXT estruturado
    """
    linhas = []
    balanco = balanco_data.get('balanco', {})
    data_ref = balanco_data.get('data_referencia', '')
    validacao = balanco_data.get('validacao', {})
    
    # Cabeçalho
    linhas.append("=" * 100)
    linhas.append("BALANÇO PATRIMONIAL")
    linhas.append(f"Data de Referência: {data_ref}")
    linhas.append("=" * 100)
    linhas.append("")
    
    # ATIVO
    ativo = balanco.get('ativo', {})
    linhas.append("ATIVO" + " " * 70 + f"R$ {ativo.get('total', 0):,.2f}")
    linhas.append("-" * 100)
    
    # Ativo Circulante
    linhas.append("ATIVO CIRCULANTE" + " " * 58 + f"R$ {ativo.get('circulante', {}).get('total', 0):,.2f}")
    for item in ativo.get('circulante', {}).get('itens', []):
        if item['saldo'] > 0:
            espacos = " " * (70 - len(f"  {item['codigo']} - {item['descricao']}"))
            linhas.append(f"  {item['codigo']} - {item['descricao']}{espacos}R$ {item['saldo']:,.2f}")
    linhas.append("")
    
    # Ativo Não Circulante
    if ativo.get('nao_circulante', {}).get('total', 0) > 0:
        linhas.append("ATIVO NÃO CIRCULANTE" + " " * 54 + f"R$ {ativo.get('nao_circulante', {}).get('total', 0):,.2f}")
        for item in ativo.get('nao_circulante', {}).get('itens', []):
            if item['saldo'] > 0:
                espacos = " " * (70 - len(f"  {item['codigo']} - {item['descricao']}"))
                linhas.append(f"  {item['codigo']} - {item['descricao']}{espacos}R$ {item['saldo']:,.2f}")
        linhas.append("")
    
    linhas.append("=" * 100)
    linhas.append("")
    
    # PASSIVO
    passivo = balanco.get('passivo', {})
    linhas.append("PASSIVO" + " " * 68 + f"R$ {passivo.get('total', 0):,.2f}")
    linhas.append("-" * 100)
    
    # Passivo Circulante
    linhas.append("PASSIVO CIRCULANTE" + " " * 56 + f"R$ {passivo.get('circulante', {}).get('total', 0):,.2f}")
    for item in passivo.get('circulante', {}).get('itens', []):
        if item['saldo'] > 0:
            espacos = " " * (70 - len(f"  {item['codigo']} - {item['descricao']}"))
            linhas.append(f"  {item['codigo']} - {item['descricao']}{espacos}R$ {item['saldo']:,.2f}")
    linhas.append("")
    
    # Passivo Não Circulante
    if passivo.get('nao_circulante', {}).get('total', 0) > 0:
        linhas.append("PASSIVO NÃO CIRCULANTE" + " " * 52 + f"R$ {passivo.get('nao_circulante', {}).get('total', 0):,.2f}")
        for item in passivo.get('nao_circulante', {}).get('itens', []):
            if item['saldo'] > 0:
                espacos = " " * (70 - len(f"  {item['codigo']} - {item['descricao']}"))
                linhas.append(f"  {item['codigo']} - {item['descricao']}{espacos}R$ {item['saldo']:,.2f}")
        linhas.append("")
    
    linhas.append("-" * 100)
    
    # PATRIMÔNIO LÍQUIDO
    pl = balanco.get('patrimonio_liquido', {})
    linhas.append("PATRIMÔNIO LÍQUIDO" + " " * 56 + f"R$ {pl.get('total', 0):,.2f}")
    for item in pl.get('itens', []):
        if item['saldo'] > 0:
            espacos = " " * (70 - len(f"  {item['codigo']} - {item['descricao']}"))
            linhas.append(f"  {item['codigo']} - {item['descricao']}{espacos}R$ {item['saldo']:,.2f}")
    linhas.append("")
    
    linhas.append("=" * 100)
    linhas.append(f"TOTAL PASSIVO + PL" + " " * 56 + f"R$ {balanco.get('total_passivo_pl', 0):,.2f}")
    linhas.append("=" * 100)
    linhas.append("")
    
    # Validação
    linhas.append("VALIDAÇÃO DO BALANÇO:")
    linhas.append(validacao.get('formula', ''))
    if validacao.get('balanco_fechado'):
        linhas.append("✅ Balanço fechado corretamente!")
    else:
        linhas.append(f"⚠️ Diferença encontrada: R$ {validacao.get('diferenca', 0):.2f}")
    
    return "\n".join(linhas)


def exportar_razao_contabil_speed_txt(razao_data: Dict) -> str:
    """
    Exporta Razão Contábil no formato TXT para Speed
    
    Args:
        razao_data: Dicionário com dados do razão
        
    Returns:
        String no formato TXT estruturado
    """
    linhas = []
    conta = razao_data.get('conta', {})
    periodo = razao_data.get('periodo', {})
    
    # Cabeçalho
    linhas.append("=" * 120)
    linhas.append("RAZÃO CONTÁBIL")
    linhas.append(f"Conta: {conta.get('codigo')} - {conta.get('descricao')}")
    linhas.append(f"Período: {periodo.get('data_inicio')} a {periodo.get('data_fim')}")
    linhas.append("=" * 120)
    linhas.append("")
    
    linhas.append(f"Saldo Anterior: R$ {razao_data.get('saldo_anterior', 0):,.2f}")
    linhas.append("")
    
    # Cabeçalho da tabela
    linhas.append(f"{'Data':<12} {'Nº Lançamento':<15} {'Histórico':<50} {'Débito':>15} {'Crédito':>15} {'Saldo':>15}")
    linhas.append("-" * 120)
    
    # Movimentações
    for mov in razao_data.get('movimentacoes', []):
        historico = mov['historico'][:48] + '..' if len(mov['historico']) > 50 else mov['historico']
        linha = (
            f"{mov['data']:<12} "
            f"{mov['numero_lancamento']:<15} "
            f"{historico:<50} "
            f"{mov['debito']:>15,.2f} "
            f"{mov['credito']:>15,.2f} "
            f"{mov['saldo']:>15,.2f}"
        )
        linhas.append(linha)
    
    linhas.append("-" * 120)
    linhas.append(f"Saldo Final: R$ {razao_data.get('saldo_atual', 0):,.2f}")
    linhas.append(f"Total de Movimentações: {razao_data.get('total_movimentacoes', 0)}")
    linhas.append("=" * 120)
    
    return "\n".join(linhas)


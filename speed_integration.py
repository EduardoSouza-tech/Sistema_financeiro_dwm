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

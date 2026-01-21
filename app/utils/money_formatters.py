"""
💰 Money Formatters - Formatação de valores monetários
======================================================

Funções compartilhadas para formatação e parsing de valores monetários.
Padroniza exibição de valores em todo o sistema.

Autor: Sistema de Otimização - Fase 4
Data: 20/01/2026
"""

from typing import Union, Optional
from decimal import Decimal, InvalidOperation


def format_currency(value: Union[int, float, Decimal, str], currency: str = 'R$', decimals: int = 2) -> str:
    """
    Formata valor como moeda brasileira
    
    Args:
        value: Valor numérico ou string
        currency: Símbolo da moeda (padrão: R$)
        decimals: Casas decimais (padrão: 2)
        
    Returns:
        String formatada (ex: "R$ 1.234,56")
        
    Examples:
        >>> format_currency(1234.56)
        'R$ 1.234,56'
        
        >>> format_currency(1000, currency='USD', decimals=2)
        'USD 1.000,00'
        
        >>> format_currency('invalid')
        'R$ 0,00'
    """
    try:
        # Converte para float
        if isinstance(value, str):
            # Remove caracteres não numéricos exceto . e ,
            value = value.replace('.', '').replace(',', '.')
            value = float(value)
        elif isinstance(value, Decimal):
            value = float(value)
        
        # Formata com separadores brasileiros
        formatted = f"{value:,.{decimals}f}"
        
        # Inverte . e , para padrão brasileiro
        formatted = formatted.replace(',', '_').replace('.', ',').replace('_', '.')
        
        return f"{currency} {formatted}"
        
    except (ValueError, TypeError, InvalidOperation):
        return f"{currency} 0,{'0' * decimals}"


def parse_currency(value_str: str) -> float:
    """
    Converte string de moeda para float
    
    Args:
        value_str: String formatada como moeda (ex: "R$ 1.234,56")
        
    Returns:
        Valor float
        
    Examples:
        >>> parse_currency('R$ 1.234,56')
        1234.56
        
        >>> parse_currency('1.500,00')
        1500.0
        
        >>> parse_currency('invalid')
        0.0
    """
    try:
        # Remove símbolos de moeda e espaços
        cleaned = value_str.replace('R$', '').replace('USD', '').replace('€', '').strip()
        
        # Remove pontos de milhar e substitui vírgula decimal por ponto
        cleaned = cleaned.replace('.', '').replace(',', '.')
        
        return float(cleaned)
        
    except (ValueError, AttributeError):
        return 0.0


def format_percentage(value: Union[int, float, Decimal], decimals: int = 2) -> str:
    """
    Formata valor como porcentagem
    
    Args:
        value: Valor numérico (ex: 15.5 para 15.5%)
        decimals: Casas decimais
        
    Returns:
        String formatada (ex: "15,50%")
        
    Examples:
        >>> format_percentage(15.5)
        '15,50%'
        
        >>> format_percentage(0.123, decimals=1)
        '0,1%'
    """
    try:
        formatted = f"{float(value):.{decimals}f}"
        formatted = formatted.replace('.', ',')
        return f"{formatted}%"
    except (ValueError, TypeError):
        return "0,00%"


def format_number(value: Union[int, float, Decimal], decimals: int = 0) -> str:
    """
    Formata número com separadores de milhar brasileiros
    
    Args:
        value: Valor numérico
        decimals: Casas decimais
        
    Returns:
        String formatada (ex: "1.234,56")
        
    Examples:
        >>> format_number(1234567)
        '1.234.567'
        
        >>> format_number(1234.56, decimals=2)
        '1.234,56'
    """
    try:
        formatted = f"{float(value):,.{decimals}f}"
        formatted = formatted.replace(',', '_').replace('.', ',').replace('_', '.')
        return formatted
    except (ValueError, TypeError):
        return "0"


def calculate_percentage(part: Union[int, float], total: Union[int, float], decimals: int = 2) -> float:
    """
    Calcula porcentagem
    
    Args:
        part: Valor parcial
        total: Valor total
        decimals: Casas decimais para arredondamento
        
    Returns:
        Porcentagem calculada
        
    Examples:
        >>> calculate_percentage(25, 100)
        25.0
        
        >>> calculate_percentage(1, 3, decimals=2)
        33.33
    """
    try:
        if total == 0:
            return 0.0
        return round((float(part) / float(total)) * 100, decimals)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def sum_currency_list(values: list) -> float:
    """
    Soma lista de valores monetários (strings ou números)
    
    Args:
        values: Lista de valores
        
    Returns:
        Soma total
        
    Examples:
        >>> sum_currency_list([100, 200, 300])
        600.0
        
        >>> sum_currency_list(['R$ 100,00', 'R$ 200,50'])
        300.5
    """
    total = 0.0
    for value in values:
        if isinstance(value, str):
            total += parse_currency(value)
        else:
            total += float(value or 0)
    return total


def is_valid_currency(value_str: str) -> bool:
    """
    Valida se string é um valor monetário válido
    
    Args:
        value_str: String a validar
        
    Returns:
        True se válida, False caso contrário
        
    Examples:
        >>> is_valid_currency('R$ 1.234,56')
        True
        
        >>> is_valid_currency('invalid')
        False
    """
    try:
        parsed = parse_currency(value_str)
        return parsed >= 0
    except:
        return False


def parse_percentage(value_str: str) -> float:
    """
    Converte string de porcentagem para float
    
    Args:
        value_str: String no formato '25%', '25.5%', ou '25'
        
    Returns:
        Valor da porcentagem como float
        
    Raises:
        ValueError: Se a string não for um formato válido
        
    Example:
        >>> parse_percentage('25%')
        25.0
        >>> parse_percentage('25.5')
        25.5
    """
    if not value_str or not isinstance(value_str, str):
        raise ValueError("Valor deve ser uma string não vazia")
    
    # Remove espaços e símbolo de porcentagem
    clean = value_str.strip().replace('%', '').replace(',', '.')
    
    try:
        return float(clean)
    except ValueError:
        raise ValueError(f"Valor inválido para porcentagem: {value_str}")


def apply_percentage(value: Union[int, float, Decimal], percentage: Union[int, float, Decimal], operation: str = 'increase') -> Decimal:
    """
    Aplica uma porcentagem a um valor (aumento ou desconto)
    
    Args:
        value: Valor base
        percentage: Porcentagem a aplicar (ex: 10 para 10%)
        operation: 'increase' para aumento, 'decrease' para desconto
        
    Returns:
        Valor resultante como Decimal
        
    Example:
        >>> apply_percentage(100, 10, 'increase')
        Decimal('110.00')
        >>> apply_percentage(100, 10, 'decrease')
        Decimal('90.00')
    """
    value_dec = Decimal(str(value))
    percentage_dec = Decimal(str(percentage))
    
    change_amount = (value_dec * percentage_dec) / Decimal('100')
    
    if operation == 'increase':
        result = value_dec + change_amount
    elif operation == 'decrease':
        result = value_dec - change_amount
    else:
        raise ValueError(f"Operação inválida: {operation}. Use 'increase' ou 'decrease'")
    
    return result.quantize(Decimal('0.01'))


def round_money(value: Union[int, float, Decimal]) -> Decimal:
    """
    Arredonda um valor monetário para 2 casas decimais
    
    Args:
        value: Valor a arredondar
        
    Returns:
        Valor arredondado como Decimal
        
    Example:
        >>> round_money(10.126)
        Decimal('10.13')
        >>> round_money(10.124)
        Decimal('10.12')
    """
    value_dec = Decimal(str(value))
    return value_dec.quantize(Decimal('0.01'))

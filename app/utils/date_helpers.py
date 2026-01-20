"""
📅 Date Helpers - Utilities para manipulação de datas
======================================================

Funções compartilhadas para parsing, formatação e conversão de datas.
Reduz duplicação de código e padroniza tratamento de datas no sistema.

Autor: Sistema de Otimização - Fase 4
Data: 20/01/2026
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union


def parse_date(date_str: Optional[str], default: Optional[Union[date, datetime]] = None) -> Union[date, datetime, None]:
    """
    Faz parse de string para date/datetime com fallback para default
    
    Args:
        date_str: String no formato ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)
        default: Valor padrão se parsing falhar ou date_str for None
        
    Returns:
        date/datetime parseado ou default
        
    Examples:
        >>> parse_date('2026-01-20')
        date(2026, 1, 20)
        
        >>> parse_date(None, datetime.now())
        datetime(...)
        
        >>> parse_date('invalid', date.today())
        date(...)
    """
    if not date_str:
        return default or datetime.now()
    
    try:
        # Tenta ISO format com datetime
        if 'T' in date_str or len(date_str) > 10:
            return datetime.fromisoformat(date_str)
        
        # Tenta formato de data simples
        return datetime.strptime(date_str, '%Y-%m-%d').date()
        
    except (ValueError, AttributeError):
        return default or datetime.now()


def format_date_br(date_obj: Union[date, datetime, str], format_type: str = 'short') -> str:
    """
    Formata data no padrão brasileiro
    
    Args:
        date_obj: date, datetime ou string ISO
        format_type: 'short' (dd/mm/yyyy), 'long' (dd de MMM de yyyy), 'month' (MMM/YY)
        
    Returns:
        String formatada
        
    Examples:
        >>> format_date_br(date(2026, 1, 20), 'short')
        '20/01/2026'
        
        >>> format_date_br(date(2026, 1, 20), 'long')
        '20 de Jan de 2026'
        
        >>> format_date_br(date(2026, 1, 20), 'month')
        'Jan/26'
    """
    if isinstance(date_obj, str):
        date_obj = parse_date(date_obj)
    
    if not date_obj:
        return ''
    
    formats = {
        'short': '%d/%m/%Y',
        'long': '%d de %b de %Y',
        'month': '%b/%y',
        'monthfull': '%b/%Y'
    }
    
    return date_obj.strftime(formats.get(format_type, '%d/%m/%Y'))


def format_date_iso(date_obj: Union[date, datetime, str]) -> str:
    """
    Formata data no formato ISO (YYYY-MM-DD)
    
    Args:
        date_obj: date, datetime ou string
        
    Returns:
        String no formato ISO
        
    Examples:
        >>> format_date_iso(date(2026, 1, 20))
        '2026-01-20'
    """
    if isinstance(date_obj, str):
        date_obj = parse_date(date_obj)
    
    if not date_obj:
        return ''
    
    if isinstance(date_obj, datetime):
        return date_obj.date().isoformat()
    
    return date_obj.isoformat()


def format_datetime_br(dt: Union[datetime, str], include_time: bool = True) -> str:
    """
    Formata datetime no padrão brasileiro
    
    Args:
        dt: datetime ou string ISO
        include_time: Se True, inclui horas (dd/mm/yyyy HH:MM)
        
    Returns:
        String formatada
        
    Examples:
        >>> format_datetime_br(datetime(2026, 1, 20, 14, 30))
        '20/01/2026 14:30'
        
        >>> format_datetime_br(datetime(2026, 1, 20, 14, 30), include_time=False)
        '20/01/2026'
    """
    if isinstance(dt, str):
        dt = parse_date(dt)
    
    if not dt:
        return ''
    
    if include_time:
        return dt.strftime('%d/%m/%Y %H:%M')
    
    return dt.strftime('%d/%m/%Y')


def get_current_date_br() -> str:
    """
    Retorna data atual formatada em português
    
    Returns:
        String no formato dd/mm/yyyy
    """
    return datetime.now().strftime('%d/%m/%Y')


def get_current_datetime_br() -> str:
    """
    Retorna datetime atual formatado em português
    
    Returns:
        String no formato dd/mm/yyyy HH:MM:SS
    """
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


def get_current_date_filename() -> str:
    """
    Retorna data atual para uso em nomes de arquivo
    
    Returns:
        String no formato YYYYMMDD
        
    Examples:
        >>> get_current_date_filename()
        '20260120'
    """
    return datetime.now().strftime('%Y%m%d')


def add_months(date_obj: date, months: int) -> date:
    """
    Adiciona meses a uma data
    
    Args:
        date_obj: Data base
        months: Número de meses a adicionar (pode ser negativo)
        
    Returns:
        Nova data
        
    Examples:
        >>> add_months(date(2026, 1, 15), 2)
        date(2026, 3, 15)
    """
    month = date_obj.month - 1 + months
    year = date_obj.year + month // 12
    month = month % 12 + 1
    day = min(date_obj.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def get_month_range(year: int, month: int) -> tuple[date, date]:
    """
    Retorna primeiro e último dia de um mês
    
    Args:
        year: Ano
        month: Mês (1-12)
        
    Returns:
        Tupla (primeiro_dia, ultimo_dia)
        
    Examples:
        >>> get_month_range(2026, 2)
        (date(2026, 2, 1), date(2026, 2, 28))
    """
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    return first_day, last_day


def is_valid_date_string(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """
    Verifica se string é uma data válida
    
    Args:
        date_str: String a validar
        format: Formato esperado (padrão: ISO)
        
    Returns:
        True se válida, False caso contrário
        
    Examples:
        >>> is_valid_date_string('2026-01-20')
        True
        
        >>> is_valid_date_string('invalid')
        False
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except (ValueError, TypeError):
        return False


def days_between(date1: Union[date, datetime, str], date2: Union[date, datetime, str]) -> int:
    """
    Calcula dias entre duas datas
    
    Args:
        date1: Primeira data
        date2: Segunda data
        
    Returns:
        Número de dias (positivo se date2 > date1)
        
    Examples:
        >>> days_between('2026-01-01', '2026-01-10')
        9
    """
    if isinstance(date1, str):
        date1 = parse_date(date1)
    if isinstance(date2, str):
        date2 = parse_date(date2)
    
    if isinstance(date1, datetime):
        date1 = date1.date()
    if isinstance(date2, datetime):
        date2 = date2.date()
    
    return (date2 - date1).days

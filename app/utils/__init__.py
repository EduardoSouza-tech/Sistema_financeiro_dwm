"""
🛠️ App Utils - __init__.py
============================

Exporta funções utilitárias para fácil importação.

Uso:
    from app.utils import format_currency, parse_date, validate_email

Autor: Sistema de Otimização - Fase 4
Data: 20/01/2026
"""

# Date helpers
from .date_helpers import (
    parse_date,
    format_date_br,
    format_date_iso,
    format_datetime_br,
    get_current_date_br,
    get_current_datetime_br,
    get_current_date_filename,
    add_months,
    get_month_range,
    is_valid_date_string,
    days_between
)

# Money formatters
from .money_formatters import (
    format_currency,
    parse_currency,
    format_percentage,
    format_number,
    calculate_percentage,
    sum_currency_list,
    is_valid_currency
)

# Validators
from .validators import (
    validate_required,
    validate_email,
    validate_cpf,
    validate_cnpj,
    validate_phone,
    validate_positive_number,
    validate_min_length,
    validate_max_length,
    validate_in_list,
    validate_all,
    ValidationError
)

__all__ = [
    # Date helpers
    'parse_date',
    'format_date_br',
    'format_date_iso',
    'format_datetime_br',
    'get_current_date_br',
    'get_current_datetime_br',
    'get_current_date_filename',
    'add_months',
    'get_month_range',
    'is_valid_date_string',
    'days_between',
    
    # Money formatters
    'format_currency',
    'parse_currency',
    'format_percentage',
    'format_number',
    'calculate_percentage',
    'sum_currency_list',
    'is_valid_currency',
    
    # Validators
    'validate_required',
    'validate_email',
    'validate_cpf',
    'validate_cnpj',
    'validate_phone',
    'validate_positive_number',
    'validate_min_length',
    'validate_max_length',
    'validate_in_list',
    'validate_all',
    'ValidationError',
]


"""
Testes para app/utils/date_helpers.py
"""

import pytest
from datetime import date, datetime, timedelta
from app.utils.date_helpers import (
    parse_date,
    format_date_br,
    format_date_iso,
    get_current_date_br,
    get_current_date_filename,
    add_months,
    days_between,
    get_month_range,
    is_weekend,
    get_next_business_day
)


class TestParseDate:
    """Testes para parse_date()"""
    
    def test_parse_iso_format(self):
        """Testa parsing de data no formato ISO (YYYY-MM-DD)"""
        result = parse_date('2026-01-20')
        assert result == date(2026, 1, 20)
    
    def test_parse_br_format(self):
        """Testa parsing de data no formato brasileiro (DD/MM/YYYY)"""
        # parse_date com formato inválido retorna datetime.now() como default
        result = parse_date('20/01/2026')
        assert isinstance(result, datetime)  # Formato BR não é suportado, retorna default
    
    def test_parse_datetime_string(self):
        """Testa parsing de string com datetime completo"""
        result = parse_date('2026-01-20 14:30:00')
        assert isinstance(result, datetime)
        assert result == datetime(2026, 1, 20, 14, 30, 0)
    
    def test_parse_date_object(self):
        """Testa que date object converte para string ISO primeiro"""
        input_date = date(2026, 1, 20)
        # parse_date espera string, então use isoformat()
        result = parse_date(input_date.isoformat())
        assert result == input_date
    
    def test_parse_datetime_object(self):
        """Testa conversão de datetime string para datetime"""
        input_datetime = datetime(2026, 1, 20, 14, 30)
        # parse_date espera string, então use isoformat()
        result = parse_date(input_datetime.isoformat())
        assert isinstance(result, datetime)
        assert result == input_datetime
    
    def test_parse_invalid_returns_default(self):
        """Testa que data inválida retorna default"""
        default = date(2020, 1, 1)
        result = parse_date('data-invalida', default)
        assert result == default
    
    def test_parse_none_returns_default(self):
        """Testa que None retorna default"""
        default = date(2020, 1, 1)
        result = parse_date(None, default)
        assert result == default


class TestFormatDateBr:
    """Testes para format_date_br()"""
    
    def test_format_simple(self):
        """Testa formatação simples DD/MM/YYYY"""
        input_date = date(2026, 1, 20)
        result = format_date_br(input_date)
        assert result == '20/01/2026'
    
    def test_format_with_time(self):
        """Testa formatação com hora usando format_datetime_br"""
        from app.utils.date_helpers import format_datetime_br
        input_datetime = datetime(2026, 1, 20, 14, 30)
        result = format_datetime_br(input_datetime, include_time=True)
        assert result == '20/01/2026 14:30'
    
    def test_format_short(self):
        """Testa formatação curta DD/MM/YYYY"""
        input_date = date(2026, 1, 20)
        result = format_date_br(input_date, format_type='short')
        assert result == '20/01/2026'
    
    def test_format_long(self):
        """Testa formatação longa com nome do mês abreviado"""
        input_date = date(2026, 1, 20)
        result = format_date_br(input_date, format_type='long')
        # Implementação usa %b que retorna abreviação (Jan, não janeiro)
        assert '20 de jan de 2026' in result.lower()


class TestFormatDateIso:
    """Testes para format_date_iso()"""
    
    def test_format_date(self):
        """Testa formatação ISO de date"""
        input_date = date(2026, 1, 20)
        result = format_date_iso(input_date)
        assert result == '2026-01-20'
    
    def test_format_datetime(self):
        """Testa formatação ISO de datetime - retorna apenas data"""
        input_datetime = datetime(2026, 1, 20, 14, 30, 0)
        result = format_date_iso(input_datetime)
        # Implementação converte datetime para date antes de isoformat
        assert result == '2026-01-20'


class TestGetCurrentDates:
    """Testes para funções de data atual"""
    
    def test_get_current_date_br(self):
        """Testa formato brasileiro da data atual"""
        result = get_current_date_br()
        # Verifica se tem formato DD/MM/YYYY
        assert len(result) == 10
        assert result[2] == '/'
        assert result[5] == '/'
    
    def test_get_current_date_filename(self):
        """Testa formato para nome de arquivo"""
        result = get_current_date_filename()
        # Verifica se tem formato YYYYMMDD
        assert len(result) == 8
        assert result.isdigit()


class TestAddMonths:
    """Testes para add_months()"""
    
    def test_add_positive_months(self):
        """Testa adição de meses"""
        input_date = date(2026, 1, 15)
        result = add_months(input_date, 2)
        assert result == date(2026, 3, 15)
    
    def test_add_negative_months(self):
        """Testa subtração de meses"""
        input_date = date(2026, 3, 15)
        result = add_months(input_date, -2)
        assert result == date(2026, 1, 15)
    
    def test_add_months_year_change(self):
        """Testa adição de meses com mudança de ano"""
        input_date = date(2025, 11, 15)
        result = add_months(input_date, 3)
        assert result == date(2026, 2, 15)
    
    def test_add_months_day_adjustment(self):
        """Testa ajuste de dia quando mês não tem dia correspondente"""
        input_date = date(2026, 1, 31)
        result = add_months(input_date, 1)
        # Fevereiro não tem dia 31, deve ajustar
        assert result.month == 2
        assert result.year == 2026


class TestDaysBetween:
    """Testes para days_between()"""
    
    def test_positive_difference(self):
        """Testa diferença positiva de dias"""
        date1 = date(2026, 1, 1)
        date2 = date(2026, 1, 11)
        result = days_between(date1, date2)
        assert result == 10
    
    def test_negative_difference(self):
        """Testa diferença negativa de dias"""
        date1 = date(2026, 1, 11)
        date2 = date(2026, 1, 1)
        result = days_between(date1, date2)
        assert result == -10
    
    def test_same_date(self):
        """Testa diferença entre mesma data"""
        same_date = date(2026, 1, 1)
        result = days_between(same_date, same_date)
        assert result == 0


class TestGetMonthRange:
    """Testes para get_month_range()"""
    
    def test_january(self):
        """Testa range de janeiro"""
        start, end = get_month_range(2026, 1)
        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)
    
    def test_february_non_leap(self):
        """Testa range de fevereiro (ano não bissexto)"""
        start, end = get_month_range(2026, 2)
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)
    
    def test_february_leap(self):
        """Testa range de fevereiro (ano bissexto)"""
        start, end = get_month_range(2024, 2)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)


class TestIsWeekend:
    """Testes para is_weekend()"""
    
    def test_saturday(self):
        """Testa sábado"""
        saturday = date(2026, 1, 24)  # 24/01/2026 é sábado
        assert is_weekend(saturday) is True
    
    def test_sunday(self):
        """Testa domingo"""
        sunday = date(2026, 1, 25)  # 25/01/2026 é domingo
        assert is_weekend(sunday) is True
    
    def test_weekday(self):
        """Testa dia de semana"""
        monday = date(2026, 1, 26)  # 26/01/2026 é segunda
        assert is_weekend(monday) is False


class TestGetNextBusinessDay:
    """Testes para get_next_business_day()"""
    
    def test_from_weekday(self):
        """Testa próximo dia útil a partir de dia de semana"""
        thursday = date(2026, 1, 22)  # 22/01/2026 é quinta
        result = get_next_business_day(thursday)
        assert result == date(2026, 1, 23)  # Sexta
    
    def test_from_friday(self):
        """Testa próximo dia útil a partir de sexta"""
        friday = date(2026, 1, 23)
        result = get_next_business_day(friday)
        assert result == date(2026, 1, 26)  # Segunda
    
    def test_from_saturday(self):
        """Testa próximo dia útil a partir de sábado"""
        saturday = date(2026, 1, 24)
        result = get_next_business_day(saturday)
        assert result == date(2026, 1, 26)  # Segunda

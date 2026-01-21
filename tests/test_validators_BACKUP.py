"""
Testes para app/utils/validators.py
"""

import pytest
from app.utils.validators import (
    validate_email,
    validate_cpf,
    validate_cnpj,
    validate_phone,
    validate_required,
    validate_positive_number,
    validate_date_range,
    validate_all,
    ValidationError
)
from datetime import date


class TestValidateEmail:
    """Testes para validate_email()"""
    
    def test_valid_simple_email(self):
        """Testa email válido simples"""
        assert validate_email('usuario@exemplo.com') is True
    
    def test_valid_subdomain(self):
        """Testa email com subdomínio"""
        assert validate_email('usuario@mail.exemplo.com') is True
    
    def test_valid_with_dots(self):
        """Testa email com pontos no nome"""
        assert validate_email('usuario.teste@exemplo.com') is True
    
    def test_valid_with_numbers(self):
        """Testa email com números"""
        assert validate_email('usuario123@exemplo.com') is True
    
    def test_invalid_no_at(self):
        """Testa email sem @"""
        assert validate_email('usuario.exemplo.com') is False
    
    def test_invalid_no_domain(self):
        """Testa email sem domínio"""
        assert validate_email('usuario@') is False
    
    def test_invalid_no_user(self):
        """Testa email sem usuário"""
        assert validate_email('@exemplo.com') is False
    
    def test_invalid_with_spaces(self):
        """Testa email com espaços"""
        assert validate_email('usuario @exemplo.com') is False
    
    def test_empty_string(self):
        """Testa string vazia"""
        assert validate_email('') is False
    
    def test_none_value(self):
        """Testa valor None"""
        assert validate_email(None) is False


class TestValidateCPF:
    """Testes para validate_cpf()"""
    
    def test_valid_formatted(self):
        """Testa CPF válido com formatação"""
        # CPF válido conhecido: 123.456.789-09
        assert validate_cpf('123.456.789-09') is True
    
    def test_valid_no_format(self):
        """Testa CPF válido sem formatação"""
        assert validate_cpf('12345678909') is True
    
    def test_invalid_check_digit(self):
        """Testa CPF com dígito verificador inválido"""
        assert validate_cpf('123.456.789-00') is False
    
    def test_invalid_all_same(self):
        """Testa CPF com todos dígitos iguais"""
        assert validate_cpf('111.111.111-11') is False
        assert validate_cpf('000.000.000-00') is False
    
    def test_invalid_wrong_length(self):
        """Testa CPF com tamanho errado"""
        assert validate_cpf('123.456.789') is False
        assert validate_cpf('123.456.789-099') is False
    
    def test_invalid_with_letters(self):
        """Testa CPF com letras"""
        assert validate_cpf('12A.456.789-09') is False
    
    def test_empty_string(self):
        """Testa string vazia"""
        assert validate_cpf('') is False


class TestValidateCNPJ:
    """Testes para validate_cnpj()"""
    
    def test_valid_formatted(self):
        """Testa CNPJ válido com formatação"""
        # CNPJ válido conhecido: 12.345.678/0001-95
        assert validate_cnpj('12.345.678/0001-95') is True
    
    def test_valid_no_format(self):
        """Testa CNPJ válido sem formatação"""
        assert validate_cnpj('12345678000195') is True
    
    def test_invalid_check_digit(self):
        """Testa CNPJ com dígito verificador inválido"""
        assert validate_cnpj('12.345.678/0001-00') is False
    
    def test_invalid_all_same(self):
        """Testa CNPJ com todos dígitos iguais"""
        assert validate_cnpj('11.111.111/1111-11') is False
        assert validate_cnpj('00.000.000/0000-00') is False
    
    def test_invalid_wrong_length(self):
        """Testa CNPJ com tamanho errado"""
        assert validate_cnpj('12.345.678/0001') is False
    
    def test_invalid_with_letters(self):
        """Testa CNPJ com letras"""
        assert validate_cnpj('12.34A.678/0001-95') is False
    
    def test_empty_string(self):
        """Testa string vazia"""
        assert validate_cnpj('') is False


class TestValidatePhone:
    """Testes para validate_phone()"""
    
    def test_valid_with_ddd(self):
        """Testa telefone com DDD"""
        assert validate_phone('(11) 98765-4321') is True
    
    def test_valid_cellphone(self):
        """Testa celular"""
        assert validate_phone('11 98765-4321') is True
    
    def test_valid_landline(self):
        """Testa telefone fixo"""
        assert validate_phone('(11) 3456-7890') is True
    
    def test_valid_no_format(self):
        """Testa telefone sem formatação"""
        assert validate_phone('11987654321') is True
    
    def test_invalid_short(self):
        """Testa telefone muito curto"""
        assert validate_phone('1234567') is False
    
    def test_invalid_with_letters(self):
        """Testa telefone com letras"""
        assert validate_phone('(11) ABC12-3456') is False
    
    def test_empty_string(self):
        """Testa string vazia"""
        assert validate_phone('') is False


class TestValidateRequired:
    """Testes para validate_required()"""
    
    def test_valid_string(self):
        """Testa string não vazia"""
        assert validate_required('texto', 'campo') is True
    
    def test_valid_number(self):
        """Testa número"""
        assert validate_required(123, 'campo') is True
    
    def test_valid_zero(self):
        """Testa zero (deve ser válido)"""
        assert validate_required(0, 'campo') is True
    
    def test_invalid_none(self):
        """Testa None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_required(None, 'campo')
        assert 'campo é obrigatório' in str(exc_info.value)
    
    def test_invalid_empty_string(self):
        """Testa string vazia"""
        with pytest.raises(ValidationError) as exc_info:
            validate_required('', 'campo')
        assert 'campo é obrigatório' in str(exc_info.value)
    
    def test_invalid_whitespace(self):
        """Testa string com apenas espaços"""
        with pytest.raises(ValidationError) as exc_info:
            validate_required('   ', 'campo')
        assert 'campo é obrigatório' in str(exc_info.value)


class TestValidatePositiveNumber:
    """Testes para validate_positive_number()"""
    
    def test_valid_positive(self):
        """Testa número positivo"""
        assert validate_positive_number(10, 'valor') is True
    
    def test_valid_zero_when_allowed(self):
        """Testa zero quando permitido"""
        assert validate_positive_number(0, 'valor', allow_zero=True) is True
    
    def test_invalid_negative(self):
        """Testa número negativo"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(-10, 'valor')
        assert 'valor deve ser positivo' in str(exc_info.value)
    
    def test_invalid_zero_when_not_allowed(self):
        """Testa zero quando não permitido"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(0, 'valor', allow_zero=False)
        assert 'valor deve ser positivo' in str(exc_info.value)
    
    def test_invalid_non_number(self):
        """Testa valor não numérico"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number('abc', 'valor')
        assert 'valor deve ser um número' in str(exc_info.value)


class TestValidateDateRange:
    """Testes para validate_date_range()"""
    
    def test_valid_range(self):
        """Testa range válido"""
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        assert validate_date_range(start, end) is True
    
    def test_valid_same_date(self):
        """Testa mesma data"""
        same_date = date(2026, 1, 1)
        assert validate_date_range(same_date, same_date) is True
    
    def test_invalid_end_before_start(self):
        """Testa data final antes da inicial"""
        start = date(2026, 1, 31)
        end = date(2026, 1, 1)
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(start, end)
        assert 'data final deve ser posterior' in str(exc_info.value).lower()
    
    def test_invalid_none_start(self):
        """Testa data inicial None"""
        end = date(2026, 1, 31)
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(None, end)
        assert 'obrigatória' in str(exc_info.value).lower()
    
    def test_invalid_none_end(self):
        """Testa data final None"""
        start = date(2026, 1, 1)
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(start, None)
        assert 'obrigatória' in str(exc_info.value).lower()


class TestValidateAll:
    """Testes para validate_all()"""
    
    def test_all_valid(self):
        """Testa todas validações passando"""
        result = validate_all(
            lambda: validate_required('texto', 'campo1'),
            lambda: validate_positive_number(10, 'campo2')
        )
        assert result is True
    
    def test_first_fails(self):
        """Testa primeira validação falhando"""
        with pytest.raises(ValidationError):
            validate_all(
                lambda: validate_required('', 'campo1'),
                lambda: validate_positive_number(10, 'campo2')
            )
    
    def test_second_fails(self):
        """Testa segunda validação falhando"""
        with pytest.raises(ValidationError):
            validate_all(
                lambda: validate_required('texto', 'campo1'),
                lambda: validate_positive_number(-10, 'campo2')
            )
    
    def test_collects_multiple_errors(self):
        """Testa coleta de múltiplos erros"""
        try:
            validate_all(
                lambda: validate_required('', 'campo1'),
                lambda: validate_positive_number(-10, 'campo2'),
                stop_on_first=False
            )
        except ValidationError as e:
            assert len(str(e).split('\n')) > 1  # Múltiplos erros


class TestValidationError:
    """Testes para ValidationError"""
    
    def test_single_error(self):
        """Testa erro único"""
        error = ValidationError('Erro de validação')
        assert str(error) == 'Erro de validação'
    
    def test_field_name(self):
        """Testa erro com nome de campo"""
        error = ValidationError('valor inválido', field='email')
        assert 'email' in str(error)

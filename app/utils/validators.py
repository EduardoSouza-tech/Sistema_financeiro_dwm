"""
✅ Validators - Validação de dados
===================================

Funções compartilhadas para validação de inputs.
Centraliza regras de negócio e validações do sistema.

Autor: Sistema de Otimização - Fase 4
Data: 20/01/2026
"""

import re
from typing import Any, Optional


def validate_required(value: Any, field_name: str = "Campo") -> tuple[bool, Optional[str]]:
    """
    Valida se campo obrigatório foi preenchido
    
    Args:
        value: Valor a validar
        field_name: Nome do campo para mensagem de erro
        
    Returns:
        Tupla (is_valid, error_message)
        
    Examples:
        >>> validate_required("valor", "Nome")
        (True, None)
        
        >>> validate_required("", "Email")
        (False, "Email é obrigatório")
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"{field_name} é obrigatório"
    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Valida formato de email
    
    Args:
        email: Email a validar
        
    Returns:
        Tupla (is_valid, error_message)
        
    Examples:
        >>> validate_email("user@example.com")
        (True, None)
        
        >>> validate_email("invalid")
        (False, "Email inválido")
    """
    if not email:
        return False, "Email é obrigatório"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Email inválido"
    
    return True, None


def validate_cpf(cpf: str) -> tuple[bool, Optional[str]]:
    """
    Valida CPF brasileiro
    
    Args:
        cpf: CPF a validar (com ou sem formatação)
        
    Returns:
        Tupla (is_valid, error_message)
        
    Examples:
        >>> validate_cpf("123.456.789-09")
        (True, None) or (False, "CPF inválido")
    """
    # Remove formatação
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False, "CPF deve ter 11 dígitos"
    
    # Verifica sequências inválidas (111.111.111-11, etc)
    if cpf == cpf[0] * 11:
        return False, "CPF inválido"
    
    # Valida primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if int(cpf[9]) != digito1:
        return False, "CPF inválido"
    
    # Valida segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if int(cpf[10]) != digito2:
        return False, "CPF inválido"
    
    return True, None


def validate_cnpj(cnpj: str) -> tuple[bool, Optional[str]]:
    """
    Valida CNPJ brasileiro
    
    Args:
        cnpj: CNPJ a validar (com ou sem formatação)
        
    Returns:
        Tupla (is_valid, error_message)
    """
    # Remove formatação
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False, "CNPJ deve ter 14 dígitos"
    
    # Verifica sequências inválidas
    if cnpj == cnpj[0] * 14:
        return False, "CNPJ inválido"
    
    # Valida primeiro dígito
    peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * peso[i] for i in range(12))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if int(cnpj[12]) != digito1:
        return False, "CNPJ inválido"
    
    # Valida segundo dígito
    peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * peso[i] for i in range(13))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if int(cnpj[13]) != digito2:
        return False, "CNPJ inválido"
    
    return True, None


def validate_phone(phone: str) -> tuple[bool, Optional[str]]:
    """
    Valida telefone brasileiro
    
    Args:
        phone: Telefone a validar
        
    Returns:
        Tupla (is_valid, error_message)
        
    Examples:
        >>> validate_phone("(11) 98765-4321")
        (True, None)
        
        >>> validate_phone("123")
        (False, "Telefone inválido")
    """
    # Remove formatação
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Valida tamanho (10 ou 11 dígitos)
    if len(phone) not in [10, 11]:
        return False, "Telefone deve ter 10 ou 11 dígitos"
    
    # Valida DDD (código de área deve estar entre 11-99)
    ddd = int(phone[:2])
    if ddd < 11 or ddd > 99:
        return False, "DDD inválido"
    
    return True, None


def validate_positive_number(value: Any, field_name: str = "Valor") -> tuple[bool, Optional[str]]:
    """
    Valida se número é positivo
    
    Args:
        value: Valor a validar
        field_name: Nome do campo
        
    Returns:
        Tupla (is_valid, error_message)
        
    Examples:
        >>> validate_positive_number(10)
        (True, None)
        
        >>> validate_positive_number(-5)
        (False, "Valor deve ser positivo")
    """
    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name} deve ser positivo"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} deve ser um número válido"


def validate_min_length(value: str, min_len: int, field_name: str = "Campo") -> tuple[bool, Optional[str]]:
    """
    Valida tamanho mínimo de string
    
    Args:
        value: String a validar
        min_len: Tamanho mínimo
        field_name: Nome do campo
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if not value or len(value) < min_len:
        return False, f"{field_name} deve ter no mínimo {min_len} caracteres"
    return True, None


def validate_max_length(value: str, max_len: int, field_name: str = "Campo") -> tuple[bool, Optional[str]]:
    """
    Valida tamanho máximo de string
    
    Args:
        value: String a validar
        max_len: Tamanho máximo
        field_name: Nome do campo
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if value and len(value) > max_len:
        return False, f"{field_name} deve ter no máximo {max_len} caracteres"
    return True, None


def validate_in_list(value: Any, valid_values: list, field_name: str = "Valor") -> tuple[bool, Optional[str]]:
    """
    Valida se valor está em lista de valores permitidos
    
    Args:
        value: Valor a validar
        valid_values: Lista de valores válidos
        field_name: Nome do campo
        
    Returns:
        Tupla (is_valid, error_message)
        
    Examples:
        >>> validate_in_list("admin", ["admin", "user"])
        (True, None)
        
        >>> validate_in_list("invalid", ["admin", "user"])
        (False, "Valor inválido")
    """
    if value not in valid_values:
        return False, f"{field_name} inválido. Valores permitidos: {', '.join(map(str, valid_values))}"
    return True, None


class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass


def validate_all(*validations) -> None:
    """
    Executa múltiplas validações e levanta exceção se alguma falhar
    
    Args:
        *validations: Tuplas (is_valid, error_message) de validate_*
        
    Raises:
        ValidationError: Se alguma validação falhar
        
    Examples:
        >>> validate_all(
        ...     validate_required("João", "Nome"),
        ...     validate_email("joao@example.com")
        ... )
        # Sucesso, nenhuma exceção
        
        >>> validate_all(
        ...     validate_required("", "Nome"),
        ...     validate_email("invalid")
        ... )
        ValidationError: Nome é obrigatório
    """
    for is_valid, error_message in validations:
        if not is_valid:
            raise ValidationError(error_message)

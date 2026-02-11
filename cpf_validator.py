"""
🔐 Validador de CPF
==================

Valida CPFs brasileiros usando algoritmo oficial da Receita Federal.

Funcionalidades:
- Validação de dígito verificador
- Formatação/Limpeza de CPF
- Detecção de CPFs inválidos conhecidos (000.000.000-00, etc)
- Relatório de CPFs inválidos no banco de dados

Data: 11/02/2026
"""

import re
from typing import Optional, Dict, List, Tuple


class CPFValidator:
    """Validador de CPF brasileiro"""
    
    # CPFs conhecidos como inválidos (todos números iguais)
    CPFS_INVALIDOS = [
        '00000000000', '11111111111', '22222222222', '33333333333',
        '44444444444', '55555555555', '66666666666', '77777777777',
        '88888888888', '99999999999'
    ]
    
    @staticmethod
    def limpar(cpf: str) -> str:
        """
        Remove caracteres não numéricos do CPF
        
        Args:
            cpf: CPF com ou sem formatação
            
        Returns:
            CPF apenas com números
        """
        if not cpf:
            return ''
        return re.sub(r'\D', '', str(cpf))
    
    @staticmethod
    def formatar(cpf: str) -> str:
        """
        Formata CPF no padrão XXX.XXX.XXX-XX
        
        Args:
            cpf: CPF sem formatação (11 dígitos)
            
        Returns:
            CPF formatado ou string vazia se inválido
        """
        cpf_limpo = CPFValidator.limpar(cpf)
        
        if len(cpf_limpo) != 11:
            return ''
        
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    
    @staticmethod
    def validar(cpf: str, permitir_vazio: bool = False) -> bool:
        """
        Valida CPF usando algoritmo oficial
        
        Args:
            cpf: CPF com ou sem formatação
            permitir_vazio: Se True, CPF vazio é considerado válido
            
        Returns:
            True se CPF é válido, False caso contrário
        """
        # Limpar CPF
        cpf_limpo = CPFValidator.limpar(cpf)
        
        # CPF vazio
        if not cpf_limpo:
            return permitir_vazio
        
        # Verifica se tem 11 dígitos
        if len(cpf_limpo) != 11:
            return False
        
        # Verifica se não é uma sequência de números iguais
        if cpf_limpo in CPFValidator.CPFS_INVALIDOS:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        
        # Verifica primeiro dígito
        if int(cpf_limpo[9]) != digito1:
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        
        # Verifica segundo dígito
        if int(cpf_limpo[10]) != digito2:
            return False
        
        return True
    
    @staticmethod
    def validar_com_detalhes(cpf: str) -> Dict[str, any]:
        """
        Valida CPF e retorna detalhes do erro
        
        Args:
            cpf: CPF com ou sem formatação
            
        Returns:
            Dicionário com:
            - valido: bool
            - erro: str (mensagem de erro se inválido)
            - cpf_formatado: str (CPF formatado se válido)
        """
        cpf_limpo = CPFValidator.limpar(cpf)
        
        # CPF vazio
        if not cpf_limpo:
            return {
                'valido': False,
                'erro': 'CPF não informado',
                'cpf_formatado': ''
            }
        
        # Tamanho inválido
        if len(cpf_limpo) != 11:
            return {
                'valido': False,
                'erro': f'CPF deve ter 11 dígitos (tem {len(cpf_limpo)})',
                'cpf_formatado': ''
            }
        
        # Sequência de números iguais
        if cpf_limpo in CPFValidator.CPFS_INVALIDOS:
            return {
                'valido': False,
                'erro': 'CPF inválido (sequência de números iguais)',
                'cpf_formatado': ''
            }
        
        # Validação de dígitos verificadores
        if not CPFValidator.validar(cpf_limpo):
            return {
                'valido': False,
                'erro': 'CPF inválido (dígitos verificadores incorretos)',
                'cpf_formatado': ''
            }
        
        return {
            'valido': True,
            'erro': None,
            'cpf_formatado': CPFValidator.formatar(cpf_limpo)
        }


def validar_lista_cpfs(cpfs: List[str]) -> Dict[str, List[str]]:
    """
    Valida lista de CPFs e separa válidos/inválidos
    
    Args:
        cpfs: Lista de CPFs (com ou sem formatação)
        
    Returns:
        Dicionário com:
        - validos: lista de CPFs válidos (formatados)
        - invalidos: lista de CPFs inválidos (original)
        - total: quantidade total
        - taxa_erro: percentual de erro
    """
    validos = []
    invalidos = []
    
    for cpf in cpfs:
        if CPFValidator.validar(cpf, permitir_vazio=False):
            validos.append(CPFValidator.formatar(cpf))
        else:
            invalidos.append(cpf)
    
    total = len(cpfs)
    taxa_erro = (len(invalidos) / total * 100) if total > 0 else 0
    
    return {
        'validos': validos,
        'invalidos': invalidos,
        'total': total,
        'total_validos': len(validos),
        'total_invalidos': len(invalidos),
        'taxa_erro': round(taxa_erro, 2)
    }


# Exemplo de uso
if __name__ == '__main__':
    print("🧪 Testando validador de CPF...\n")
    
    # Testes
    testes = [
        ("123.456.789-09", True),   # Válido
        ("111.111.111-11", False),  # Sequência
        ("000.000.001-91", True),   # Válido
        ("12345678909", True),      # Sem formatação
        ("123.456.789-00", False),  # Dígito inválido
        ("", False),                # Vazio
        ("123", False),             # Tamanho errado
    ]
    
    for cpf, esperado in testes:
        resultado = CPFValidator.validar(cpf)
        status = "✅" if resultado == esperado else "❌"
        print(f"{status} {cpf:20s} -> {resultado} (esperado: {esperado})")
    
    print("\n✅ Testes concluídos!")

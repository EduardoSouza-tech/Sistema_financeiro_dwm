#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO DE CORREÇÃO AUTOMÁTICA DE CPF
Sistema de correção heurística para CPFs inválidos

Tipos de correção suportados:
1. Formatação (espaços, caracteres especiais)
2. Zeros à esquerda faltando
3. Recálculo de dígitos verificadores
4. Detectar transposições simples de dígitos

Autor: Sistema Financeiro DWM
Data: 2026-02-11
"""

import re
from typing import Dict, List, Optional, Tuple
from cpf_validator import CPFValidator


class CPFCorrector:
    """
    Sistema avançado de correção automática de CPF
    """
    
    @staticmethod
    def tentar_correcao_automatica(cpf: str) -> Dict[str, any]:
        """
        Tenta corrigir automaticamente um CPF inválido
        
        Args:
            cpf: CPF com possíveis erros
            
        Returns:
            Dict com:
            - corrigido: bool (se foi possível corrigir)
            - cpf_original: str (CPF original)
            - cpf_corrigido: str (CPF corrigido, se aplicável)
            - tipo_correcao: str (tipo de correção aplicada)
            - confianca: float (0.0 a 1.0 - confiança na correção)
            - erro: str (se não foi possível corrigir)
        """
        
        cpf_original = str(cpf).strip() if cpf else ""
        
        # Se CPF está vazio, não há o que corrigir
        if not cpf_original:
            return {
                'corrigido': False,
                'cpf_original': '',
                'cpf_corrigido': '',
                'tipo_correcao': '',
                'confianca': 0.0,
                'erro': 'CPF não informado'
            }
        
        # Se CPF já é válido, não precisa correção
        if CPFValidator.validar(cpf_original):
            return {
                'corrigido': True,
                'cpf_original': cpf_original,
                'cpf_corrigido': CPFValidator.formatar(cpf_original),
                'tipo_correcao': 'formatacao_apenas',
                'confianca': 1.0,
                'erro': None
            }
        
        # Tentar diferentes tipos de correção em ordem de confiança
        
        # 1. CORREÇÃO DE FORMATAÇÃO E ZEROS
        cpf_corrigido = CPFCorrector._corrigir_formatacao_zeros(cpf_original)
        if cpf_corrigido and CPFValidator.validar(cpf_corrigido):
            return {
                'corrigido': True,
                'cpf_original': cpf_original,
                'cpf_corrigido': CPFValidator.formatar(cpf_corrigido),
                'tipo_correcao': 'formatacao_e_zeros',
                'confianca': 0.95,
                'erro': None
            }
        
        # 2. RECÁLCULO DE DÍGITOS VERIFICADORES
        cpf_corrigido = CPFCorrector._corrigir_digitos_verificadores(cpf_original)
        if cpf_corrigido and CPFValidator.validar(cpf_corrigido):
            return {
                'corrigido': True,
                'cpf_original': cpf_original,
                'cpf_corrigido': CPFValidator.formatar(cpf_corrigido),
                'tipo_correcao': 'digitos_verificadores',
                'confianca': 0.90,
                'erro': None
            }
        
        # 3. DETECTAR TRANSPOSIÇÃO DE DÍGITOS ADJACENTES
        cpf_corrigido = CPFCorrector._corrigir_transposicao(cpf_original)
        if cpf_corrigido and CPFValidator.validar(cpf_corrigido):
            return {
                'corrigido': True,
                'cpf_original': cpf_original,
                'cpf_corrigido': CPFValidator.formatar(cpf_corrigido),
                'tipo_correcao': 'transposicao_digitos',
                'confianca': 0.75,
                'erro': None
            }
        
        # 4. DETECTAR UM DÍGITO INCORRETO (FORÇA BRUTA LIMITADA)
        cpf_corrigido = CPFCorrector._corrigir_digito_simples(cpf_original)
        if cpf_corrigido and CPFValidator.validar(cpf_corrigido):
            return {
                'corrigido': True,
                'cpf_original': cpf_original,
                'cpf_corrigido': CPFValidator.formatar(cpf_corrigido),
                'tipo_correcao': 'digito_simples',
                'confianca': 0.60,
                'erro': None
            }
        
        # Nenhuma correção funcionou
        validacao = CPFValidator.validar_com_detalhes(cpf_original)
        return {
            'corrigido': False,
            'cpf_original': cpf_original,
            'cpf_corrigido': '',
            'tipo_correcao': '',
            'confianca': 0.0,
            'erro': validacao.get('erro', 'CPF não pode ser corrigido automaticamente')
        }
    
    @staticmethod
    def _corrigir_formatacao_zeros(cpf: str) -> Optional[str]:
        """
        Corrige formatação e adiciona zeros à esquerda se necessário
        
        Casos tratados:
        - Remove caracteres não numéricos (pontos, traços, espaços)
        - Adiciona zeros à esquerda até completar 11 dígitos
        - Rejeita CPFs com mais de 11 dígitos após limpeza
        
        Exemplos:
        - "969.256.476-20" -> "96925647620" (apenas formatação)
        - "9692564762" -> "09692564762" (1 zero à esquerda)
        - "969256476" -> "00969256476" (2 zeros à esquerda)
        - "12345678901234" -> None (mais de 11 dígitos)
        """
        if not cpf:
            return None
            
        # Limpar tudo que não é dígito
        cpf_limpo = re.sub(r'\D', '', cpf)
        
        # Se não tem dígitos, retornar None
        if not cpf_limpo:
            return None
        
        # Se tem mais de 11 dígitos, não pode corrigir
        if len(cpf_limpo) > 11:
            return None
        
        # Adicionar zeros à esquerda até completar 11 dígitos
        cpf_completo = cpf_limpo.zfill(11)
        
        # Retornar CPF com 11 dígitos
        return cpf_completo
    
    @staticmethod
    def _corrigir_digitos_verificadores(cpf: str) -> Optional[str]:
        """
        Recalcula e corrige os dígitos verificadores (últimos 2 dígitos)
        """
        cpf_limpo = CPFCorrector._corrigir_formatacao_zeros(cpf)
        
        if not cpf_limpo or len(cpf_limpo) != 11:
            return None
        
        # Pegar apenas os 9 primeiros dígitos
        cpf_base = cpf_limpo[:9]
        
        # Calcular primeiro dígito verificador
        soma = sum(int(cpf_base[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        
        # Calcular segundo dígito verificador
        cpf_com_primeiro = cpf_base + str(digito1)
        soma = sum(int(cpf_com_primeiro[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        
        cpf_corrigido = cpf_base + str(digito1) + str(digito2)
        
        # Verificar se não é sequência inválida
        if cpf_corrigido in CPFValidator.CPFS_INVALIDOS:
            return None
        
        return cpf_corrigido
    
    @staticmethod
    def _corrigir_transposicao(cpf: str) -> Optional[str]:
        """
        Detecta e corrige transposição de dígitos adjacentes
        Exemplo: 12354678901 → 12345678901
        """
        cpf_limpo = CPFCorrector._corrigir_formatacao_zeros(cpf)
        
        if not cpf_limpo or len(cpf_limpo) != 11:
            return None
        
        # Testar trocar cada par de dígitos adjacentes
        for i in range(len(cpf_limpo) - 1):
            cpf_array = list(cpf_limpo)
            # Trocar posições i e i+1
            cpf_array[i], cpf_array[i + 1] = cpf_array[i + 1], cpf_array[i]
            cpf_testado = ''.join(cpf_array)
            
            if CPFValidator.validar(cpf_testado):
                return cpf_testado
        
        return None
    
    @staticmethod
    def _corrigir_digito_simples(cpf: str) -> Optional[str]:
        """
        Força bruta limitada: testa corrigir um único dígito
        Apenas para os 9 primeiros dígitos (não os verificadores)
        """
        cpf_limpo = CPFCorrector._corrigir_formatacao_zeros(cpf)
        
        if not cpf_limpo or len(cpf_limpo) != 11:
            return None
        
        # Testar mudar cada um dos 9 primeiros dígitos
        for pos in range(9):  # Apenas os 9 primeiros
            for digito in range(10):
                if str(digito) == cpf_limpo[pos]:
                    continue  # Pular o dígito atual
                
                cpf_array = list(cpf_limpo)
                cpf_array[pos] = str(digito)
                cpf_base = ''.join(cpf_array[:9])
                
                # Recalcular dígitos verificadores para este novo CPF base
                cpf_corrigido = CPFCorrector._recalcular_cpf_completo(cpf_base)
                
                if cpf_corrigido and CPFValidator.validar(cpf_corrigido):
                    return cpf_corrigido
        
        return None
    
    @staticmethod
    def _recalcular_cpf_completo(cpf_base_9_digitos: str) -> Optional[str]:
        """
        Recalcula CPF completo a partir dos 9 primeiros dígitos
        """
        if len(cpf_base_9_digitos) != 9:
            return None
        
        # Calcular primeiro dígito verificador
        soma = sum(int(cpf_base_9_digitos[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        
        # Calcular segundo dígito verificador
        cpf_com_primeiro = cpf_base_9_digitos + str(digito1)
        soma = sum(int(cpf_com_primeiro[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        
        cpf_completo = cpf_base_9_digitos + str(digito1) + str(digito2)
        
        # Verificar se não é sequência inválida
        if cpf_completo in CPFValidator.CPFS_INVALIDOS:
            return None
        
        return cpf_completo
    
    @staticmethod
    def corrigir_lista_funcionarios(funcionarios: List[Dict]) -> Dict[str, any]:
        """
        Aplica correção automática em uma lista de funcionários
        
        Args:
            funcionarios: Lista de dicts com pelo menos {'id': int, 'cpf': str, 'nome': str}
            
        Returns:
            Dict com estatísticas e lista de correções sugeridas
        """
        resultado = {
            'total_analisados': len(funcionarios),
            'total_corrigidos': 0,
            'total_nao_corrigidos': 0,
            'correcoes_por_tipo': {},
            'correcoes_sugeridas': []
        }
        
        for func in funcionarios:
            cpf = func.get('cpf', '')
            
            # Tentar correção
            correcao = CPFCorrector.tentar_correcao_automatica(cpf)
            
            if correcao['corrigido'] and correcao['tipo_correcao'] != 'formatacao_apenas':
                resultado['total_corrigidos'] += 1
                
                # Contar tipo de correção
                tipo = correcao['tipo_correcao']
                resultado['correcoes_por_tipo'][tipo] = resultado['correcoes_por_tipo'].get(tipo, 0) + 1
                
                # Adicionar à lista de sugestões
                resultado['correcoes_sugeridas'].append({
                    'funcionario_id': func.get('id'),
                    'funcionario_nome': func.get('nome', ''),
                    'cpf_original': correcao['cpf_original'],
                    'cpf_corrigido': correcao['cpf_corrigido'],
                    'tipo_correcao': correcao['tipo_correcao'],
                    'confianca': correcao['confianca'],
                    'recomendacao': CPFCorrector._get_recomendacao(correcao['confianca'])
                })
            else:
                resultado['total_nao_corrigidos'] += 1
        
        return resultado
    
    @staticmethod
    def _get_recomendacao(confianca: float) -> str:
        """Retorna recomendação baseada no nível de confiança"""
        if confianca >= 0.90:
            return "✅ APLICAR AUTOMATICAMENTE"
        elif confianca >= 0.75:
            return "⚠️ REVISAR E APLICAR"
        elif confianca >= 0.60:
            return "🔍 VERIFICAR MANUALMENTE"
        else:
            return "❌ NÃO RECOMENDADO"


# ============================================================================
# TESTES UNITÁRIOS
# ============================================================================

if __name__ == "__main__":
    print("🧪 TESTES DO CORRETOR DE CPF")
    print("=" * 50)
    
    # Casos de teste
    casos_teste = [
        # Formatação e zeros
        ("12345678909", "Já válido"),
        ("   123.456.789-09   ", "Formatação com espaços"),
        ("1234567890", "Faltando zero à esquerda"),  # Vai virar 01234567890, mas é inválido
        
        # Dígitos verificadores errados
        ("12345678900", "Dígitos verificadores errados"),
        ("98765432100", "Outro caso de dígitos errados"),
        
        # Transposição
        ("21345678909", "Primeiro e segundo trocados"),
        ("12354678909", "Quarto e quinto trocados"),
        
        # Casos impossíveis
        ("11111111111", "Sequência inválida"),
        ("00000000000", "Zeros inválidos"),
        ("", "CPF vazio"),
        ("123", "Muito curto"),
    ]
    
    for cpf_teste, descricao in casos_teste:
        print(f"\n🔍 Testando: {descricao}")
        print(f"   CPF: '{cpf_teste}'")
        
        resultado = CPFCorrector.tentar_correcao_automatica(cpf_teste)
        
        if resultado['corrigido']:
            print(f"   ✅ CORRIGIDO: {resultado['cpf_corrigido']}")
            print(f"   📋 Tipo: {resultado['tipo_correcao']}")
            print(f"   📊 Confiança: {resultado['confianca']:.0%}")
        else:
            print(f"   ❌ NÃO CORRIGIDO: {resultado['erro']}")
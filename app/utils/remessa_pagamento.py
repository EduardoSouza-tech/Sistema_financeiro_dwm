"""
Utilitários para Remessa de Pagamento Sicredi
Geração e processamento de arquivos CNAB 240
Versão: 1.0.0 - 09/02/2026
"""

from datetime import datetime, date
from typing import List, Dict, Tuple
import hashlib
import re


# =============================================================================
# VALIDADORES BRASILEIROS
# =============================================================================

def validar_cpf(cpf: str) -> Tuple[bool, str]:
    """
    Valida CPF brasileiro com dígitos verificadores
    
    Args:
        cpf: CPF no formato XXX.XXX.XXX-XX ou apenas números
        
    Returns:
        (bool, str): (válido, mensagem_erro)
    """
    # Remove formatação
    cpf_limpo = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica tamanho
    if len(cpf_limpo) != 11:
        return False, "CPF deve ter 11 dígitos"
    
    # Verifica sequências inválidas (111.111.111-11, etc.)
    if cpf_limpo == cpf_limpo[0] * 11:
        return False, "CPF inválido"
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if int(cpf_limpo[9]) != digito1:
        return False, "CPF com dígito verificador inválido"
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if int(cpf_limpo[10]) != digito2:
        return False, "CPF com dígito verificador inválido"
    
    return True, ""


def validar_cnpj(cnpj: str) -> Tuple[bool, str]:
    """
    Valida CNPJ brasileiro com dígitos verificadores
    
    Args:
        cnpj: CNPJ no formato XX.XXX.XXX/XXXX-XX ou apenas números
        
    Returns:
        (bool, str): (válido, mensagem_erro)
    """
    # Remove formatação
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica tamanho
    if len(cnpj_limpo) != 14:
        return False, "CNPJ deve ter 14 dígitos"
    
    # Verifica sequências inválidas
    if cnpj_limpo == cnpj_limpo[0] * 14:
        return False, "CNPJ inválido"
    
    # Calcula primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj_limpo[i]) * pesos1[i] for i in range(12))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if int(cnpj_limpo[12]) != digito1:
        return False, "CNPJ com dígito verificador inválido"
    
    # Calcula segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj_limpo[i]) * pesos2[i] for i in range(13))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if int(cnpj_limpo[13]) != digito2:
        return False, "CNPJ com dígito verificador inválido"
    
    return True, ""


def validar_codigo_barras(codigo: str) -> Tuple[bool, str]:
    """
    Valida código de barras de boleto bancário
    
    Args:
        codigo: Código de barras (44 ou 47 dígitos)
        
    Returns:
        (bool, str): (válido, mensagem_erro)
    """
    # Remove espaços e formatação
    codigo_limpo = re.sub(r'[^0-9]', '', codigo)
    
    # Verifica tamanho (44 para bancário, 47 para arrecadação)
    if len(codigo_limpo) not in [44, 47]:
        return False, f"Código de barras deve ter 44 ou 47 dígitos (tem {len(codigo_limpo)})"
    
    # Para código de 44 dígitos (bancário)
    if len(codigo_limpo) == 44:
        # Dígito verificador está na posição 4 (índice 3)
        dv = int(codigo_limpo[3])
        
        # Monta código sem DV para cálculo
        codigo_sem_dv = codigo_limpo[0:3] + codigo_limpo[4:44]
        
        # Calcula DV (módulo 11)
        soma = 0
        multiplicador = 2
        for i in range(len(codigo_sem_dv) - 1, -1, -1):
            soma += int(codigo_sem_dv[i]) * multiplicador
            multiplicador += 1
            if multiplicador > 9:
                multiplicador = 2
        
        resto = soma % 11
        dv_calculado = 11 - resto
        
        if dv_calculado >= 10:
            dv_calculado = 1
        
        if dv != dv_calculado:
            return False, "Código de barras com dígito verificador inválido"
    
    return True, ""


def validar_dados_bancarios(banco: str, agencia: str, conta: str) -> Tuple[bool, str]:
    """
    Valida dados bancários básicos
    
    Args:
        banco: Código do banco (3 dígitos)
        agencia: Número da agência
        conta: Número da conta
        
    Returns:
        (bool, str): (válido, mensagem_erro)
    """
    if not banco or len(banco) != 3:
        return False, "Código do banco deve ter 3 dígitos"
    
    if not banco.isdigit():
        return False, "Código do banco deve conter apenas números"
    
    if not agencia or len(agencia) < 4:
        return False, "Agência deve ter no mínimo 4 dígitos"
    
    if not conta or len(conta) < 5:
        return False, "Conta deve ter no mínimo 5 dígitos"
    
    return True, ""


# =============================================================================
# GERADOR CNAB 240 - SICREDI
# =============================================================================

class GeradorCNAB240:
    """
    Gerador de arquivos CNAB 240 para o Banco Sicredi
    Layout versão 103
    """
    
    BANCO_SICREDI = "748"
    VERSAO_LAYOUT = "103"
    
    def __init__(self, empresa: Dict, convenio: Dict):
        """
        Inicializa gerador com dados da empresa e convênio
        
        Args:
            empresa: {razao_social, cnpj, agencia, conta}
            convenio: {codigo_convenio, codigo_beneficiario}
        """
        self.empresa = empresa
        self.convenio = convenio
    
    def gerar_remessa(self, pagamentos: List[Dict], data_arquivo: datetime = None) -> str:
        """
        Gera arquivo CNAB 240 completo
        
        Args:
            pagamentos: Lista de dicionários com dados dos pagamentos
            data_arquivo: Data de geração (default: agora)
            
        Returns:
            str: Conteúdo do arquivo CNAB (múltiplas linhas)
        """
        if data_arquivo is None:
            data_arquivo = datetime.now()
        
        linhas = []
        
        # Header do arquivo (Tipo 0)
        linhas.append(self._gerar_header_arquivo(data_arquivo))
        
        numero_lote = 1
        
        # Separar pagamentos por tipo
        pagamentos_ted = [p for p in pagamentos if p.get('tipo') == 'TED']
        pagamentos_pix = [p for p in pagamentos if p.get('tipo') == 'PIX']
        pagamentos_boleto = [p for p in pagamentos if p.get('tipo') == 'BOLETO']
        pagamentos_tributo = [p for p in pagamentos if p.get('tipo') == 'TRIBUTO']
        
        # Gerar lote TED
        if pagamentos_ted:
            linhas.extend(self._gerar_lote_ted(pagamentos_ted, numero_lote))
            numero_lote += 1
        
        # Gerar lote PIX
        if pagamentos_pix:
            linhas.extend(self._gerar_lote_pix(pagamentos_pix, numero_lote))
            numero_lote += 1
        
        # Gerar lote Boleto
        if pagamentos_boleto:
            linhas.extend(self._gerar_lote_boleto(pagamentos_boleto, numero_lote))
            numero_lote += 1
        
        # Gerar lote Tributo
        if pagamentos_tributo:
            linhas.extend(self._gerar_lote_tributo(pagamentos_tributo, numero_lote))
            numero_lote += 1
        
        # Trailer do arquivo (Tipo 9)
        linhas.append(self._gerar_trailer_arquivo(numero_lote - 1, len(linhas) + 1))
        
        return '\n'.join(linhas)
    
    def _gerar_header_arquivo(self, data_arquivo: datetime) -> str:
        """Gera header do arquivo (Tipo 0)"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += "0000"  # 004-007: Lote (0000 para header)
        linha += "0"  # 008: Tipo registro (0=header arquivo)
        linha += " " * 9  # 009-017: Uso exclusivo FEBRABAN
        linha += "2" if len(self.empresa.get('cnpj', '')) == 14 else "1"  # 018: Tipo inscrição (1=CPF, 2=CNPJ)
        linha += self.empresa.get('cnpj', '').zfill(14)  # 019-032: CNPJ/CPF
        linha += self.convenio.get('codigo_convenio', '').ljust(20)  # 033-052: Convênio
        linha += self.empresa.get('agencia', '').zfill(5)  # 053-057: Agência
        linha += " "  # 058: DV agência
        linha += self.empresa.get('conta', '').zfill(12)  # 059-070: Conta
        linha += " "  # 071: DV conta
        linha += " "  # 072: DV agência/conta
        linha += self.empresa.get('razao_social', '')[:30].ljust(30).upper()  # 073-102: Nome empresa
        linha += "SICREDI".ljust(30)  # 103-132: Nome banco
        linha += " " * 10  # 133-142: Uso exclusivo FEBRABAN
        linha += "1"  # 143: Código remessa (1=Remessa)
        linha += data_arquivo.strftime("%d%m%Y")  # 144-151: Data geração
        linha += data_arquivo.strftime("%H%M%S")  # 152-157: Hora geração
        linha += "000001"  # 158-163: Sequencial arquivo (NSA)
        linha += self.VERSAO_LAYOUT  # 164-166: Versão layout
        linha += "00000"  # 167-171: Densidade gravação
        linha += " " * 20  # 172-191: Uso banco
        linha += " " * 20  # 192-211: Uso empresa
        linha += " " * 29  # 212-240: Uso exclusivo FEBRABAN
        
        return linha
    
    def _gerar_lote_ted(self, pagamentos: List[Dict], numero_lote: int) -> List[str]:
        """Gera lote de TED/DOC"""
        linhas = []
        
        # Header do lote
        linhas.append(self._gerar_header_lote(numero_lote, "01", "03"))  # 01=Crédito Conta, 03=DOC/TED
        
        # Detalhes (Segmento A)
        for i, pag in enumerate(pagamentos, 1):
            linhas.append(self._gerar_segmento_a_ted(pag, numero_lote, i))
        
        # Trailer do lote
        linhas.append(self._gerar_trailer_lote(numero_lote, len(pagamentos)))
        
        return linhas
    
    def _gerar_lote_pix(self, pagamentos: List[Dict], numero_lote: int) -> List[str]:
        """Gera lote de PIX"""
        linhas = []
        
        # Header do lote
        linhas.append(self._gerar_header_lote(numero_lote, "45", "45"))  # 45=PIX
        
        # Detalhes (Segmento PIX)
        for i, pag in enumerate(pagamentos, 1):
            linhas.append(self._gerar_segmento_pix(pag, numero_lote, i))
        
        # Trailer do lote
        linhas.append(self._gerar_trailer_lote(numero_lote, len(pagamentos)))
        
        return linhas
    
    def _gerar_lote_boleto(self, pagamentos: List[Dict], numero_lote: int) -> List[str]:
        """Gera lote de Boletos"""
        linhas = []
        
        # Header do lote
        linhas.append(self._gerar_header_lote(numero_lote, "31", "31"))  # 31=Boleto
        
        # Detalhes (Segmento J)
        for i, pag in enumerate(pagamentos, 1):
            linhas.append(self._gerar_segmento_boleto(pag, numero_lote, i))
        
        # Trailer do lote
        linhas.append(self._gerar_trailer_lote(numero_lote, len(pagamentos)))
        
        return linhas
    
    def _gerar_lote_tributo(self, pagamentos: List[Dict], numero_lote: int) -> List[str]:
        """Gera lote de Tributos"""
        linhas = []
        
        # Header do lote
        linhas.append(self._gerar_header_lote(numero_lote, "17", "17"))  # 17=Tributos
        
        # Detalhes (Segmento Tributo)
        for i, pag in enumerate(pagamentos, 1):
            linhas.append(self._gerar_segmento_tributo(pag, numero_lote, i))
        
        # Trailer do lote
        linhas.append(self._gerar_trailer_lote(numero_lote, len(pagamentos)))
        
        return linhas
    
    def _gerar_header_lote(self, numero_lote: int, tipo_operacao: str, forma_pagamento: str) -> str:
        """Gera header de lote (Tipo 1)"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += str(numero_lote).zfill(4)  # 004-007: Número lote
        linha += "1"  # 008: Tipo registro (1=header lote)
        linha += "C"  # 009: Tipo operação (C=Crédito, D=Débito)
        linha += tipo_operacao.zfill(2)  # 010-011: Tipo serviço
        linha += forma_pagamento.zfill(2)  # 012-013: Forma lançamento
        linha += self.VERSAO_LAYOUT  # 014-016: Versão layout lote
        linha += " "  # 017: Uso exclusivo FEBRABAN
        linha += "2" if len(self.empresa.get('cnpj', '')) == 14 else "1"  # 018: Tipo inscrição
        linha += self.empresa.get('cnpj', '').zfill(14)  # 019-032: CNPJ/CPF
        linha += self.convenio.get('codigo_convenio', '').ljust(20)  # 033-052: Convênio
        linha += self.empresa.get('agencia', '').zfill(5)  # 053-057: Agência
        linha += " "  # 058: DV agência
        linha += self.empresa.get('conta', '').zfill(12)  # 059-070: Conta
        linha += " "  # 071: DV conta
        linha += " "  # 072: DV agência/conta
        linha += self.empresa.get('razao_social', '')[:30].ljust(30).upper()  # 073-102: Nome empresa
        linha += " " * 40  # 103-142: Mensagem
        linha += " " * 8  # 143-150: Logradouro
        linha += "00000"  # 151-155: Número
        linha += " " * 15  # 156-170: Complemento
        linha += " " * 20  # 171-190: Cidade
        linha += "00000000"  # 191-198: CEP
        linha += "  "  # 199-200: UF
        linha += " " * 8  # 201-208: Uso exclusivo FEBRABAN
        linha += " " * 32  # 209-240: Ocorrências
        
        return linha
    
    def _gerar_segmento_a_ted(self, pagamento: Dict, numero_lote: int, sequencial: int) -> str:
        """Gera Segmento A para TED/DOC"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += str(numero_lote).zfill(4)  # 004-007: Número lote
        linha += "3"  # 008: Tipo registro (3=detalhe)
        linha += str(sequencial).zfill(5)  # 009-013: Número registro no lote
        linha += "A"  # 014: Segmento
        linha += "0"  # 015: Tipo movimento (0=Inclusão)
        linha += "00"  # 016-017: Código movimento
        linha += pagamento.get('banco', '').zfill(3)  # 018-020: Banco favorecido
        linha += pagamento.get('agencia', '').zfill(5)  # 021-025: Agência favorecida
        linha += " "  # 026: DV agência
        linha += pagamento.get('conta', '').zfill(12)  # 027-038: Conta favorecida
        linha += " "  # 039: DV conta
        linha += " "  # 040: DV agência/conta
        linha += pagamento.get('favorecido', '')[:30].ljust(30).upper()  # 041-070: Nome favorecido
        linha += pagamento.get('seu_numero', '').ljust(20)  # 071-090: Seu número
        linha += pagamento.get('data_pagamento', date.today()).strftime("%d%m%Y")  # 091-098: Data pagamento
        linha += "REA"  # 099-101: Tipo moeda (REA=Real)
        linha += "00000"  # 102-106: Quantidade moeda
        linha += str(int(pagamento.get('valor', 0) * 100)).zfill(15)  # 107-121: Valor pagamento
        linha += " " * 20  # 122-141: Nosso número
        linha += "00000000"  # 142-149: Data real efetivação
        linha += "000000000000000"  # 150-164: Valor real efetivação
        linha += " " * 40  # 165-204: Informação 2
        linha += " " * 2  # 205-206: Código finalidade DOC
        linha += " " * 5  # 207-211: Código finalidade TED
        linha += " " * 5  # 212-216: Uso exclusivo FEBRABAN
        linha += "0"  # 217: Aviso ao favorecido
        linha += " " * 10  # 218-227: Ocorrências
        linha += " " * 13  # 228-240: Uso exclusivo FEBRABAN
        
        return linha
    
    def _gerar_segmento_pix(self, pagamento: Dict, numero_lote: int, sequencial: int) -> str:
        """Gera Segmento PIX"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += str(numero_lote).zfill(4)  # 004-007: Número lote
        linha += "3"  # 008: Tipo registro
        linha += str(sequencial).zfill(5)  # 009-013: Número registro
        linha += "P"  # 014: Segmento PIX
        linha += "0"  # 015: Tipo movimento
        linha += "00"  # 016-017: Código movimento
        linha += self.BANCO_SICREDI  # 018-020: Banco (próprio)
        linha += " " * 20  # 021-040: Dados bancários (não usado em PIX)
        linha += pagamento.get('favorecido', '')[:30].ljust(30).upper()  # 041-070: Nome favorecido
        linha += pagamento.get('seu_numero', '').ljust(20)  # 071-090: Seu número
        linha += pagamento.get('data_pagamento', date.today()).strftime("%d%m%Y")  # 091-098: Data pagamento
        linha += "REA"  # 099-101: Tipo moeda
        linha += "00000"  # 102-106: Quantidade moeda
        linha += str(int(pagamento.get('valor', 0) * 100)).zfill(15)  # 107-121: Valor
        linha += pagamento.get('chave_pix', '').ljust(77)  # 122-198: Chave PIX
        linha += pagamento.get('tipo_chave', '').ljust(2)  # 199-200: Tipo chave PIX
        linha += " " * 40  # 201-240: Uso exclusivo
        
        return linha
    
    def _gerar_segmento_boleto(self, pagamento: Dict, numero_lote: int, sequencial: int) -> str:
        """Gera Segmento J para Boleto"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += str(numero_lote).zfill(4)  # 004-007: Número lote
        linha += "3"  # 008: Tipo registro
        linha += str(sequencial).zfill(5)  # 009-013: Número registro
        linha += "J"  # 014: Segmento
        linha += "0"  # 015: Tipo movimento
        linha += "00"  # 016-017: Código movimento
        linha += pagamento.get('codigo_barras', '').ljust(44)  # 018-061: Código barras
        linha += pagamento.get('favorecido', '')[:30].ljust(30).upper()  # 062-091: Nome favorecido
        linha += pagamento.get('data_vencimento', date.today()).strftime("%d%m%Y")  # 092-099: Vencimento
        linha += str(int(pagamento.get('valor', 0) * 100)).zfill(15)  # 100-114: Valor título
        linha += "00000000000000"  # 115-128: Desconto
        linha += "00000000000000"  # 129-143: Mora/juros
        linha += pagamento.get('data_pagamento', date.today()).strftime("%d%m%Y")  # 144-151: Data pagamento
        linha += str(int(pagamento.get('valor', 0) * 100)).zfill(15)  # 152-166: Valor pagamento
        linha += " " * 15  # 167-181: Quantidade moeda
        linha += " " * 40  # 182-221: Referência sacado
        linha += " " * 2  # 222-223: Uso exclusivo FEBRABAN
        linha += " " * 17  # 224-240: Uso exclusivo
        
        return linha
    
    def _gerar_segmento_tributo(self, pagamento: Dict, numero_lote: int, sequencial: int) -> str:
        """Gera Segmento para Tributo"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += str(numero_lote).zfill(4)  # 004-007: Número lote
        linha += "3"  # 008: Tipo registro
        linha += str(sequencial).zfill(5)  # 009-013: Número registro
        linha += "N"  # 014: Segmento Tributo
        linha += "0"  # 015: Tipo movimento
        linha += "00"  # 016-017: Código movimento
        linha += pagamento.get('codigo_receita', '').zfill(4)  # 018-021: Código receita tributo
        linha += "8"  # 022: Tipo identificação contribuinte (8=CNPJ)
        linha += self.empresa.get('cnpj', '').zfill(14)  # 023-036: CNPJ contribuinte
        linha += pagamento.get('periodo_apuracao', '').zfill(8)  # 037-044: Período apuração
        linha += pagamento.get('numero_referencia', '').ljust(17)  # 045-061: Número referência
        linha += str(int(pagamento.get('valor', 0) * 100)).zfill(15)  # 062-076: Valor principal
        linha += "000000000000000"  # 077-091: Valor mora
        linha += "000000000000000"  # 092-106: Valor multa
        linha += pagamento.get('data_vencimento', date.today()).strftime("%d%m%Y")  # 107-114: Vencimento
        linha += pagamento.get('data_pagamento', date.today()).strftime("%d%m%Y")  # 115-122: Data pagamento
        linha += str(int(pagamento.get('valor', 0) * 100)).zfill(15)  # 123-137: Valor pagamento
        linha += " " * 103  # 138-240: Uso exclusivo
        
        return linha
    
    def _gerar_trailer_lote(self, numero_lote: int, quantidade_registros: int) -> str:
        """Gera trailer de lote (Tipo 5)"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += str(numero_lote).zfill(4)  # 004-007: Número lote
        linha += "5"  # 008: Tipo registro (5=trailer lote)
        linha += " " * 9  # 009-017: Uso exclusivo FEBRABAN
        linha += str(quantidade_registros + 2).zfill(6)  # 018-023: Quantidade registros (inclui header e trailer)
        linha += " " * 217  # 024-240: Uso exclusivo
        
        return linha
    
    def _gerar_trailer_arquivo(self, quantidade_lotes: int, quantidade_registros: int) -> str:
        """Gera trailer do arquivo (Tipo 9)"""
        linha = ""
        linha += self.BANCO_SICREDI.zfill(3)  # 001-003: Código banco
        linha += "9999"  # 004-007: Lote (9999 para trailer)
        linha += "9"  # 008: Tipo registro (9=trailer arquivo)
        linha += " " * 9  # 009-017: Uso exclusivo FEBRABAN
        linha += str(quantidade_lotes).zfill(6)  # 018-023: Quantidade lotes
        linha += str(quantidade_registros + 2).zfill(6)  # 024-029: Quantidade registros (inclui header e trailer arquivo)
        linha += " " * 211  # 030-240: Uso exclusivo
        
        return linha


# =============================================================================
# PROCESSADOR RETORNO CNAB 240
# =============================================================================

class ProcessadorRetornoCNAB240:
    """
    Processador de arquivos de retorno CNAB 240 do Sicredi
    """
    
    def processar_arquivo(self, conteudo: str) -> Dict:
        """
        Processa arquivo de retorno do banco
        
        Args:
            conteudo: Conteúdo do arquivo de retorno
            
        Returns:
            Dict com informações processadas
        """
        linhas = conteudo.strip().split('\n')
        
        resultado = {
            'header_arquivo': {},
            'lotes': [],
            'total_lotes': 0,
            'total_pagamentos': 0,
            'efetuados': 0,
            'rejeitados': 0,
            'agendados': 0,
            'processando': 0
        }
        
        lote_atual = None
        
        for linha in linhas:
            if len(linha) < 240:
                continue
            
            tipo_registro = linha[7]
            
            if tipo_registro == '0':  # Header arquivo
                resultado['header_arquivo'] = self._processar_header_arquivo(linha)
            
            elif tipo_registro == '1':  # Header lote
                if lote_atual:
                    resultado['lotes'].append(lote_atual)
                
                lote_atual = {
                    'numero': int(linha[3:7]),
                    'tipo': linha[9:11],
                    'pagamentos': []
                }
            
            elif tipo_registro == '3':  # Detalhe
                if lote_atual:
                    detalhe = self._processar_detalhe(linha)
                    lote_atual['pagamentos'].append(detalhe)
                    resultado['total_pagamentos'] += 1
                    
                    # Contabilizar status
                    if detalhe['status'] == 'EFETUADO':
                        resultado['efetuados'] += 1
                    elif detalhe['status'] == 'REJEITADO':
                        resultado['rejeitados'] += 1
                    elif detalhe['status'] == 'AGENDADO':
                        resultado['agendados'] += 1
                    else:
                        resultado['processando'] += 1
            
            elif tipo_registro == '5':  # Trailer lote
                if lote_atual:
                    resultado['lotes'].append(lote_atual)
                    resultado['total_lotes'] += 1
                    lote_atual = None
        
        return resultado
    
    def _processar_header_arquivo(self, linha: str) -> Dict:
        """Processa header do arquivo"""
        return {
            'banco': linha[0:3],
            'data_geracao': linha[143:151],
            'hora_geracao': linha[151:157],
            'sequencial': linha[157:163]
        }
    
    def _processar_detalhe(self, linha: str) -> Dict:
        """Processa linha de detalhe"""
        segmento = linha[13]
        codigo_ocorrencia = linha[230:232].strip()
        
        return {
            'segmento': segmento,
            'sequencial': int(linha[8:13]),
            'codigo_ocorrencia': codigo_ocorrencia,
            'descricao_ocorrencia': self._interpretar_ocorrencias(codigo_ocorrencia),
            'status': self._determinar_status(codigo_ocorrencia)
        }
    
    def _interpretar_ocorrencias(self, codigo: str) -> str:
        """Interpreta códigos de ocorrência do retorno"""
        ocorrencias = {
            '00': 'EFETUADO - Pagamento realizado com sucesso',
            '02': 'REJEITADO - Pagamento rejeitado pelo banco',
            'BD': 'DADOS BANCARIOS INVALIDOS',
            'SC': 'SALDO INSUFICIENTE',
            'CA': 'CODIGO BARRAS INVALIDO',
            'TA': 'AGENCIA FAVORECIDO INVALIDA',
            'TC': 'CONTA FAVORECIDO INVALIDA',
            'AG': 'AGENDADO - Pagamento agendado',
            'PR': 'PROCESSANDO - Pagamento em processamento'
        }
        return ocorrencias.get(codigo, f'Código {codigo} desconhecido')
    
    def _determinar_status(self, codigo: str) -> str:
        """Determina status baseado no código de ocorrência"""
        if codigo == '00':
            return 'EFETUADO'
        elif codigo in ['02', 'BD', 'SC', 'CA', 'TA', 'TC']:
            return 'REJEITADO'
        elif codigo == 'AG':
            return 'AGENDADO'
        else:
            return 'PROCESSANDO'


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def gerar_hash_remessa(conteudo: str) -> str:
    """
    Gera hash SHA-256 do conteúdo da remessa para verificação de integridade
    
    Args:
        conteudo: Conteúdo do arquivo CNAB
        
    Returns:
        Hash SHA-256 em formato hexadecimal
    """
    return hashlib.sha256(conteudo.encode('utf-8')).hexdigest()


def formatar_nome_arquivo_remessa(empresa_id: int, sequencial: int, data: date) -> str:
    """
    Formata nome do arquivo de remessa seguindo padrão
    
    Args:
        empresa_id: ID da empresa
        sequencial: Número sequencial da remessa
        data: Data de geração
        
    Returns:
        Nome formatado: REM0001_000123_09022026.txt
    """
    return f"REM{str(empresa_id).zfill(4)}_{str(sequencial).zfill(6)}_{data.strftime('%d%m%Y')}.txt"

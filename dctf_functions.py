# -*- coding: utf-8 -*-
"""
Funções de Geração de DCTF (Declaração de Débitos e Créditos Tributários Federais)

DCTF = Declaração mensal de:
- IRPJ (Imposto de Renda Pessoa Jurídica)
- CSLL (Contribuição Social sobre o Lucro Líquido)
- PIS/PASEP
- COFINS
- IPI
- IRRF (Imposto de Renda Retido na Fonte)

Formato: Arquivo texto delimitado por pipe (|)
"""

from decimal import Decimal
from datetime import datetime, date
import calendar
from database_postgresql import executar_query
from logger_config import logger


def gerar_registro_dctf_00(empresa_id, mes, ano):
    """
    Registro 00 - Abertura do arquivo DCTF
    
    Layout:
    |00|CNPJ|NOME|MES/ANO|TIPO_DECLARACAO|SITUACAO|
    """
    empresa = executar_query(
        "SELECT cnpj, razao_social FROM empresas WHERE id = %s",
        (empresa_id,)
    )[0]
    
    cnpj = empresa['cnpj'].replace('.', '').replace('/', '').replace('-', '')
    nome = empresa['razao_social']
    periodo = f"{mes:02d}{ano}"
    tipo = "1"  # 1=Normal, 2=Retificadora
    situacao = "0"  # 0=Ativo, 1=Inativo
    
    return f"|00|{cnpj}|{nome}|{periodo}|{tipo}|{situacao}|"


def gerar_registro_dctf_10(empresa_id, mes, ano):
    """
    Registro 10 - Identificação da pessoa jurídica
    
    Layout:
    |10|CNPJ|NOME|MUNICIPIO|UF|TELEFONE|EMAIL|
    """
    empresa = executar_query(
        """
        SELECT cnpj, razao_social, municipio, estado, telefone, email
        FROM empresas 
        WHERE id = %s
        """,
        (empresa_id,)
    )[0]
    
    cnpj = empresa['cnpj'].replace('.', '').replace('/', '').replace('-', '')
    nome = empresa['razao_social']
    municipio = empresa.get('municipio', '')
    uf = empresa.get('estado', '')
    telefone = empresa.get('telefone', '')
    email = empresa.get('email', '')
    
    return f"|10|{cnpj}|{nome}|{municipio}|{uf}|{telefone}|{email}|"


def gerar_registros_dctf_50(empresa_id, mes, ano):
    """
    Registro 50 - Débitos e Créditos
    
    Layout:
    |50|CODIGO_RECEITA|PERIODO_APURACAO|VALOR_PRINCIPAL|VALOR_MULTA|VALOR_JUROS|VALOR_TOTAL|
    
    Códigos de Receita principais:
    - 0220: PIS - Folha de Pagamento
    - 2172: PIS - Regime de Apuração Não Cumulativa
    - 2371: COFINS - Regime de Apuração Não Cumulativa
    - 5425: IRPJ - Lucro Real
    - 2030: CSLL
    - 8739: PIS - Importação
    - 8771: COFINS - Importação
    """
    registros = []
    
    # Buscar débitos de PIS/COFINS do período
    # Usando a apuração da EFD-Contribuições
    try:
        from sped_efd_contribuicoes_functions import calcular_apuracao_mensal
        
        apuracao = calcular_apuracao_mensal(empresa_id, mes, ano)
        
        if apuracao.get('success'):
            periodo = f"{mes:02d}{ano}"
            
            # PIS
            valor_pis = Decimal(str(apuracao.get('pis_a_pagar', 0)))
            if valor_pis > 0:
                registros.append(
                    f"|50|2172|{periodo}|{valor_pis:.2f}|0.00|0.00|{valor_pis:.2f}|"
                )
            
            # COFINS
            valor_cofins = Decimal(str(apuracao.get('cofins_a_pagar', 0)))
            if valor_cofins > 0:
                registros.append(
                    f"|50|2371|{periodo}|{valor_cofins:.2f}|0.00|0.00|{valor_cofins:.2f}|"
                )
    
    except Exception as e:
        logger.error(f"Erro ao buscar apuração PIS/COFINS para DCTF: {e}")
    
    # Buscar IRPJ e CSLL
    # Simplificado: Usar lançamentos contábeis das contas de tributos a pagar
    try:
        tributos = executar_query("""
            SELECT 
                pc.codigo,
                pc.nome,
                SUM(CASE WHEN lci.tipo = 'C' THEN lci.valor ELSE -lci.valor END) as saldo
            FROM lancamentos_contabeis_itens lci
            INNER JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id
            INNER JOIN plano_contas pc ON pc.id = lci.conta_id
            WHERE lc.empresa_id = %s
            AND EXTRACT(MONTH FROM lc.data_lancamento) = %s
            AND EXTRACT(YEAR FROM lc.data_lancamento) = %s
            AND pc.codigo IN ('2.01.03.01', '2.01.03.02')  -- IRPJ e CSLL a pagar
            GROUP BY pc.codigo, pc.nome
            HAVING SUM(CASE WHEN lci.tipo = 'C' THEN lci.valor ELSE -lci.valor END) > 0
        """, (empresa_id, mes, ano))
        
        periodo = f"{mes:02d}{ano}"
        
        for tributo in tributos:
            # Identificar código de receita
            if 'IRPJ' in tributo['nome'].upper():
                codigo_receita = "5425"  # IRPJ Lucro Real
            elif 'CSLL' in tributo['nome'].upper():
                codigo_receita = "2030"  # CSLL
            else:
                continue
            
            valor = Decimal(str(tributo['saldo']))
            registros.append(
                f"|50|{codigo_receita}|{periodo}|{valor:.2f}|0.00|0.00|{valor:.2f}|"
            )
    
    except Exception as e:
        logger.error(f"Erro ao buscar IRPJ/CSLL para DCTF: {e}")
    
    return registros


def gerar_registro_dctf_90():
    """
    Registro 90 - Quantidade de registros
    
    Layout:
    |90|TOTAL_REGISTROS|
    """
    # Será calculado ao final
    return "|90|{total}|"


def gerar_arquivo_dctf(empresa_id, mes, ano):
    """
    Gera arquivo DCTF completo
    
    Args:
        empresa_id: ID da empresa
        mes: Mês de referência (1-12)
        ano: Ano de referência
        
    Returns:
        dict: Arquivo DCTF e resumo
    """
    try:
        linhas = []
        
        # Registro 00 - Abertura
        linhas.append(gerar_registro_dctf_00(empresa_id, mes, ano))
        
        # Registro 10 - Identificação
        linhas.append(gerar_registro_dctf_10(empresa_id, mes, ano))
        
        # Registros 50 - Débitos
        registros_50 = gerar_registros_dctf_50(empresa_id, mes, ano)
        linhas.extend(registros_50)
        
        # Registro 90 - Total
        total_registros = len(linhas) + 1
        linhas.append(f"|90|{total_registros}|")
        
        # Montar arquivo
        conteudo = '\n'.join(linhas)
        
        # Calcular totais
        total_debitos = sum([
            Decimal(linha.split('|')[7]) 
            for linha in registros_50 
            if linha.startswith('|50|')
        ])
        
        return {
            'success': True,
            'conteudo': conteudo,
            'nome_arquivo': f"DCTF_{mes:02d}_{ano}.txt",
            'total_linhas': len(linhas),
            'total_debitos': float(total_debitos),
            'quantidade_tributos': len(registros_50)
        }
    
    except Exception as e:
        logger.error(f"Erro ao gerar DCTF: {e}")
        return {
            'success': False,
            'error': str(e)
        }

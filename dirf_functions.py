# -*- coding: utf-8 -*-
"""
Funções de Geração de DIRF (Declaração do Imposto de Renda Retido na Fonte)

DIRF = Declaração anual de:
- Rendimentos pagos a pessoas físicas e jurídicas
- Imposto de renda retido na fonte
- Contribuições previdenciárias
- Pagamentos a planos de saúde

Formato: Arquivo texto delimitado por pipe (|)
Periodicidade: Anual (entrega até último dia útil de fevereiro do ano seguinte)
"""

from decimal import Decimal
from datetime import datetime, date
from database_postgresql import executar_query
from logger_config import logger


def gerar_registro_dirf(tipo_registro, **campos):
    """
    Gera um registro DIRF no formato pipe-delimited
    
    Args:
        tipo_registro: Tipo do registro (DIRF, RESPO, BPFDEC, etc.)
        **campos: Campos do registro
        
    Returns:
        str: Linha formatada
    """
    valores = [str(campos.get(campo, '')) for campo in sorted(campos.keys())]
    return f"|{tipo_registro}|{'|'.join(valores)}|"


def gerar_registro_dirf_header(empresa_id, ano):
    """
    Registro DIRF - Identificação do declarante
    
    Layout:
    |DIRF|ANO_CALENDARIO|ANO_REFERENCIA|CNPJ|NOME|
    """
    empresa = executar_query(
        "SELECT cnpj, razao_social FROM empresas WHERE id = %s",
        (empresa_id,)
    )[0]
    
    cnpj = empresa['cnpj'].replace('.', '').replace('/', '').replace('-', '')
    nome = empresa['razao_social']
    
    return f"|DIRF|{ano}|{ano}|{cnpj}|{nome}|"


def gerar_registro_respo(empresa_id):
    """
    Registro RESPO - Responsável pelas informações
    
    Layout:
    |RESPO|CPF|NOME|DDD|TELEFONE|EMAIL|
    """
    # Buscar dados do responsável (geralmente o contador ou administrador)
    responsavel = executar_query(
        """
        SELECT 
            u.cpf,
            u.nome,
            e.telefone,
            u.email
        FROM usuarios u
        INNER JOIN empresas e ON e.id = u.empresa_id
        WHERE u.empresa_id = %s
        AND u.nivel_acesso = 'admin'
        LIMIT 1
        """,
        (empresa_id,)
    )
    
    if responsavel:
        resp = responsavel[0]
        cpf = resp.get('cpf', '').replace('.', '').replace('-', '')
        nome = resp.get('nome', '')
        telefone = resp.get('telefone', '')
        ddd = telefone[:2] if telefone else ''
        numero = telefone[2:] if len(telefone) > 2 else telefone
        email = resp.get('email', '')
        
        return f"|RESPO|{cpf}|{nome}|{ddd}|{numero}|{email}|"
    
    return "|RESPO||||||"


def gerar_registros_bpfdec(empresa_id, ano):
    """
    Registro BPFDEC - Beneficiários Pessoa Física com rendimentos declarados
    
    Layout:
    |BPFDEC|CPF|NOME|
    
    Depois vem os registros de rendimentos (RTPO, RPPO, etc.)
    """
    # Buscar funcionários ou prestadores de serviço PF que receberam pagamentos
    beneficiarios = executar_query("""
        SELECT DISTINCT
            f.cpf,
            f.nome
        FROM funcionarios f
        WHERE f.empresa_id = %s
        AND EXISTS (
            SELECT 1 FROM pagamentos_salarios ps
            WHERE ps.funcionario_id = f.id
            AND EXTRACT(YEAR FROM ps.data_pagamento) = %s
        )
        ORDER BY f.nome
    """, (empresa_id, ano))
    
    registros = []
    
    for benef in beneficiarios:
        cpf = benef['cpf'].replace('.', '').replace('-', '')
        nome = benef['nome']
        
        registros.append(f"|BPFDEC|{cpf}|{nome}|")
        
        # Buscar rendimentos tributáveis do beneficiário
        rendimentos = executar_query("""
            SELECT 
                EXTRACT(MONTH FROM ps.data_pagamento) as mes,
                SUM(ps.valor_bruto) as valor_bruto,
                SUM(ps.valor_ir_retido) as ir_retido,
                SUM(ps.valor_inss) as inss
            FROM pagamentos_salarios ps
            WHERE ps.funcionario_id = (
                SELECT id FROM funcionarios WHERE cpf = %s AND empresa_id = %s
            )
            AND EXTRACT(YEAR FROM ps.data_pagamento) = %s
            GROUP BY EXTRACT(MONTH FROM ps.data_pagamento)
            ORDER BY mes
        """, (benef['cpf'], empresa_id, ano))
        
        # Totalizar para o ano
        total_rendimentos = Decimal(0)
        total_ir_retido = Decimal(0)
        total_inss = Decimal(0)
        
        for rend in rendimentos:
            total_rendimentos += Decimal(str(rend['valor_bruto']))
            total_ir_retido += Decimal(str(rend['ir_retido']))
            total_inss += Decimal(str(rend['inss']))
        
        # Registro RTPO - Rendimentos Tributáveis de Pessoa Física
        if total_rendimentos > 0:
            registros.append(
                f"|RTPO|{total_rendimentos:.2f}|{total_ir_retido:.2f}|{total_inss:.2f}|"
            )
    
    return registros


def gerar_registros_bpjdec(empresa_id, ano):
    """
    Registro BPJDEC - Beneficiários Pessoa Jurídica com rendimentos declarados
    
    Layout:
    |BPJDEC|CNPJ|NOME|
    
    Depois vem os registros de rendimentos (RTPJ, etc.)
    """
    # Buscar fornecedores PJ que receberam pagamentos com retenção
    beneficiarios = executar_query("""
        SELECT DISTINCT
            f.cnpj,
            f.razao_social
        FROM fornecedores f
        WHERE f.empresa_id = %s
        AND f.cnpj IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM pagamentos p
            WHERE p.fornecedor_id = f.id
            AND EXTRACT(YEAR FROM p.data_pagamento) = %s
            AND p.valor_ir_retido > 0
        )
        ORDER BY f.razao_social
    """, (empresa_id, ano))
    
    registros = []
    
    for benef in beneficiarios:
        cnpj = benef['cnpj'].replace('.', '').replace('/', '').replace('-', '')
        nome = benef['razao_social']
        
        registros.append(f"|BPJDEC|{cnpj}|{nome}|")
        
        # Buscar rendimentos sujeitos à retenção
        rendimentos = executar_query("""
            SELECT 
                EXTRACT(MONTH FROM p.data_pagamento) as mes,
                SUM(p.valor) as valor_pago,
                SUM(p.valor_ir_retido) as ir_retido,
                SUM(p.valor_pis_retido) as pis_retido,
                SUM(p.valor_cofins_retido) as cofins_retido,
                SUM(p.valor_csll_retido) as csll_retido
            FROM pagamentos p
            INNER JOIN fornecedores f ON f.id = p.fornecedor_id
            WHERE f.cnpj = %s
            AND f.empresa_id = %s
            AND EXTRACT(YEAR FROM p.data_pagamento) = %s
            GROUP BY EXTRACT(MONTH FROM p.data_pagamento)
            ORDER BY mes
        """, (benef['cnpj'], empresa_id, ano))
        
        # Totalizar
        total_pago = Decimal(0)
        total_ir = Decimal(0)
        total_pis = Decimal(0)
        total_cofins = Decimal(0)
        total_csll = Decimal(0)
        
        for rend in rendimentos:
            total_pago += Decimal(str(rend['valor_pago']))
            total_ir += Decimal(str(rend['ir_retido']))
            total_pis += Decimal(str(rend['pis_retido']))
            total_cofins += Decimal(str(rend['cofins_retido']))
            total_csll += Decimal(str(rend['csll_retido']))
        
        # Registro RTPJ - Rendimentos a Pessoa Jurídica
        if total_pago > 0:
            registros.append(
                f"|RTPJ|{total_pago:.2f}|{total_ir:.2f}|{total_pis:.2f}|{total_cofins:.2f}|{total_csll:.2f}|"
            )
    
    return registros


def gerar_registro_dirf_fim(total_registros):
    """
    Registro FIM - Encerramento da DIRF
    
    Layout:
    |FIM|TOTAL_REGISTROS|
    """
    return f"|FIM|{total_registros}|"


def gerar_arquivo_dirf(empresa_id, ano):
    """
    Gera arquivo DIRF completo
    
    Args:
        empresa_id: ID da empresa
        ano: Ano de referência (ano-calendário dos rendimentos)
        
    Returns:
        dict: Arquivo DIRF e resumo
    """
    try:
        linhas = []
        
        # Registro DIRF - Header
        linhas.append(gerar_registro_dirf_header(empresa_id, ano))
        
        # Registro RESPO - Responsável
        linhas.append(gerar_registro_respo(empresa_id))
        
        # Registros BPFDEC - Beneficiários PF
        registros_pf = gerar_registros_bpfdec(empresa_id, ano)
        linhas.extend(registros_pf)
        
        # Registros BPJDEC - Beneficiários PJ
        registros_pj = gerar_registros_bpjdec(empresa_id, ano)
        linhas.extend(registros_pj)
        
        # Registro FIM
        total_registros = len(linhas) + 1
        linhas.append(gerar_registro_dirf_fim(total_registros))
        
        # Montar arquivo
        conteudo = '\n'.join(linhas)
        
        # Calcular totais
        total_beneficiarios_pf = len([l for l in registros_pf if l.startswith('|BPFDEC|')])
        total_beneficiarios_pj = len([l for l in registros_pj if l.startswith('|BPJDEC|')])
        
        return {
            'success': True,
            'conteudo': conteudo,
            'nome_arquivo': f"DIRF_{ano}.txt",
            'total_linhas': len(linhas),
            'total_beneficiarios_pf': total_beneficiarios_pf,
            'total_beneficiarios_pj': total_beneficiarios_pj
        }
    
    except Exception as e:
        logger.error(f"Erro ao gerar DIRF: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def obter_resumo_dirf(empresa_id, ano):
    """
    Obtém resumo da DIRF antes de gerar o arquivo
    
    Returns:
        dict: Resumo de rendimentos e retenções
    """
    try:
        # Total pago a pessoas físicas
        pf = executar_query("""
            SELECT 
                COUNT(DISTINCT f.id) as quantidade_beneficiarios,
                SUM(ps.valor_bruto) as total_rendimentos,
                SUM(ps.valor_ir_retido) as total_ir_retido
            FROM funcionarios f
            INNER JOIN pagamentos_salarios ps ON ps.funcionario_id = f.id
            WHERE f.empresa_id = %s
            AND EXTRACT(YEAR FROM ps.data_pagamento) = %s
        """, (empresa_id, ano))
        
        # Total pago a pessoas jurídicas
        pj = executar_query("""
            SELECT 
                COUNT(DISTINCT fr.id) as quantidade_beneficiarios,
                SUM(p.valor) as total_pagamentos,
                SUM(p.valor_ir_retido) as total_ir_retido,
                SUM(p.valor_pis_retido) as total_pis_retido,
                SUM(p.valor_cofins_retido) as total_cofins_retido
            FROM fornecedores fr
            INNER JOIN pagamentos p ON p.fornecedor_id = fr.id
            WHERE fr.empresa_id = %s
            AND EXTRACT(YEAR FROM p.data_pagamento) = %s
            AND p.valor_ir_retido > 0
        """, (empresa_id, ano))
        
        return {
            'success': True,
            'ano': ano,
            'pessoa_fisica': pf[0] if pf else {},
            'pessoa_juridica': pj[0] if pj else {}
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter resumo DIRF: {e}")
        return {
            'success': False,
            'error': str(e)
        }

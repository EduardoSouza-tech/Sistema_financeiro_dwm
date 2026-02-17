"""
Plano de Contas Padrão para Empresas de Software/Tecnologia
Este plano é automaticamente carregado para novas empresas
"""

PLANO_CONTAS_PADRAO = [
    # 1 ATIVO
    {"codigo": "1", "nome": "ATIVO", "classificacao": "ativo", "nivel": 1, "parent_codigo": None},
    
    # 1.1 ATIVO CIRCULANTE
    {"codigo": "1.1", "nome": "ATIVO CIRCULANTE", "classificacao": "ativo", "nivel": 2, "parent_codigo": "1"},
    
    # 1.1.01 DISPONÍVEL
    {"codigo": "1.1.01", "nome": "DISPONÍVEL", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.1"},
    {"codigo": "1.1.01.001", "nome": "CAIXA", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.01"},
    {"codigo": "1.1.01.002", "nome": "BANCOS CONTA MOVIMENTO", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.01"},
    {"codigo": "1.1.01.003", "nome": "APLICAÇÕES FINANCEIRAS", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.01"},
    
    # 1.1.02 CLIENTES
    {"codigo": "1.1.02", "nome": "CLIENTES", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.1"},
    {"codigo": "1.1.02.001", "nome": "DUPLICATAS A RECEBER", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.02"},
    {"codigo": "1.1.02.002", "nome": "CLIENTES DIVERSOS", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.02"},
    
    # 1.1.03 IMPOSTOS A RECUPERAR
    {"codigo": "1.1.03", "nome": "IMPOSTOS A RECUPERAR", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.1"},
    {"codigo": "1.1.03.001", "nome": "IRPJ A RECUPERAR", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.03"},
    {"codigo": "1.1.03.002", "nome": "CSLL A RECUPERAR", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.03"},
    {"codigo": "1.1.03.003", "nome": "PIS A RECUPERAR", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.03"},
    {"codigo": "1.1.03.004", "nome": "COFINS A RECUPERAR", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.03"},
    {"codigo": "1.1.03.005", "nome": "INSS A RECUPERAR", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.03"},
    
    # 1.1.04 OUTROS CRÉDITOS
    {"codigo": "1.1.04", "nome": "OUTROS CRÉDITOS", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.1"},
    {"codigo": "1.1.04.001", "nome": "ADIANTAMENTOS A FORNECEDORES", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.04"},
    {"codigo": "1.1.04.002", "nome": "ADIANTAMENTOS A EMPREGADOS", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.1.04"},
    
    # 1.2 ATIVO NÃO CIRCULANTE
    {"codigo": "1.2", "nome": "ATIVO NÃO CIRCULANTE", "classificacao": "ativo", "nivel": 2, "parent_codigo": "1"},
    
    # 1.2.01 REALIZÁVEL A LONGO PRAZO
    {"codigo": "1.2.01", "nome": "REALIZÁVEL A LONGO PRAZO", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.2"},
    {"codigo": "1.2.01.001", "nome": "CLIENTES LP", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.01"},
    
    # 1.2.02 IMOBILIZADO
    {"codigo": "1.2.02", "nome": "IMOBILIZADO", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.2"},
    {"codigo": "1.2.02.001", "nome": "COMPUTADORES E EQUIPAMENTOS", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.02"},
    {"codigo": "1.2.02.002", "nome": "MÓVEIS E UTENSÍLIOS", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.02"},
    {"codigo": "1.2.02.003", "nome": "INSTALAÇÕES", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.02"},
    {"codigo": "1.2.02.004", "nome": "VEÍCULOS", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.02"},
    {"codigo": "1.2.02.005", "nome": "(-) DEPRECIAÇÃO ACUMULADA", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.02"},
    
    # 1.2.03 INTANGÍVEL
    {"codigo": "1.2.03", "nome": "INTANGÍVEL", "classificacao": "ativo", "nivel": 3, "parent_codigo": "1.2"},
    {"codigo": "1.2.03.001", "nome": "SOFTWARES", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.03"},
    {"codigo": "1.2.03.002", "nome": "MARCAS E PATENTES", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.03"},
    {"codigo": "1.2.03.003", "nome": "(-) AMORTIZAÇÃO ACUMULADA", "classificacao": "ativo", "nivel": 4, "parent_codigo": "1.2.03"},
    
    # 2 PASSIVO
    {"codigo": "2", "nome": "PASSIVO", "classificacao": "passivo", "nivel": 1, "parent_codigo": None},
    
    # 2.1 PASSIVO CIRCULANTE
    {"codigo": "2.1", "nome": "PASSIVO CIRCULANTE", "classificacao": "passivo", "nivel": 2, "parent_codigo": "2"},
    
    # 2.1.01 FORNECEDORES
    {"codigo": "2.1.01", "nome": "FORNECEDORES", "classificacao": "passivo", "nivel": 3, "parent_codigo": "2.1"},
    {"codigo": "2.1.01.001", "nome": "FORNECEDORES NACIONAIS", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.01"},
    
    # 2.1.02 OBRIGAÇÕES TRABALHISTAS
    {"codigo": "2.1.02", "nome": "OBRIGAÇÕES TRABALHISTAS", "classificacao": "passivo", "nivel": 3, "parent_codigo": "2.1"},
    {"codigo": "2.1.02.001", "nome": "SALÁRIOS A PAGAR", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.02"},
    {"codigo": "2.1.02.002", "nome": "PRÓ-LABORE A PAGAR", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.02"},
    {"codigo": "2.1.02.003", "nome": "INSS A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.02"},
    {"codigo": "2.1.02.004", "nome": "FGTS A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.02"},
    
    # 2.1.03 OBRIGAÇÕES TRIBUTÁRIAS
    {"codigo": "2.1.03", "nome": "OBRIGAÇÕES TRIBUTÁRIAS", "classificacao": "passivo", "nivel": 3, "parent_codigo": "2.1"},
    {"codigo": "2.1.03.001", "nome": "SIMPLES NACIONAL A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.03"},
    {"codigo": "2.1.03.002", "nome": "ISS A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.03"},
    {"codigo": "2.1.03.003", "nome": "IRRF A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.03"},
    {"codigo": "2.1.03.004", "nome": "PIS A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.03"},
    {"codigo": "2.1.03.005", "nome": "COFINS A RECOLHER", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.03"},
    
    # 2.1.04 EMPRÉSTIMOS E FINANCIAMENTOS
    {"codigo": "2.1.04", "nome": "EMPRÉSTIMOS E FINANCIAMENTOS", "classificacao": "passivo", "nivel": 3, "parent_codigo": "2.1"},
    {"codigo": "2.1.04.001", "nome": "EMPRÉSTIMOS BANCÁRIOS CP", "classificacao": "passivo", "nivel": 4, "parent_codigo": "2.1.04"},
    
    # 2.2 PASSIVO NÃO CIRCULANTE
    {"codigo": "2.2", "nome": "PASSIVO NÃO CIRCULANTE", "classificacao": "passivo", "nivel": 2, "parent_codigo": "2"},
    {"codigo": "2.2.01", "nome": "EMPRÉSTIMOS E FINANCIAMENTOS LP", "classificacao": "passivo", "nivel": 3, "parent_codigo": "2.2"},
    {"codigo": "2.2.02", "nome": "PARCELAMENTOS TRIBUTÁRIOS LP", "classificacao": "passivo", "nivel": 3, "parent_codigo": "2.2"},
    
    # 3 PATRIMÔNIO LÍQUIDO
    {"codigo": "3", "nome": "PATRIMÔNIO LÍQUIDO", "classificacao": "patrimonio_liquido", "nivel": 1, "parent_codigo": None},
    
    # 3.1 CAPITAL SOCIAL
    {"codigo": "3.1", "nome": "CAPITAL SOCIAL", "classificacao": "patrimonio_liquido", "nivel": 2, "parent_codigo": "3"},
    {"codigo": "3.1.01", "nome": "CAPITAL SOCIAL INTEGRALIZADO", "classificacao": "patrimonio_liquido", "nivel": 3, "parent_codigo": "3.1"},
    
    # 3.2 RESERVAS
    {"codigo": "3.2", "nome": "RESERVAS", "classificacao": "patrimonio_liquido", "nivel": 2, "parent_codigo": "3"},
    {"codigo": "3.2.01", "nome": "RESERVA LEGAL", "classificacao": "patrimonio_liquido", "nivel": 3, "parent_codigo": "3.2"},
    {"codigo": "3.2.02", "nome": "LUCROS ACUMULADOS", "classificacao": "patrimonio_liquido", "nivel": 3, "parent_codigo": "3.2"},
    
    # 3.3 RESULTADO DO EXERCÍCIO
    {"codigo": "3.3", "nome": "RESULTADO DO EXERCÍCIO", "classificacao": "patrimonio_liquido", "nivel": 2, "parent_codigo": "3"},
    
    # 4 RECEITAS
    {"codigo": "4", "nome": "RECEITAS", "classificacao": "receita", "nivel": 1, "parent_codigo": None},
    
    # 4.1 RECEITA BRUTA
    {"codigo": "4.1", "nome": "RECEITA BRUTA", "classificacao": "receita", "nivel": 2, "parent_codigo": "4"},
    {"codigo": "4.1.01", "nome": "RECEITA DE LICENCIAMENTO DE SOFTWARE", "classificacao": "receita", "nivel": 3, "parent_codigo": "4.1"},
    {"codigo": "4.1.02", "nome": "RECEITA DE DESENVOLVIMENTO SOB ENCOMENDA", "classificacao": "receita", "nivel": 3, "parent_codigo": "4.1"},
    {"codigo": "4.1.03", "nome": "RECEITA DE SUPORTE TÉCNICO", "classificacao": "receita", "nivel": 3, "parent_codigo": "4.1"},
    {"codigo": "4.1.04", "nome": "RECEITA DE MANUTENÇÃO", "classificacao": "receita", "nivel": 3, "parent_codigo": "4.1"},
    
    # 4.2 (-) DEDUÇÕES DA RECEITA
    {"codigo": "4.2", "nome": "(-) DEDUÇÕES DA RECEITA", "classificacao": "receita", "nivel": 2, "parent_codigo": "4"},
    {"codigo": "4.2.01", "nome": "IMPOSTOS SOBRE RECEITA (SN)", "classificacao": "receita", "nivel": 3, "parent_codigo": "4.2"},
    {"codigo": "4.2.02", "nome": "CANCELAMENTOS E DESCONTOS", "classificacao": "receita", "nivel": 3, "parent_codigo": "4.2"},
    
    # 5 CUSTOS
    {"codigo": "5", "nome": "CUSTOS", "classificacao": "despesa", "nivel": 1, "parent_codigo": None},
    
    # 5.1 CUSTOS DIRETOS
    {"codigo": "5.1", "nome": "CUSTOS DIRETOS", "classificacao": "despesa", "nivel": 2, "parent_codigo": "5"},
    {"codigo": "5.1.01", "nome": "MÃO DE OBRA DIRETA", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.1"},
    {"codigo": "5.1.02", "nome": "ENCARGOS SOCIAIS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.1"},
    {"codigo": "5.1.03", "nome": "HOSPEDAGEM SERVIDORES", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.1"},
    {"codigo": "5.1.04", "nome": "LICENÇAS DE SOFTWARE", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.1"},
    {"codigo": "5.1.05", "nome": "SERVIÇOS TERCEIRIZADOS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.1"},
    
    # 5.2 CUSTOS INDIRETOS
    {"codigo": "5.2", "nome": "CUSTOS INDIRETOS", "classificacao": "despesa", "nivel": 2, "parent_codigo": "5"},
    {"codigo": "5.2.01", "nome": "ENERGIA ELÉTRICA PRODUÇÃO", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.2"},
    {"codigo": "5.2.02", "nome": "INTERNET PRODUÇÃO", "classificacao": "despesa", "nivel": 3, "parent_codigo": "5.2"},
    
    # 6 DESPESAS OPERACIONAIS
    {"codigo": "6", "nome": "DESPESAS OPERACIONAIS", "classificacao": "despesa", "nivel": 1, "parent_codigo": None},
    
    # 6.1 DESPESAS ADMINISTRATIVAS
    {"codigo": "6.1", "nome": "DESPESAS ADMINISTRATIVAS", "classificacao": "despesa", "nivel": 2, "parent_codigo": "6"},
    {"codigo": "6.1.01", "nome": "ALUGUEL", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.02", "nome": "CONDOMÍNIO", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.03", "nome": "ENERGIA ELÉTRICA", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.04", "nome": "INTERNET", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.05", "nome": "TELEFONE", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.06", "nome": "MATERIAL DE ESCRITÓRIO", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.07", "nome": "HONORÁRIOS CONTÁBEIS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    {"codigo": "6.1.08", "nome": "SISTEMAS E ASSINATURAS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.1"},
    
    # 6.2 DESPESAS COM PESSOAL
    {"codigo": "6.2", "nome": "DESPESAS COM PESSOAL", "classificacao": "despesa", "nivel": 2, "parent_codigo": "6"},
    {"codigo": "6.2.01", "nome": "SALÁRIOS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.2"},
    {"codigo": "6.2.02", "nome": "PRÓ-LABORE", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.2"},
    {"codigo": "6.2.03", "nome": "INSS PATRONAL", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.2"},
    {"codigo": "6.2.04", "nome": "FGTS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.2"},
    {"codigo": "6.2.05", "nome": "FÉRIAS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.2"},
    {"codigo": "6.2.06", "nome": "13º SALÁRIO", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.2"},
    
    # 6.3 DESPESAS FINANCEIRAS
    {"codigo": "6.3", "nome": "DESPESAS FINANCEIRAS", "classificacao": "despesa", "nivel": 2, "parent_codigo": "6"},
    {"codigo": "6.3.01", "nome": "JUROS PASSIVOS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.3"},
    {"codigo": "6.3.02", "nome": "MULTAS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.3"},
    {"codigo": "6.3.03", "nome": "TARIFAS BANCÁRIAS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.3"},
    
    # 6.4 DESPESAS TRIBUTÁRIAS
    {"codigo": "6.4", "nome": "DESPESAS TRIBUTÁRIAS", "classificacao": "despesa", "nivel": 2, "parent_codigo": "6"},
    {"codigo": "6.4.01", "nome": "ISS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.4"},
    {"codigo": "6.4.02", "nome": "TAXAS MUNICIPAIS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.4"},
    {"codigo": "6.4.03", "nome": "OUTROS TRIBUTOS", "classificacao": "despesa", "nivel": 3, "parent_codigo": "6.4"},
    
    # 7 RESULTADO
    {"codigo": "7", "nome": "RESULTADO", "classificacao": "resultado", "nivel": 1, "parent_codigo": None},
    {"codigo": "7.1", "nome": "RESULTADO OPERACIONAL", "classificacao": "resultado", "nivel": 2, "parent_codigo": "7"},
    {"codigo": "7.2", "nome": "RESULTADO ANTES IR/CS", "classificacao": "resultado", "nivel": 2, "parent_codigo": "7"},
    {"codigo": "7.3", "nome": "LUCRO LÍQUIDO DO EXERCÍCIO", "classificacao": "resultado", "nivel": 2, "parent_codigo": "7"},
]


def obter_plano_contas_padrao():
    """
    Retorna o plano de contas padrão
    """
    return PLANO_CONTAS_PADRAO.copy()


def contar_contas():
    """
    Retorna estatísticas do plano de contas padrão
    """
    return {
        'total': len(PLANO_CONTAS_PADRAO),
        'ativo': len([c for c in PLANO_CONTAS_PADRAO if c['classificacao'] == 'ativo']),
        'passivo': len([c for c in PLANO_CONTAS_PADRAO if c['classificacao'] == 'passivo']),
        'patrimonio_liquido': len([c for c in PLANO_CONTAS_PADRAO if c['classificacao'] == 'patrimonio_liquido']),
        'receita': len([c for c in PLANO_CONTAS_PADRAO if c['classificacao'] == 'receita']),
        'despesa': len([c for c in PLANO_CONTAS_PADRAO if c['classificacao'] == 'despesa']),
        'resultado': len([c for c in PLANO_CONTAS_PADRAO if c['classificacao'] == 'resultado']),
    }

# -*- coding: utf-8 -*-
"""
SPED EFD-Contribuições - Escrituração Fiscal Digital de PIS/PASEP e COFINS
Geração de arquivo EFD-Contribuições conforme layout SPED
"""

from datetime import datetime
from decimal import Decimal
from database_postgresql import get_connection
import hashlib
import calendar


def formatar_valor(valor):
    """Formata valor para o padrão SPED (sem separador de milhar, vírgula decimal, 2 casas)"""
    if valor is None:
        return "0,00"
    valor_decimal = Decimal(str(valor))
    valor_formatado = f"{abs(valor_decimal):.2f}".replace('.', ',')
    return valor_formatado


def formatar_data(data):
    """Formata data para o padrão SPED: ddmmaaaa"""
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d')
    return data.strftime('%d%m%Y')


def formatar_mes(data):
    """Formata mês/ano para o padrão SPED: mmaaaa"""
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d')
    return data.strftime('%m%Y')


def gerar_hash_arquivo(conteudo):
    """Gera hash MD5 do arquivo para validação"""
    return hashlib.md5(conteudo.encode('utf-8')).hexdigest().upper()


def obter_regime_tributario(empresa_id):
    """
    Obtém regime tributário da empresa
    1 = Lucro Real
    2 = Lucro Presumido
    3 = Simples Nacional
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Por enquanto, retorna Lucro Presumido como padrão
        # Em produção, isso deveria vir de uma tabela de configuração da empresa
        return 2  # Lucro Presumido
    finally:
        cursor.close()
        conn.close()


def obter_aliquotas_pis_cofins(regime_tributario):
    """
    Retorna alíquotas de PIS/COFINS conforme regime
    
    Regime 1 (Lucro Real - Não Cumulativo):
        PIS: 1,65%
        COFINS: 7,6%
    
    Regime 2 (Lucro Presumido - Cumulativo):
        PIS: 0,65%
        COFINS: 3,0%
    
    Regime 3 (Simples Nacional):
        PIS/COFINS inclusos no DAS
        Retorna 0
    """
    if regime_tributario == 1:  # Lucro Real (Não Cumulativo)
        return {'pis': Decimal('1.65'), 'cofins': Decimal('7.6')}
    elif regime_tributario == 2:  # Lucro Presumido (Cumulativo)
        return {'pis': Decimal('0.65'), 'cofins': Decimal('3.0')}
    else:  # Simples Nacional
        return {'pis': Decimal('0'), 'cofins': Decimal('0')}


# ==================== BLOCO 0 - ABERTURA ====================

def gerar_registro_0000(empresa_id, data_inicio, data_fim):
    """
    0000: ABERTURA DO ARQUIVO DIGITAL E IDENTIFICAÇÃO DA PESSOA JURÍDICA
    
    Campos:
    01 - REG: 0000
    02 - COD_VER: Código versão leiaute (012)
    03 - TIPO_ESCRIT: Tipo escrituração (0=Original, 1=Retificadora)
    04 - IND_SIT_ESP: Indicador situação especial
    05 - NUM_REC_ANTERIOR: Número recibo anterior (se retificadora)
    06 - DT_INI: Data inicial
    07 - DT_FIN: Data final
    08 - NOME: Nome empresarial
    09 - CNPJ: CNPJ
    10 - UF: Sigla UF
    11 - COD_MUN: Código município (IBGE)
    12 - SUFRAMA: Inscrição SUFRAMA
    13 - IND_NAT_PJ: Natureza PJ (00=Sociedade empresária, 01=SCP, etc)
    14 - IND_ATIV: Indicador atividade (0=Industrial, 1=Prestador serviços, etc)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT nome, cnpj, estado, cidade
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        empresa = cursor.fetchone()
        if not empresa:
            return None
        
        nome, cnpj, uf, cidade = empresa
        
        # Formatar CNPJ (apenas números)
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj or ''))
        
        registro = (
            f"|0000|"
            f"012|"  # Versão leiaute
            f"0|"    # Tipo escrituração (0=Original)
            f"|"     # IND_SIT_ESP
            f"|"     # NUM_REC_ANTERIOR
            f"{formatar_data(data_inicio)}|"
            f"{formatar_data(data_fim)}|"
            f"{nome}|"
            f"{cnpj_limpo}|"
            f"{uf or ''}|"
            f"|"     # COD_MUN
            f"|"     # SUFRAMA
            f"00|"   # IND_NAT_PJ (00=Sociedade empresária)
            f"1|"    # IND_ATIV (1=Prestador de serviços)
        )
        
        return registro
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_0001():
    """0001: ABERTURA DO BLOCO 0"""
    return "|0001|0|"


def gerar_registro_0110(empresa_id):
    """
    0110: REGIMES DE APURAÇÃO DA CONTRIBUIÇÃO SOCIAL E DE APROPRIAÇÃO DE CRÉDITO
    
    Campos:
    01 - REG: 0110
    02 - COD_INC_TRIB: Código indicador incidência tributária (1=Escrit. op. incidentes)
    03 - IND_APRO_CRED: Indicador apropriação crédito (1=Apropriação direta)
    04 - COD_TIPO_CONT: Código tipo contribuição (1=Alíquota básica)
    05 - IND_REG_CUM: Indicador regime cumulativo (1=Regime cumulativo)
    """
    regime = obter_regime_tributario(empresa_id)
    ind_reg_cum = "1" if regime == 2 else "2"  # 1=Cumulativo, 2=Não cumulativo
    
    registro = (
        f"|0110|"
        f"1|"  # COD_INC_TRIB
        f"1|"  # IND_APRO_CRED
        f"1|"  # COD_TIPO_CONT
        f"{ind_reg_cum}|"
    )
    return registro


def gerar_registro_0140(empresa_id):
    """
    0140: TABELA DE CADASTRO DE ESTABELECIMENTO
    
    Campos:
    01 - REG: 0140
    02 - COD_EST: Código estabelecimento
    03 - NOME: Nome estabelecimento
    04 - CNPJ: CNPJ
    05 - UF: UF
    06 - IE: Inscrição estadual
    07 - COD_MUN: Código município
    08 - IM: Inscrição municipal
    09 - SUFRAMA: SUFRAMA
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, nome, cnpj, estado, inscricao_estadual, inscricao_municipal
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        empresa = cursor.fetchone()
        if not empresa:
            return None
        
        est_id, nome, cnpj, uf, ie, im = empresa
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj or ''))
        
        registro = (
            f"|0140|"
            f"{est_id}|"
            f"{nome}|"
            f"{cnpj_limpo}|"
            f"{uf or ''}|"
            f"{ie or ''}|"
            f"|"  # COD_MUN
            f"{im or ''}|"
            f"|"  # SUFRAMA
        )
        
        return registro
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_0990(qtd_linhas):
    """0990: ENCERRAMENTO DO BLOCO 0"""
    return f"|0990|{qtd_linhas}|"


# ==================== BLOCO C - DOCUMENTOS FISCAIS (SERVIÇOS) ====================

def gerar_registro_C001():
    """C001: ABERTURA DO BLOCO C"""
    return "|C001|0|"


def gerar_registro_C010(mes_ano):
    """
    C010: IDENTIFICAÇÃO DO ESTABELECIMENTO
    
    Campos:
    01 - REG: C010
    02 - CNPJ: CNPJ estabelecimento
    03 - IND_ESCRI: Indicador escrituração (1=Consolidada)
    """
    # Simplificado - em produção deveria buscar CNPJ do estabelecimento
    return "|C010||1|"


def gerar_registros_C100_C170_C181(empresa_id, data_inicio, data_fim):
    """
    C100: NOTA FISCAL (SERVIÇOS)
    C170: COMPLEMENTO (Itens)
    C181: DETALHAMENTO PIS/COFINS (OP. RECEITAS)
    
    Simplificado: Usa lançamentos contábeis de receita como base
    Em produção, deveria usar tabela de notas fiscais (NFS-e)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar receitas do período (simplificado)
        cursor.execute("""
            SELECT 
                lc.id,
                lc.numero_lancamento,
                lc.data,
                lc.historico,
                SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END) as valor_receita
            FROM lancamentos_contabeis lc
            JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            WHERE lc.empresa_id = %s
                AND lc.data >= %s
                AND lc.data <= %s
                AND lc.is_estornado = false
                AND pc.classificacao = 'receita'
            GROUP BY lc.id, lc.numero_lancamento, lc.data, lc.historico
            HAVING SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END) > 0
            ORDER BY lc.data, lc.numero_lancamento
        """, (empresa_id, data_inicio, data_fim))
        
        receitas = cursor.fetchall()
        
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        for idx, receita in enumerate(receitas, 1):
            lanc_id, num_lanc, data_doc, historico, valor_receita = receita
            
            # Registro C100 (simplificado - seria NFS-e)
            # Em produção, teria mais campos (cliente, município, etc)
            registro_c100 = (
                f"|C100|"
                f"1|"  # IND_OPER (1=Entrada/aquisição)
                f"1|"  # IND_EMIT (1=Emissão própria)
                f"65|"  # COD_PART (código participante - simplificado)
                f"NFS|"  # COD_MOD (Nota Fiscal de Serviços)
                f"1|"  # COD_SIT (1=Normal)
                f"1|"  # SER (Série)
                f"{num_lanc}|"  # NUM_DOC
                f"|"  # CHV_NFE
                f"{formatar_data(data_doc)}|"  # DT_DOC
                f"{formatar_data(data_doc)}|"  # DT_E_S
                f"{formatar_valor(valor_receita)}|"  # VL_DOC
                f"|"  # IND_PGTO
                f"{formatar_valor(valor_receita)}|"  # VL_DESC
                f"0,00|"  # VL_ABAT_NT
                f"{formatar_valor(valor_receita)}|"  # VL_MERC
                f"|"  # IND_FRT
                f"0,00|"  # VL_FRT
                f"0,00|"  # VL_SEG
                f"0,00|"  # VL_OUT_DA
                f"0,00|"  # VL_BC_ICMS
                f"0,00|"  # VL_ICMS
                f"0,00|"  # VL_BC_ICMS_ST
                f"0,00|"  # VL_ICMS_ST
                f"0,00|"  # VL_IPI
                f"{formatar_valor(valor_receita)}|"  # VL_PIS
                f"{formatar_valor(valor_receita)}|"  # VL_COFINS
                f"{formatar_valor(valor_receita)}|"  # VL_PIS_ST
                f"{formatar_valor(valor_receita)}|"  # VL_COFINS_ST
            )
            registros.append(registro_c100)
            
            # Registro C170 (Item da nota - simplificado)
            valor_pis = valor_receita * aliquotas['pis'] / 100
            valor_cofins = valor_receita * aliquotas['cofins'] / 100
            
            registro_c170 = (
                f"|C170|"
                f"1|"  # NUM_ITEM
                f"SERVICO|"  # COD_ITEM
                f"Serviços prestados - {historico[:50]}|"  # DESCR_COMPL
                f"1,00|"  # QTD
                f"UN|"  # UNID
                f"{formatar_valor(valor_receita)}|"  # VL_ITEM
                f"0,00|"  # VL_DESC
                f"|"  # IND_MOV
                f"5933|"  # CST_ICMS (simplificado)
                f"0,00|"  # CFOP assumindo prestação serviço
                f"|"  # COD_NAT
                f"0,00|"  # VL_BC_ICMS
                f"0,00|"  # ALIQ_ICMS
                f"0,00|"  # VL_ICMS
                f"0,00|"  # VL_BC_ICMS_ST
                f"0,00|"  # ALIQ_ST
                f"0,00|"  # VL_ICMS_ST
                f"|"  # IND_APUR
                f"50|"  # CST_PIS (50=Op. tributável, regime monofásico)
                f"{formatar_valor(valor_receita)}|"  # VL_BC_PIS
                f"{formatar_valor(aliquotas['pis'])}|"  # ALIQ_PIS (%)
                f"0,00|"  # QUANT_BC_PIS
                f"0,00|"  # ALIQ_PIS (R$)
                f"{formatar_valor(valor_pis)}|"  # VL_PIS
                f"50|"  # CST_COFINS
                f"{formatar_valor(valor_receita)}|"  # VL_BC_COFINS
                f"{formatar_valor(aliquotas['cofins'])}|"  # ALIQ_COFINS (%)
                f"0,00|"  # QUANT_BC_COFINS
                f"0,00|"  # ALIQ_COFINS (R$)
                f"{formatar_valor(valor_cofins)}|"  # VL_COFINS
                f"|"  # COD_CTA
            )
            registros.append(registro_c170)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_C990(qtd_linhas):
    """C990: ENCERRAMENTO DO BLOCO C"""
    return f"|C990|{qtd_linhas}|"


# ==================== BLOCO M - APURAÇÃO DAS CONTRIBUIÇÕES ====================

def gerar_registro_M001():
    """M001: ABERTURA DO BLOCO M"""
    return "|M001|0|"


def gerar_registro_M100_M110(empresa_id, data_inicio, data_fim):
    """
    M100: CRÉDITO DE PIS/PASEP RELATIVO AO PERÍODO
    M110: AJUSTES DO CRÉDITO DE PIS/PASEP DO PERÍODO
    
    Simplificado: Calcula créditos básicos
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar total de receitas tributáveis
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) as total_receitas
            FROM lancamentos_contabeis lc
            JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            WHERE lc.empresa_id = %s
                AND lc.data >= %s
                AND lc.data <= %s
                AND lc.is_estornado = false
                AND pc.classificacao = 'receita'
        """, (empresa_id, data_inicio, data_fim))
        
        result = cursor.fetchone()
        total_receitas = result[0] if result else 0
        
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        # Calcular PIS
        base_calculo_pis = total_receitas
        aliq_pis = aliquotas['pis']
        valor_pis = base_calculo_pis * aliq_pis / 100
        
        # M100 - Crédito PIS
        registro_m100 = (
            f"|M100|"
            f"01|"  # COD_CRED (01=Alíquota básica)
            f"|"  # IND_CRED_ORI
            f"{formatar_valor(base_calculo_pis)}|"  # VL_BC_PIS
            f"{formatar_valor(aliq_pis)}|"  # ALIQ_PIS
            f"0,00|"  # QUANT_BC_PIS
            f"0,00|"  # ALIQ_PIS_QUANT
            f"{formatar_valor(valor_pis)}|"  # VL_CRED
            f"|"  # VL_AJUS_ACRES
            f"|"  # VL_AJUS_REDUC
            f"{formatar_valor(valor_pis)}|"  # VL_CRED_DIF
            f"{formatar_valor(valor_pis)}|"  # VL_CRED_DISP
            f"|"  # IND_DESC_CRED
            f"|"  # VL_CRED_DESC
            f"|"  # SLD_CRED
        )
        registros.append(registro_m100)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_M200_M210(empresa_id, data_inicio, data_fim):
    """
    M200: CONTRIBUIÇÃO PARA O PIS/PASEP DO PERÍODO
    M210: DETALHAMENTO DA CONTRIBUIÇÃO
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar total de receitas tributáveis
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) as total_receitas
            FROM lancamentos_contabeis lc
            JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            WHERE lc.empresa_id = %s
                AND lc.data >= %s
                AND lc.data <= %s
                AND lc.is_estornado = false
                AND pc.classificacao = 'receita'
        """, (empresa_id, data_inicio, data_fim))
        
        result = cursor.fetchone()
        total_receitas = result[0] if result else 0
        
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        # Calcular contributição PIS
        base_calculo = total_receitas
        aliq_pis = aliquotas['pis']
        valor_contribuicao_pis = base_calculo * aliq_pis / 100
        
        # M200 - Consolidação da contribuição
        registro_m200 = (
            f"|M200|"
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_TOT_CONT_NC_PER
            f"0,00|"  # VL_TOT_CRED_DESC
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_TOT_CONT_NC_DEV
            f"0,00|"  # VL_RET_NC
            f"0,00|"  # VL_OUT_DED_NC
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_CONT_NC_REC
            f"0,00|"  # VL_TOT_CONT_CUM_PER
            f"0,00|"  # VL_RET_CUM
            f"0,00|"  # VL_OUT_DED_CUM
            f"0,00|"  # VL_CONT_CUM_REC
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_TOT_CONT_REC
        )
        registros.append(registro_m200)
        
        # M210 - Detalhamento
        registro_m210 = (
            f"|M210|"
            f"01|"  # COD_CONT (01=PIS sobre receitas)
            f"{formatar_valor(base_calculo)}|"  # VL_REC_BRT
            f"{formatar_valor(base_calculo)}|"  # VL_BC_CONT
            f"{formatar_valor(aliq_pis)}|"  # ALIQ_PIS
            f"0,00|"  # QUANT_BC_PIS
            f"0,00|"  # ALIQ_PIS_QUANT
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_CONT_APUR
            f"|"  # VL_AJUS_ACRES
            f"|"  # VL_AJUS_REDUC
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_CONT_DIFER
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_CONT_DIFER_ANT
            f"{formatar_valor(valor_contribuicao_pis)}|"  # VL_CONT_PER
        )
        registros.append(registro_m210)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_M500_M510(empresa_id, data_inicio, data_fim):
    """
    M500: CRÉDITO DE COFINS RELATIVO AO PERÍODO
    M510: AJUSTES DO CRÉDITO DE COFINS DO PERÍODO
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) as total_receitas
            FROM lancamentos_contabeis lc
            JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            WHERE lc.empresa_id = %s
                AND lc.data >= %s
                AND lc.data <= %s
                AND lc.is_estornado = false
                AND pc.classificacao = 'receita'
        """, (empresa_id, data_inicio, data_fim))
        
        result = cursor.fetchone()
        total_receitas = result[0] if result else 0
        
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        # Calcular COFINS
        base_calculo_cofins = total_receitas
        aliq_cofins = aliquotas['cofins']
        valor_cofins = base_calculo_cofins * aliq_cofins / 100
        
        # M500 - Crédito COFINS
        registro_m500 = (
            f"|M500|"
            f"01|"  # COD_CRED
            f"|"  # IND_CRED_ORI
            f"{formatar_valor(base_calculo_cofins)}|"  # VL_BC_COFINS
            f"{formatar_valor(aliq_cofins)}|"  # ALIQ_COFINS
            f"0,00|"  # QUANT_BC_COFINS
            f"0,00|"  # ALIQ_COFINS_QUANT
            f"{formatar_valor(valor_cofins)}|"  # VL_CRED
            f"|"  # VL_AJUS_ACRES
            f"|"  # VL_AJUS_REDUC
            f"{formatar_valor(valor_cofins)}|"  # VL_CRED_DIF
            f"{formatar_valor(valor_cofins)}|"  # VL_CRED_DISP
            f"|"  # IND_DESC_CRED
            f"|"  # VL_CRED_DESC
            f"|"  # SLD_CRED
        )
        registros.append(registro_m500)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_M600_M610(empresa_id, data_inicio, data_fim):
    """
    M600: CONTRIBUIÇÃO PARA A COFINS DO PERÍODO
    M610: DETALHAMENTO DA CONTRIBUIÇÃO
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0) as total_receitas
            FROM lancamentos_contabeis lc
            JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            JOIN plano_contas pc ON pc.id = lci.plano_contas_id
            WHERE lc.empresa_id = %s
                AND lc.data >= %s
                AND lc.data <= %s
                AND lc.is_estornado = false
                AND pc.classificacao = 'receita'
        """, (empresa_id, data_inicio, data_fim))
        
        result = cursor.fetchone()
        total_receitas = result[0] if result else 0
        
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        # Calcular COFINS
        base_calculo = total_receitas
        aliq_cofins = aliquotas['cofins']
        valor_contribuicao_cofins = base_calculo * aliq_cofins / 100
        
        # M600 - Consolidação COFINS
        registro_m600 = (
            f"|M600|"
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_TOT_CONT_NC_PER
            f"0,00|"  # VL_TOT_CRED_DESC
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_TOT_CONT_NC_DEV
            f"0,00|"  # VL_RET_NC
            f"0,00|"  # VL_OUT_DED_NC
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_CONT_NC_REC
            f"0,00|"  # VL_TOT_CONT_CUM_PER
            f"0,00|"  # VL_RET_CUM
            f"0,00|"  # VL_OUT_DED_CUM
            f"0,00|"  # VL_CONT_CUM_REC
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_TOT_CONT_REC
        )
        registros.append(registro_m600)
        
        # M610 - Detalhamento
        registro_m610 = (
            f"|M610|"
            f"01|"  # COD_CONT
            f"{formatar_valor(base_calculo)}|"  # VL_REC_BRT
            f"{formatar_valor(base_calculo)}|"  # VL_BC_CONT
            f"{formatar_valor(aliq_cofins)}|"  # ALIQ_COFINS
            f"0,00|"  # QUANT_BC_COFINS
            f"0,00|"  # ALIQ_COFINS_QUANT
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_CONT_APUR
            f"|"  # VL_AJUS_ACRES
            f"|"  # VL_AJUS_REDUC
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_CONT_DIFER
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_CONT_DIFER_ANT
            f"{formatar_valor(valor_contribuicao_cofins)}|"  # VL_CONT_PER
        )
        registros.append(registro_m610)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_M990(qtd_linhas):
    """M990: ENCERRAMENTO DO BLOCO M"""
    return f"|M990|{qtd_linhas}|"


# ==================== BLOCO 9 - ENCERRAMENTO ====================

def gerar_registro_9001():
    """9001: ABERTURA DO BLOCO 9"""
    return "|9001|0|"


def gerar_registros_9900(contagem_registros):
    """9900: REGISTROS DO ARQUIVO"""
    registros = []
    
    for reg_tipo, qtd in sorted(contagem_registros.items()):
        registros.append(f"|9900|{reg_tipo}|{qtd}|")
    
    return registros


def gerar_registro_9990(qtd_linhas):
    """9990: ENCERRAMENTO DO BLOCO 9"""
    return f"|9990|{qtd_linhas}|"


def gerar_registro_9999(qtd_total):
    """9999: ENCERRAMENTO DO ARQUIVO"""
    return f"|9999|{qtd_total}|"


# ==================== FUNÇÃO PRINCIPAL ====================

def gerar_arquivo_efd_contribuicoes(empresa_id, mes, ano):
    """
    Gera arquivo EFD-Contribuições completo para um mês específico
    
    Args:
        empresa_id: ID da empresa
        mes: Mês (1-12)
        ano: Ano (YYYY)
    
    Returns:
        dict: {
            'success': bool,
            'conteudo': str (conteúdo do arquivo),
            'total_linhas': int,
            'hash': str,
            'data_geracao': str,
            'periodo': str,
            'totais': {
                'receitas': Decimal,
                'pis': Decimal,
                'cofins': Decimal
            }
        }
    """
    try:
        # Calcular datas do mês
        primeiro_dia = f"{ano}-{mes:02d}-01"
        ultimo_dia_num = calendar.monthrange(ano, mes)[1]
        ultimo_dia = f"{ano}-{mes:02d}-{ultimo_dia_num:02d}"
        
        linhas = []
        contagem_registros = {}
        
        def adicionar_registro(registro, tipo_reg=None):
            if registro:
                linhas.append(registro)
                if tipo_reg:
                    contagem_registros[tipo_reg] = contagem_registros.get(tipo_reg, 0) + 1
        
        # ===== BLOCO 0 - ABERTURA =====
        bloco_0_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_0000(empresa_id, primeiro_dia, ultimo_dia), '0000')
        adicionar_registro(gerar_registro_0001(), '0001')
        adicionar_registro(gerar_registro_0110(empresa_id), '0110')
        adicionar_registro(gerar_registro_0140(empresa_id), '0140')
        
        qtd_bloco_0 = len(linhas) - bloco_0_inicio + 1
        adicionar_registro(gerar_registro_0990(qtd_bloco_0), '0990')
        
        # ===== BLOCO C - DOCUMENTOS FISCAIS =====
        bloco_c_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_C001(), 'C001')
        adicionar_registro(gerar_registro_C010(f"{mes:02d}{ano}"), 'C010')
        
        # C100, C170, C181 - Documentos fiscais
        registros_c = gerar_registros_C100_C170_C181(empresa_id, primeiro_dia, ultimo_dia)
        for reg in registros_c:
            tipo = reg[1:5]  # Extrai C100, C170, etc
            adicionar_registro(reg, tipo)
        
        qtd_bloco_c = len(linhas) - bloco_c_inicio + 1
        adicionar_registro(gerar_registro_C990(qtd_bloco_c), 'C990')
        
        # ===== BLOCO M - APURAÇÃO =====
        bloco_m_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_M001(), 'M001')
        
        # PIS
        registros_m100 = gerar_registro_M100_M110(empresa_id, primeiro_dia, ultimo_dia)
        for reg in registros_m100:
            adicionar_registro(reg, 'M100')
        
        registros_m200 = gerar_registro_M200_M210(empresa_id, primeiro_dia, ultimo_dia)
        for reg in registros_m200:
            tipo = reg[1:5]
            adicionar_registro(reg, tipo)
        
        # COFINS
        registros_m500 = gerar_registro_M500_M510(empresa_id, primeiro_dia, ultimo_dia)
        for reg in registros_m500:
            adicionar_registro(reg, 'M500')
        
        registros_m600 = gerar_registro_M600_M610(empresa_id, primeiro_dia, ultimo_dia)
        for reg in registros_m600:
            tipo = reg[1:5]
            adicionar_registro(reg, tipo)
        
        qtd_bloco_m = len(linhas) - bloco_m_inicio + 1
        adicionar_registro(gerar_registro_M990(qtd_bloco_m), 'M990')
        
        # ===== BLOCO 9 - ENCERRAMENTO =====
        bloco_9_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_9001(), '9001')
        
        registros_9900 = gerar_registros_9900(contagem_registros)
        for reg in registros_9900:
            adicionar_registro(reg, '9900')
        
        qtd_bloco_9 = len(linhas) - bloco_9_inicio + 2
        adicionar_registro(gerar_registro_9990(qtd_bloco_9), '9990')
        
        qtd_total = len(linhas) + 1
        adicionar_registro(gerar_registro_9999(qtd_total), '9999')
        
        # Montar conteúdo final
        conteudo = '\n'.join(linhas)
        hash_arquivo = gerar_hash_arquivo(conteudo)
        
        # Calcular totais para retorno
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0)
                FROM lancamentos_contabeis lc
                JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
                JOIN plano_contas pc ON pc.id = lci.plano_contas_id
                WHERE lc.empresa_id = %s
                    AND lc.data >= %s
                    AND lc.data <= %s
                    AND lc.is_estornado = false
                    AND pc.classificacao = 'receita'
            """, (empresa_id, primeiro_dia, ultimo_dia))
            
            result = cursor.fetchone()
            total_receitas = Decimal(str(result[0])) if result else Decimal('0')
        finally:
            cursor.close()
            conn.close()
        
        valor_pis = total_receitas * aliquotas['pis'] / 100
        valor_cofins = total_receitas * aliquotas['cofins'] / 100
        
        return {
            'success': True,
            'conteudo': conteudo,
            'total_linhas': len(linhas),
            'hash': hash_arquivo,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'periodo': f"{mes:02d}/{ano}",
            'totais': {
                'receitas': float(total_receitas),
                'pis': float(valor_pis),
                'cofins': float(valor_cofins),
                'total_tributos': float(valor_pis + valor_cofins)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def calcular_apuracao_mensal(empresa_id, mes, ano):
    """
    Calcula apuração mensal de PIS/COFINS sem gerar arquivo
    Útil para visualização rápida
    
    Returns:
        dict: {
            'success': bool,
            'periodo': str,
            'regime': str,
            'receitas': {
                'total': Decimal,
                'tributavel': Decimal,
                'nao_tributavel': Decimal
            },
            'pis': {
                'aliquota': Decimal,
                'base_calculo': Decimal,
                'valor': Decimal
            },
            'cofins': {
                'aliquota': Decimal,
                'base_calculo': Decimal,
                'valor': Decimal
            }
        }
    """
    try:
        # Calcular datas
        primeiro_dia = f"{ano}-{mes:02d}-01"
        ultimo_dia_num = calendar.monthrange(ano, mes)[1]
        ultimo_dia = f"{ano}-{mes:02d}-{ultimo_dia_num:02d}"
        
        regime = obter_regime_tributario(empresa_id)
        aliquotas = obter_aliquotas_pis_cofins(regime)
        
        regime_nome = {
            1: 'Lucro Real (Não Cumulativo)',
            2: 'Lucro Presumido (Cumulativo)',
            3: 'Simples Nacional'
        }
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN lci.tipo = 'credito' THEN lci.valor ELSE 0 END), 0)
                FROM lancamentos_contabeis lc
                JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
                JOIN plano_contas pc ON pc.id = lci.plano_contas_id
                WHERE lc.empresa_id = %s
                    AND lc.data >= %s
                    AND lc.data <= %s
                    AND lc.is_estornado = false
                    AND pc.classificacao = 'receita'
            """, (empresa_id, primeiro_dia, ultimo_dia))
            
            result = cursor.fetchone()
            total_receitas = Decimal(str(result[0])) if result else Decimal('0')
        finally:
            cursor.close()
            conn.close()
        
        base_calculo = total_receitas
        valor_pis = base_calculo * aliquotas['pis'] / 100
        valor_cofins = base_calculo * aliquotas['cofins'] / 100
        
        return {
            'success': True,
            'periodo': f"{mes:02d}/{ano}",
            'regime': regime_nome.get(regime, 'Não definido'),
            'receitas': {
                'total': float(total_receitas),
                'tributavel': float(base_calculo),
                'nao_tributavel': 0.0
            },
            'pis': {
                'aliquota': float(aliquotas['pis']),
                'base_calculo': float(base_calculo),
                'valor': float(valor_pis)
            },
            'cofins': {
                'aliquota': float(aliquotas['cofins']),
                'base_calculo': float(base_calculo),
                'valor': float(valor_cofins)
            },
            'total_tributos': float(valor_pis + valor_cofins)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

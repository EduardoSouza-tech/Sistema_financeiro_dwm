# -*- coding: utf-8 -*-
"""
SPED ECD - Escrituração Contábil Digital
Geração de arquivo ECD conforme layout SPED
"""

from datetime import datetime
from decimal import Decimal
from database_postgresql import get_connection
import hashlib


def formatar_valor(valor):
    """Formata valor para o padrão ECD (sem separador de milhar, vírgula decimal)"""
    if valor is None:
        return "0,00"
    valor_decimal = Decimal(str(valor))
    valor_formatado = f"{abs(valor_decimal):.2f}".replace('.', ',')
    return valor_formatado


def formatar_data(data):
    """Formata data para o padrão ECD: ddmmaaaa"""
    if isinstance(data, str):
        data = datetime.strptime(data, '%Y-%m-%d')
    return data.strftime('%d%m%Y')


def gerar_hash_arquivo(conteudo):
    """Gera hash MD5 do arquivo para validação"""
    return hashlib.md5(conteudo.encode('utf-8')).hexdigest().upper()


# ==================== BLOCO 0 - ABERTURA ====================

def gerar_registro_0000(empresa_id, data_inicio, data_fim):
    """
    0000: ABERTURA DO ARQUIVO DIGITAL E IDENTIFICAÇÃO DA ENTIDADE
    
    Campos:
    01 - REG: 0000
    02 - LECD: Texto fixo "LECD"
    03 - DT_INI: Data inicial
    04 - DT_FIN: Data final
    05 - NOME: Nome empresarial
    06 - CNPJ: CNPJ
    07 - UF: Sigla UF
    08 - IE: Inscrição estadual
    09 - COD_MUN: Código município (IBGE)
    10 - IM: Inscrição municipal
    11 - IND_SIT_ESP: Indicador situação especial
    12 - IND_SIT_INI_PER: Indicador situação início período
    13 - IND_NAT_PJ: Indicador natureza PJ
    14 - IND_ATIV: Indicador tipo atividade
    15 - IND_GRANDE_PORTE: Grande porte
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT nome, cnpj, estado, inscricao_estadual, cidade, inscricao_municipal
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        empresa = cursor.fetchone()
        if not empresa:
            return None
        
        nome, cnpj, uf, ie, cidade, im = empresa
        
        # Formatar CNPJ (apenas números)
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj or ''))
        
        registro = (
            f"|0000|"
            f"LECD|"
            f"{formatar_data(data_inicio)}|"
            f"{formatar_data(data_fim)}|"
            f"{nome}|"
            f"{cnpj_limpo}|"
            f"{uf or ''}|"
            f"{ie or ''}|"
            f"|"  # COD_MUN (vazio por enquanto)
            f"{im or ''}|"
            f"|"  # IND_SIT_ESP
            f"0|"  # IND_SIT_INI_PER (0=Regular)
            f"00|"  # IND_NAT_PJ (00=Sociedade Empresária)
            f"0|"  # IND_ATIV (0=Industrial/comercial/outros)
            f"0|"  # IND_GRANDE_PORTE (0=Não)
        )
        
        return registro
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_0001():
    """
    0001: ABERTURA DO BLOCO 0
    
    Campos:
    01 - REG: 0001
    02 - IND_DAD: 0=Bloco com dados
    """
    return "|0001|0|"


def gerar_registro_0007(empresa_id):
    """
    0007: OUTRAS INSCRIÇÕES CADASTRAIS DA PESSOA JURÍDICA
    (Opcional - apenas se houver)
    """
    # Por enquanto, retorna vazio (não implementado)
    return None


def gerar_registro_0020(empresa_id, data_inicio, data_fim):
    """
    0020: PARÂMETROS COMPLEMENTARES
    
    Campos:
    01 - REG: 0020
    02 - IND_DEC: Indicador descentralização (0=Não possui)
    03 - CNPJ: CNPJ estabelecimento descentralizado
    04 - UF: UF estabelecimento
    05 - IE: IE estabelecimento
    06 - COD_MUN: Código município
    07 - IM: IM
    08 - NIRE: NIRE
    09 - IND_CONV: Indicador contabilidade em conjunto
    10 - DT_CONV: Data início conv
    11 - DT_FIN_CONV: Data fim conv
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT nire
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        result = cursor.fetchone()
        nire = result[0] if result and result[0] else ""
        
        registro = (
            f"|0020|"
            f"0|"  # IND_DEC (0=Não descentralizado)
            f"|"  # CNPJ
            f"|"  # UF
            f"|"  # IE
            f"|"  # COD_MUN
            f"|"  # IM
            f"{nire}|"
            f"0|"  # IND_CONV (0=Não há)
            f"|"  # DT_CONV
            f"|"  # DT_FIN_CONV
        )
        
        return registro
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_0990(qtd_linhas):
    """
    0990: ENCERRAMENTO DO BLOCO 0
    
    Campos:
    01 - REG: 0990
    02 - QTD_LIN_0: Quantidade de linhas do Bloco 0
    """
    return f"|0990|{qtd_linhas}|"


# ==================== BLOCO I - LANÇAMENTOS CONTÁBEIS ====================

def gerar_registro_I001():
    """I001: ABERTURA DO BLOCO I"""
    return "|I001|0|"


def gerar_registro_I010(empresa_id, data_inicio, data_fim):
    """
    I010: IDENTIFICAÇÃO DA ESCRITURAÇÃO CONTÁBIL
    
    Campos:
    01 - REG: I010
    02 - IND_ESC: Indicador tipo escrituração (G=Livro Diário)
    03 - COD_VER_LC: Código versão leiaute
    04 - NOME: Nome do livro
    05 - DT_INI: Data início
    06 - DT_FIN: Data fim
    """
    registro = (
        f"|I010|"
        f"G|"  # G=Livro Diário
        f"10.0.0|"  # Versão leiaute
        f"Livro Diário|"
        f"{formatar_data(data_inicio)}|"
        f"{formatar_data(data_fim)}|"
    )
    return registro


def gerar_registro_I030(empresa_id, data_inicio):
    """
    I030: TERMO DE ABERTURA
    
    Campos:
    01 - REG: I030
    02 - NUM_ORD: Número de ordem livro
    03 - NAT_LIVR: Natureza livro
    04 - TIPO_ESCR: Tipo escrituração (R=Resumida, A=Auxiliar, Z=Razão auxiliar)
    05 - COD_HASH_SUB: Hash substituído (se for retificação)
    06 - COD_PART: Código participante (empresa)
    07 - COD_SCP: SCP (se houver)
    08 - DT_DOC: Data abertura
    09 - DESCR_LIVR: Descrição do livro
    """
    registro = (
        f"|I030|"
        f"1|"  # Número de ordem
        f"R|"  # Natureza: R=Livro Razão
        f"R|"  # Tipo: R=Resumida
        f"|"  # Hash substituído
        f"|"  # Código participante
        f"|"  # SCP
        f"{formatar_data(data_inicio)}|"
        f"Livro Diário - Escrituração Contábil Digital|"
    )
    return registro


def gerar_registros_I050(empresa_id, versao_plano_id=None):
    """
    I050: PLANO DE CONTAS
    
    Campos:
    01 - REG: I050
    02 - DT_ALT: Data alteração
    03 - COD_NAT: Código natureza conta (01=Contas ativo, 02=Contas passivo, etc)
    04 - IND_CTA: Indicador tipo conta (A=Analítica, S=Sintética)
    05 - NÍVEL: Nível conta
    06 - COD_CTA: Código conta
    07 - COD_CTA_SUP: Código conta superior
    08 - NOME_CTA: Nome conta
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar plano de contas
        query = """
            SELECT 
                pc.codigo,
                pc.descricao,
                pc.nivel,
                pc.tipo,
                pc.classificacao,
                pc.codigo_pai,
                COALESCE(v.data_versao, pc.created_at::date)
            FROM plano_contas pc
            LEFT JOIN plano_contas_versao v ON v.id = pc.versao_id
            WHERE pc.empresa_id = %s
                AND pc.ativo = true
        """
        
        params = [empresa_id]
        
        if versao_plano_id:
            query += " AND pc.versao_id = %s"
            params.append(versao_plano_id)
        
        query += " ORDER BY pc.codigo"
        
        cursor.execute(query, params)
        contas = cursor.fetchall()
        
        for conta in contas:
            codigo, descricao, nivel, tipo, classificacao, codigo_pai, data_alt = conta
            
            # Mapear classificação para código natureza ECD
            cod_nat_map = {
                'ativo': '01',
                'passivo': '02',
                'patrimonio_liquido': '02',
                'receita': '03',
                'despesa': '04',
                'custos': '04'
            }
            cod_nat = cod_nat_map.get(classificacao, '05')
            
            # Indicador tipo conta (A=Analítica, S=Sintética)
            ind_cta = 'A' if tipo == 'analitica' else 'S'
            
            registro = (
                f"|I050|"
                f"{formatar_data(data_alt)}|"
                f"{cod_nat}|"
                f"{ind_cta}|"
                f"{nivel}|"
                f"{codigo}|"
                f"{codigo_pai or ''}|"
                f"{descricao}|"
            )
            registros.append(registro)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registros_I150_I155(empresa_id, data_inicio, data_fim, versao_plano_id=None):
    """
    I150: SALDO DAS CONTAS ANALÍTICAS
    I155: DETALHES DOS SALDOS PERIÓDICOS
    
    I150 - Campos:
    01 - REG: I150
    02 - DT_INI: Data inicial
    03 - DT_FIN: Data final
    
    I155 - Campos:
    01 - REG: I155
    02 - COD_CTA: Código conta
    03 - COD_CCUS: Código centro custo
    04 - VL_SLD_INI: Valor saldo inicial
    05 - IND_DC_INI: Indicador D/C inicial
    06 - VL_DEB: Valor débitos
    07 - VL_CRED: Valor créditos
    08 - VL_SLD_FIN: Valor saldo final
    09 - IND_DC_FIN: Indicador D/C final
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Registro I150 (cabeçalho do período)
        registros.append(
            f"|I150|{formatar_data(data_inicio)}|{formatar_data(data_fim)}|"
        )
        
        # Buscar saldos das contas analíticas
        query = """
            WITH saldos_periodo AS (
                SELECT 
                    pc.codigo,
                    pc.natureza,
                    -- Saldo inicial (antes do período)
                    COALESCE(SUM(
                        CASE 
                            WHEN lci.tipo = 'debito' AND lc.data < %s THEN lci.valor
                            WHEN lci.tipo = 'credito' AND lc.data < %s THEN -lci.valor
                            ELSE 0
                        END
                    ), 0) as saldo_inicial,
                    -- Débitos do período
                    COALESCE(SUM(
                        CASE 
                            WHEN lci.tipo = 'debito' AND lc.data >= %s AND lc.data <= %s 
                            THEN lci.valor 
                            ELSE 0 
                        END
                    ), 0) as debitos_periodo,
                    -- Créditos do período
                    COALESCE(SUM(
                        CASE 
                            WHEN lci.tipo = 'credito' AND lc.data >= %s AND lc.data <= %s 
                            THEN lci.valor 
                            ELSE 0 
                        END
                    ), 0) as creditos_periodo
                FROM plano_contas pc
                LEFT JOIN lancamentos_contabeis_itens lci ON lci.plano_contas_id = pc.id
                LEFT JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id AND lc.is_estornado = false
                WHERE pc.empresa_id = %s
                    AND pc.tipo = 'analitica'
                    AND pc.ativo = true
        """
        
        params = [data_inicio, data_inicio, data_inicio, data_fim, data_inicio, data_fim, empresa_id]
        
        if versao_plano_id:
            query += " AND pc.versao_id = %s"
            params.append(versao_plano_id)
        
        query += """
                GROUP BY pc.id, pc.codigo, pc.natureza
                HAVING 
                    SUM(CASE WHEN lci.tipo = 'debito' AND lc.data < %s THEN lci.valor WHEN lci.tipo = 'credito' AND lc.data < %s THEN -lci.valor ELSE 0 END) != 0
                    OR SUM(CASE WHEN lci.tipo = 'debito' AND lc.data >= %s AND lc.data <= %s THEN lci.valor ELSE 0 END) != 0
                    OR SUM(CASE WHEN lci.tipo = 'credito' AND lc.data >= %s AND lc.data <= %s THEN lci.valor ELSE 0 END) != 0
                ORDER BY pc.codigo
        """
        params.extend([data_inicio, data_inicio, data_inicio, data_fim, data_inicio, data_fim])
        
        cursor.execute(query, params)
        saldos = cursor.fetchall()
        
        for saldo in saldos:
            codigo, natureza, saldo_ini, debitos, creditos = saldo
            
            # Calcular saldo final
            if natureza == 'devedora':
                saldo_fin = saldo_ini + debitos - creditos
            else:
                saldo_fin = saldo_ini - debitos + creditos
            
            # Indicadores D/C
            ind_dc_ini = 'D' if saldo_ini >= 0 else 'C'
            ind_dc_fin = 'D' if saldo_fin >= 0 else 'C'
            
            # Registro I155
            registro = (
                f"|I155|"
                f"{codigo}|"
                f"|"  # COD_CCUS (centro de custo - não implementado)
                f"{formatar_valor(abs(saldo_ini))}|"
                f"{ind_dc_ini}|"
                f"{formatar_valor(debitos)}|"
                f"{formatar_valor(creditos)}|"
                f"{formatar_valor(abs(saldo_fin))}|"
                f"{ind_dc_fin}|"
            )
            registros.append(registro)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registros_I200_I250(empresa_id, data_inicio, data_fim):
    """
    I200: LANÇAMENTO CONTÁBIL
    I250: PARTIDAS DO LANÇAMENTO
    
    I200 - Campos:
    01 - REG: I200
    02 - NUM_LCTO: Número lançamento
    03 - DT_LCTO: Data lançamento
    04 - VL_LCTO: Valor total lançamento
    05 - IND_LCTO: Indicador tipo lançamento (N=Normal)
    06 - DT_LCTO_EXT: Data lançamento extemporâneo
    07 - VL_DC_LCTO: Valor D/C lançamento
    08 - IND_DC_EXT: Indicador D/C lançamento extemporâneo
    09 - HIST: Histórico
    
    I250 - Campos:
    01 - REG: I250
    02 - COD_CTA: Código conta
    03 - COD_CCUS: Código centro custo
    04 - VL_DC: Valor débito/crédito
    05 - IND_DC: Indicador D/C
    06 - NUM_PART: Número participante
    07 - HIST_PART: Histórico partida
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar lançamentos do período
        cursor.execute("""
            SELECT 
                lc.id,
                lc.numero_lancamento,
                lc.data,
                lc.historico,
                lc.valor_total
            FROM lancamentos_contabeis lc
            WHERE lc.empresa_id = %s
                AND lc.data >= %s
                AND lc.data <= %s
                AND lc.is_estornado = false
            ORDER BY lc.data, lc.numero_lancamento
        """, (empresa_id, data_inicio, data_fim))
        
        lancamentos = cursor.fetchall()
        
        for lancamento in lancamentos:
            lanc_id, num_lanc, data_lanc, historico, valor_total = lancamento
            
            # Registro I200 (cabeçalho do lançamento)
            registro_i200 = (
                f"|I200|"
                f"{num_lanc}|"
                f"{formatar_data(data_lanc)}|"
                f"{formatar_valor(valor_total)}|"
                f"N|"  # N=Normal
                f"|"  # DT_LCTO_EXT
                f"|"  # VL_DC_LCTO
                f"|"  # IND_DC_EXT
                f"{historico[:200]}|"  # Histórico limitado a 200 caracteres
            )
            registros.append(registro_i200)
            
            # Buscar itens do lançamento (partidas)
            cursor.execute("""
                SELECT 
                    pc.codigo,
                    lci.tipo,
                    lci.valor,
                    lci.historico
                FROM lancamentos_contabeis_itens lci
                JOIN plano_contas pc ON pc.id = lci.plano_contas_id
                WHERE lci.lancamento_id = %s
                ORDER BY lci.tipo DESC, lci.id
            """, (lanc_id,))
            
            itens = cursor.fetchall()
            
            for item in itens:
                codigo_cta, tipo, valor, hist_part = item
                
                ind_dc = 'D' if tipo == 'debito' else 'C'
                
                # Registro I250 (partida)
                registro_i250 = (
                    f"|I250|"
                    f"{codigo_cta}|"
                    f"|"  # COD_CCUS
                    f"{formatar_valor(valor)}|"
                    f"{ind_dc}|"
                    f"|"  # NUM_PART
                    f"{(hist_part or '')[:200]}|"  # Histórico partida
                )
                registros.append(registro_i250)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_I990(qtd_linhas):
    """I990: ENCERRAMENTO DO BLOCO I"""
    return f"|I990|{qtd_linhas}|"


# ==================== BLOCO J - DEMONSTRAÇÕES CONTÁBEIS ====================

def gerar_registro_J001():
    """J001: ABERTURA DO BLOCO J"""
    return "|J001|0|"


def gerar_registro_J005(empresa_id, data_fim):
    """
    J005: DEMONSTRAÇÕES CONTÁBEIS
    
    Campos:
    01 - REG: J005
    02 - DT_FIN: Data fim
    03 - IND_SIT_ESP: Indicador situação especial
    04 - INV_CP: Investimentos controladas/coligadas
    05 - NIRE: NIRE
    06 - CNPJ_OT: CNPJ outro
    07 - DOC_TC: Documento termo conversão
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT nire FROM empresas WHERE id = %s", (empresa_id,))
        result = cursor.fetchone()
        nire = result[0] if result and result[0] else ""
        
        registro = (
            f"|J005|"
            f"{formatar_data(data_fim)}|"
            f"|"  # IND_SIT_ESP
            f"|"  # INV_CP
            f"{nire}|"
            f"|"  # CNPJ_OT
            f"|"  # DOC_TC
        )
        return registro
        
    finally:
        cursor.close()
        conn.close()


def gerar_registros_J100(empresa_id, data_fim, versao_plano_id=None):
    """
    J100: BALANÇO PATRIMONIAL
    
    Campos:
    01 - REG: J100
    02 - COD_AGL: Código aglutinação
    03 - INDSC_AGL: Nível aglutinação
    04 - NÍVEL: Nível conta
    05 - COD_CTA: Código conta
    06 - COD_CTA_SUP: Código conta superior
    07 - NOME_CTA: Nome conta
    08 - VL_CTA_FIN: Valor conta no fim do período
    09 - IND_DC_CTA: Indicador D/C
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar contas de balanço (ativo, passivo, PL)
        query = """
            SELECT 
                pc.codigo,
                pc.descricao,
                pc.nivel,
                pc.codigo_pai,
                pc.tipo,
                pc.classificacao,
                COALESCE(SUM(
                    CASE 
                        WHEN lci.tipo = 'debito' AND lc.data <= %s 
                        THEN lci.valor
                        WHEN lci.tipo = 'credito' AND lc.data <= %s 
                        THEN -lci.valor
                        ELSE 0
                    END
                ), 0) as saldo
            FROM plano_contas pc
            LEFT JOIN lancamentos_contabeis_itens lci ON lci.plano_contas_id = pc.id
            LEFT JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id AND lc.is_estornado = false
            WHERE pc.empresa_id = %s
                AND pc.ativo = true
                AND pc.classificacao IN ('ativo', 'passivo', 'patrimonio_liquido')
        """
        
        params = [data_fim, data_fim, empresa_id]
        
        if versao_plano_id:
            query += " AND pc.versao_id = %s"
            params.append(versao_plano_id)
        
        query += """
            GROUP BY pc.id, pc.codigo, pc.descricao, pc.nivel, pc.codigo_pai, pc.tipo, pc.classificacao
            HAVING pc.tipo = 'analitica' 
                OR EXISTS (
                    SELECT 1 FROM plano_contas pc2 
                    WHERE pc2.codigo_pai = pc.codigo 
                    AND pc2.empresa_id = pc.empresa_id
                )
            ORDER BY pc.codigo
        """
        
        cursor.execute(query, params)
        contas = cursor.fetchall()
        
        for conta in contas:
            codigo, descricao, nivel, codigo_pai, tipo, classificacao, saldo = conta
            
            # Determinar indicador D/C
            ind_dc = 'D' if saldo >= 0 else 'C'
            
            registro = (
                f"|J100|"
                f"|"  # COD_AGL (código aglutinação - não implementado)
                f"|"  # INDSC_AGL
                f"{nivel}|"
                f"{codigo}|"
                f"{codigo_pai or ''}|"
                f"{descricao}|"
                f"{formatar_valor(abs(saldo))}|"
                f"{ind_dc}|"
            )
            registros.append(registro)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registros_J150(empresa_id, data_inicio, data_fim, versao_plano_id=None):
    """
    J150: DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO
    
    Campos:
    01 - REG: J150
    02 - COD_AGL: Código aglutinação
    03 - INDSC_AGL: Nível aglutinação
    04 - NÍVEL: Nível conta
    05 - COD_CTA: Código conta
    06 - COD_CTA_SUP: Código conta superior
    07 - NOME_CTA: Nome conta
    08 - VL_CTA: Valor conta
    09 - IND_VL: Indicador valor (D/C)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    registros = []
    
    try:
        # Buscar contas de resultado (receita, despesa)
        query = """
            SELECT 
                pc.codigo,
                pc.descricao,
                pc.nivel,
                pc.codigo_pai,
                pc.tipo,
                pc.classificacao,
                COALESCE(SUM(
                    CASE 
                        WHEN lci.tipo = 'debito' THEN -lci.valor
                        WHEN lci.tipo = 'credito' THEN lci.valor
                        ELSE 0
                    END
                ), 0) as valor
            FROM plano_contas pc
            LEFT JOIN lancamentos_contabeis_itens lci ON lci.plano_contas_id = pc.id
            LEFT JOIN lancamentos_contabeis lc ON lc.id = lci.lancamento_id 
                AND lc.is_estornado = false
                AND lc.data >= %s 
                AND lc.data <= %s
            WHERE pc.empresa_id = %s
                AND pc.ativo = true
                AND pc.classificacao IN ('receita', 'despesa', 'custos')
        """
        
        params = [data_inicio, data_fim, empresa_id]
        
        if versao_plano_id:
            query += " AND pc.versao_id = %s"
            params.append(versao_plano_id)
        
        query += """
            GROUP BY pc.id, pc.codigo, pc.descricao, pc.nivel, pc.codigo_pai, pc.tipo, pc.classificacao
            HAVING pc.tipo = 'analitica'
                OR EXISTS (
                    SELECT 1 FROM plano_contas pc2 
                    WHERE pc2.codigo_pai = pc.codigo 
                    AND pc2.empresa_id = pc.empresa_id
                )
            ORDER BY pc.codigo
        """
        
        cursor.execute(query, params)
        contas = cursor.fetchall()
        
        for conta in contas:
            codigo, descricao, nivel, codigo_pai, tipo, classificacao, valor = conta
            
            # DRE: receitas são positivas, despesas são negativas
            ind_vl = 'C' if valor >= 0 else 'D'
            
            registro = (
                f"|J150|"
                f"|"  # COD_AGL
                f"|"  # INDSC_AGL
                f"{nivel}|"
                f"{codigo}|"
                f"{codigo_pai or ''}|"
                f"{descricao}|"
                f"{formatar_valor(abs(valor))}|"
                f"{ind_vl}|"
            )
            registros.append(registro)
        
        return registros
        
    finally:
        cursor.close()
        conn.close()


def gerar_registro_J800(empresa_id, data_fim):
    """
    J800: OUTRAS INFORMAÇÕES
    
    Campos:
    01 - REG: J800
    02 - ARQ_RTF: Arquivo RTF
    03 - IND_FIN_RTF: Indicador fim RTF
    04 - TIPO_DOC: Tipo documento
    05 - HASH: Hash documento
    """
    # Por enquanto, não implementado (opcional)
    return None


def gerar_registro_J900(empresa_id, data_inicio, data_fim):
    """
    J900: TERMO DE ENCERRAMENTO
    
    Campos:
    01 - REG: J900
    02 - NUM_ORD: Número ordem
    03 - NAT_LIVR: Natureza livro
    04 - NOME: Nome livro
    05 - DT_ARQ_CONV: Data arquivo conversão
    06 - DT_ARQ: Data arquivo  
    07 - DESCR: Descrição
    """
    registro = (
        f"|J900|"
        f"1|"  # Número ordem
        f"1|"  # Natureza: 1=Livro Diário
        f"Livro Diário|"
        f"|"  # DT_ARQ_CONV
        f"{formatar_data(data_fim)}|"
        f"Termo de Encerramento do Livro Diário - ECD|"
    )
    return registro


def gerar_registro_J990(qtd_linhas):
    """J990: ENCERRAMENTO DO BLOCO J"""
    return f"|J990|{qtd_linhas}|"


# ==================== BLOCO 9 - ENCERRAMENTO ====================

def gerar_registro_9001():
    """9001: ABERTURA DO BLOCO 9"""
    return "|9001|0|"


def gerar_registros_9900(contagem_registros):
    """
    9900: REGISTROS DO ARQUIVO
    
    Campos:
    01 - REG: 9900
    02 - REG_BLC: Registro bloco
    03 - QTD_REG_BLC: Quantidade registros do bloco
    """
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

def gerar_arquivo_ecd(empresa_id, data_inicio, data_fim, versao_plano_id=None):
    """
    Gera arquivo ECD completo
    
    Returns:
        dict: {
            'success': bool,
            'conteudo': str (conteúdo do arquivo),
            'total_linhas': int,
            'hash': str,
            'data_geracao': str
        }
    """
    try:
        linhas = []
        contagem_registros = {}
        
        def adicionar_registro(registro, tipo_reg=None):
            if registro:
                linhas.append(registro)
                if tipo_reg:
                    contagem_registros[tipo_reg] = contagem_registros.get(tipo_reg, 0) + 1
        
        # ===== BLOCO 0 - ABERTURA =====
        bloco_0_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_0000(empresa_id, data_inicio, data_fim), '0000')
        adicionar_registro(gerar_registro_0001(), '0001')
        adicionar_registro(gerar_registro_0020(empresa_id, data_inicio, data_fim), '0020')
        
        qtd_bloco_0 = len(linhas) - bloco_0_inicio + 1  # +1 para o 0990
        adicionar_registro(gerar_registro_0990(qtd_bloco_0), '0990')
        
        # ===== BLOCO I - LANÇAMENTOS =====
        bloco_i_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_I001(), 'I001')
        adicionar_registro(gerar_registro_I010(empresa_id, data_inicio, data_fim), 'I010')
        adicionar_registro(gerar_registro_I030(empresa_id, data_inicio), 'I030')
        
        # I050 - Plano de contas
        registros_i050 = gerar_registros_I050(empresa_id, versao_plano_id)
        for reg in registros_i050:
            adicionar_registro(reg, 'I050')
        
        # I150/I155 - Saldos periódicos
        registros_i150 = gerar_registros_I150_I155(empresa_id, data_inicio, data_fim, versao_plano_id)
        for reg in registros_i150:
            tipo = reg[1:5]  # Extrai I150 ou I155
            adicionar_registro(reg, tipo)
        
        # I200/I250 - Lançamentos e partidas
        registros_i200 = gerar_registros_I200_I250(empresa_id, data_inicio, data_fim)
        for reg in registros_i200:
            tipo = reg[1:5]  # Extrai I200 ou I250
            adicionar_registro(reg, tipo)
        
        qtd_bloco_i = len(linhas) - bloco_i_inicio + 1
        adicionar_registro(gerar_registro_I990(qtd_bloco_i), 'I990')
        
        # ===== BLOCO J - DEMONSTRAÇÕES =====
        bloco_j_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_J001(), 'J001')
        adicionar_registro(gerar_registro_J005(empresa_id, data_fim), 'J005')
        
        # J100 - Balanço Patrimonial
        registros_j100 = gerar_registros_J100(empresa_id, data_fim, versao_plano_id)
        for reg in registros_j100:
            adicionar_registro(reg, 'J100')
        
        # J150 - DRE
        registros_j150 = gerar_registros_J150(empresa_id, data_inicio, data_fim, versao_plano_id)
        for reg in registros_j150:
            adicionar_registro(reg, 'J150')
        
        adicionar_registro(gerar_registro_J900(empresa_id, data_inicio, data_fim), 'J900')
        
        qtd_bloco_j = len(linhas) - bloco_j_inicio + 1
        adicionar_registro(gerar_registro_J990(qtd_bloco_j), 'J990')
        
        # ===== BLOCO 9 - ENCERRAMENTO =====
        bloco_9_inicio = len(linhas)
        
        adicionar_registro(gerar_registro_9001(), '9001')
        
        # 9900 - Contagem de registros
        registros_9900 = gerar_registros_9900(contagem_registros)
        for reg in registros_9900:
            adicionar_registro(reg, '9900')
        
        qtd_bloco_9 = len(linhas) - bloco_9_inicio + 2  # +2 para 9990 e 9999
        adicionar_registro(gerar_registro_9990(qtd_bloco_9), '9990')
        
        qtd_total = len(linhas) + 1  # +1 para o 9999
        adicionar_registro(gerar_registro_9999(qtd_total), '9999')
        
        # Montar conteúdo final
        conteudo = '\n'.join(linhas)
        hash_arquivo = gerar_hash_arquivo(conteudo)
        
        return {
            'success': True,
            'conteudo': conteudo,
            'total_linhas': len(linhas),
            'hash': hash_arquivo,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'periodo': f"{formatar_data(data_inicio)} a {formatar_data(data_fim)}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

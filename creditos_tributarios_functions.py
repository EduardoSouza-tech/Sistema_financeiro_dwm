# -*- coding: utf-8 -*-
"""
Funções de Cálculo de Créditos Tributários
Para regime de Lucro Real (não cumulativo)

Permite calcular créditos de PIS/COFINS sobre:
- Aquisição de insumos
- Energia elétrica
- Aluguéis
- Fretes
- Armazenagem
- Serviços de pessoa jurídica
- Depreciação de ativos imobilizados
"""

from decimal import Decimal
from datetime import datetime, date
from database_postgresql import get_connection, executar_query
from logger_config import logger


# ===== ALÍQUOTAS DO REGIME NÃO CUMULATIVO (LUCRO REAL) =====
ALIQUOTA_PIS_NAO_CUMULATIVO = Decimal('1.65')
ALIQUOTA_COFINS_NAO_CUMULATIVO = Decimal('7.6')


# ===== CÁLCULO DE CRÉDITOS SOBRE NOTAS FISCAIS DE ENTRADA =====

def calcular_creditos_insumos(empresa_id, mes, ano):
    """
    Calcula créditos de PIS/COFINS sobre aquisição de insumos
    
    Podem gerar crédito:
    - Matérias-primas
    - Produtos intermediários
    - Materiais de embalagem
    - Bens utilizados na fabricação ou prestação de serviços
    
    CFOPs de entrada que geram crédito:
    - 1.101, 1.102 (Compras para produção/comercialização)
    - 1.401, 1.403 (Compras para industrialização)
    - 2.101, 2.102, 2.401, 2.403 (Compras interestaduais)
    
    Args:
        empresa_id: ID da empresa
        mes: Mês de referência (1-12)
        ano: Ano de referência
        
    Returns:
        dict: Créditos calculados de PIS e COFINS
    """
    try:
        # Período do mês
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1)
        else:
            data_fim = date(ano, mes + 1, 1)
        
        # Buscar notas de entrada com CST que gera crédito
        # CST 50, 51, 52, 53, 54, 55, 56, 60, 61, 62, 63, 64, 65, 66, 67 = geram crédito
        notas_insumos = executar_query("""
            SELECT 
                nf.id,
                nf.numero,
                nf.serie,
                nf.chave_acesso,
                nf.data_emissao,
                nf.cfop,
                nf.participante_nome,
                nfi.id as item_id,
                nfi.numero_item,
                nfi.descricao,
                nfi.cfop as cfop_item,
                nfi.cst_pis,
                nfi.cst_cofins,
                nfi.base_calculo_pis,
                nfi.base_calculo_cofins,
                nfi.aliquota_pis,
                nfi.aliquota_cofins,
                nfi.valor_pis,
                nfi.valor_cofins
            FROM notas_fiscais nf
            INNER JOIN notas_fiscais_itens nfi ON nfi.nota_fiscal_id = nf.id
            WHERE nf.empresa_id = %s
            AND nf.direcao = 'ENTRADA'
            AND nf.data_emissao >= %s
            AND nf.data_emissao < %s
            AND nf.situacao = 'NORMAL'
            AND nfi.cst_pis IN ('50', '51', '52', '53', '54', '55', '56', '60', '61', '62', '63', '64', '65', '66', '67')
            AND nfi.cfop IN ('1101', '1102', '1401', '1403', '2101', '2102', '2401', '2403')
            ORDER BY nf.data_emissao, nf.numero, nfi.numero_item
        """, (empresa_id, data_inicio, data_fim))
        
        total_credito_pis = Decimal(0)
        total_credito_cofins = Decimal(0)
        creditos_gerados = []
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            for nota in notas_insumos:
                # Usar PIS/COFINS informados na nota, ou calcular
                if nota['valor_pis'] and nota['valor_pis'] > 0:
                    credito_pis = Decimal(str(nota['valor_pis']))
                else:
                    # Calcular com alíquota padrão não cumulativa
                    base = Decimal(str(nota['base_calculo_pis'])) if nota['base_calculo_pis'] else Decimal(0)
                    credito_pis = (base * ALIQUOTA_PIS_NAO_CUMULATIVO) / 100
                
                if nota['valor_cofins'] and nota['valor_cofins'] > 0:
                    credito_cofins = Decimal(str(nota['valor_cofins']))
                else:
                    base = Decimal(str(nota['base_calculo_cofins'])) if nota['base_calculo_cofins'] else Decimal(0)
                    credito_cofins = (base * ALIQUOTA_COFINS_NAO_CUMULATIVO) / 100
                
                # Registrar crédito PIS
                if credito_pis > 0:
                    cursor.execute("""
                        INSERT INTO creditos_tributarios (
                            empresa_id, mes, ano, tipo_credito, tributo,
                            nota_fiscal_id, documento_numero, documento_data,
                            base_calculo, aliquota, valor_credito,
                            descricao, aprovado, data_aprovacao
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (empresa_id, mes, ano, tipo_credito, tributo, nota_fiscal_id) DO UPDATE
                        SET valor_credito = EXCLUDED.valor_credito,
                            base_calculo = EXCLUDED.base_calculo,
                            aliquota = EXCLUDED.aliquota,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (
                        empresa_id, mes, ano, 'INSUMOS', 'PIS',
                        nota['id'], f"{nota['numero']}/{nota['serie']}", nota['data_emissao'],
                        nota['base_calculo_pis'], ALIQUOTA_PIS_NAO_CUMULATIVO, credito_pis,
                        f"Insumo: {nota['descricao'][:100]}", True, date.today()
                    ))
                    
                    credito_id = cursor.fetchone()[0]
                    total_credito_pis += credito_pis
                    
                    creditos_gerados.append({
                        'credito_id': credito_id,
                        'tributo': 'PIS',
                        'nota': f"{nota['numero']}/{nota['serie']}",
                        'fornecedor': nota['participante_nome'],
                        'valor': float(credito_pis)
                    })
                
                # Registrar crédito COFINS
                if credito_cofins > 0:
                    cursor.execute("""
                        INSERT INTO creditos_tributarios (
                            empresa_id, mes, ano, tipo_credito, tributo,
                            nota_fiscal_id, documento_numero, documento_data,
                            base_calculo, aliquota, valor_credito,
                            descricao, aprovado, data_aprovacao
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (empresa_id, mes, ano, tipo_credito, tributo, nota_fiscal_id) DO UPDATE
                        SET valor_credito = EXCLUDED.valor_credito,
                            base_calculo = EXCLUDED.base_calculo,
                            aliquota = EXCLUDED.aliquota,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (
                        empresa_id, mes, ano, 'INSUMOS', 'COFINS',
                        nota['id'], f"{nota['numero']}/{nota['serie']}", nota['data_emissao'],
                        nota['base_calculo_cofins'], ALIQUOTA_COFINS_NAO_CUMULATIVO, credito_cofins,
                        f"Insumo: {nota['descricao'][:100]}", True, date.today()
                    ))
                    
                    credito_id = cursor.fetchone()[0]
                    total_credito_cofins += credito_cofins
                    
                    creditos_gerados.append({
                        'credito_id': credito_id,
                        'tributo': 'COFINS',
                        'nota': f"{nota['numero']}/{nota['serie']}",
                        'fornecedor': nota['participante_nome'],
                        'valor': float(credito_cofins)
                    })
            
            conn.commit()
            
            return {
                'success': True,
                'tipo': 'INSUMOS',
                'credito_pis': float(total_credito_pis),
                'credito_cofins': float(total_credito_cofins),
                'total_creditos': float(total_credito_pis + total_credito_cofins),
                'quantidade': len(creditos_gerados),
                'creditos': creditos_gerados
            }
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"Erro ao calcular créditos de insumos: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def calcular_creditos_energia(empresa_id, mes, ano):
    """
    Calcula créditos de PIS/COFINS sobre energia elétrica
    
    Condições:
    - Energia consumida nos estabelecimentos da pessoa jurídica
    - CFOPs 1.253 (dentro do estado) ou 2.253 (fora do estado)
    
    Args:
        empresa_id: ID da empresa
        mes: Mês de referência
        ano: Ano de referência
        
    Returns:
        dict: Créditos calculados
    """
    try:
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1)
        else:
            data_fim = date(ano, mes + 1, 1)
        
        # Buscar notas de energia elétrica
        notas_energia = executar_query("""
            SELECT 
                nf.id,
                nf.numero,
                nf.data_emissao,
                nf.participante_nome,
                nf.valor_produtos,
                nf.valor_pis,
                nf.valor_cofins
            FROM notas_fiscais nf
            WHERE nf.empresa_id = %s
            AND nf.direcao = 'ENTRADA'
            AND nf.data_emissao >= %s
            AND nf.data_emissao < %s
            AND nf.situacao = 'NORMAL'
            AND nf.cfop IN ('1253', '2253')
            ORDER BY nf.data_emissao, nf.numero
        """, (empresa_id, data_inicio, data_fim))
        
        total_credito_pis = Decimal(0)
        total_credito_cofins = Decimal(0)
        creditos_gerados = []
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            for nota in notas_energia:
                # Calcular créditos
                base_calculo = Decimal(str(nota['valor_produtos']))
                credito_pis = (base_calculo * ALIQUOTA_PIS_NAO_CUMULATIVO) / 100
                credito_cofins = (base_calculo * ALIQUOTA_COFINS_NAO_CUMULATIVO) / 100
                
                # Registrar PIS
                cursor.execute("""
                    INSERT INTO creditos_tributarios (
                        empresa_id, mes, ano, tipo_credito, tributo,
                        nota_fiscal_id, documento_numero, documento_data,
                        base_calculo, aliquota, valor_credito,
                        descricao, aprovado, data_aprovacao
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (empresa_id, mes, ano, tipo_credito, tributo, nota_fiscal_id) DO UPDATE
                    SET valor_credito = EXCLUDED.valor_credito
                    RETURNING id
                """, (
                    empresa_id, mes, ano, 'ENERGIA', 'PIS',
                    nota['id'], nota['numero'], nota['data_emissao'],
                    base_calculo, ALIQUOTA_PIS_NAO_CUMULATIVO, credito_pis,
                    f"Energia elétrica - {nota['participante_nome']}", True, date.today()
                ))
                
                total_credito_pis += credito_pis
                
                # Registrar COFINS
                cursor.execute("""
                    INSERT INTO creditos_tributarios (
                        empresa_id, mes, ano, tipo_credito, tributo,
                        nota_fiscal_id, documento_numero, documento_data,
                        base_calculo, aliquota, valor_credito,
                        descricao, aprovado, data_aprovacao
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (empresa_id, mes, ano, tipo_credito, tributo, nota_fiscal_id) DO UPDATE
                    SET valor_credito = EXCLUDED.valor_credito
                    RETURNING id
                """, (
                    empresa_id, mes, ano, 'ENERGIA', 'COFINS',
                    nota['id'], nota['numero'], nota['data_emissao'],
                    base_calculo, ALIQUOTA_COFINS_NAO_CUMULATIVO, credito_cofins,
                    f"Energia elétrica - {nota['participante_nome']}", True, date.today()
                ))
                
                total_credito_cofins += credito_cofins
                
                creditos_gerados.append({
                    'nota': nota['numero'],
                    'fornecedor': nota['participante_nome'],
                    'valor_pis': float(credito_pis),
                    'valor_cofins': float(credito_cofins)
                })
            
            conn.commit()
            
            return {
                'success': True,
                'tipo': 'ENERGIA',
                'credito_pis': float(total_credito_pis),
                'credito_cofins': float(total_credito_cofins),
                'total_creditos': float(total_credito_pis + total_credito_cofins),
                'quantidade': len(creditos_gerados),
                'creditos': creditos_gerados
            }
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"Erro ao calcular créditos de energia: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def calcular_creditos_aluguel(empresa_id, mes, ano):
    """
    Calcula créditos de PIS/COFINS sobre aluguéis de prédios, máquinas e equipamentos
    
    Condições:
    - Aluguéis de pessoa jurídica
    - Utilizados nas atividades da empresa
    - NFS-e ou recibos com retenção de PIS/COFINS
    
    Args:
        empresa_id: ID da empresa
        mes: Mês de referência
        ano: Ano de referência
        
    Returns:
        dict: Créditos calculados
    """
    try:
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1)
        else:
            data_fim = date(ano, mes + 1, 1)
        
        # Buscar lançamentos contábeis de aluguel
        # (Contas: 3.01.02 - Aluguéis)
        lancamentos_aluguel = executar_query("""
            SELECT 
                lc.id,
                lc.data_lancamento,
                lc.historico,
                lci.valor
            FROM lancamentos_contabeis lc
            INNER JOIN lancamentos_contabeis_itens lci ON lci.lancamento_id = lc.id
            INNER JOIN plano_contas pc ON pc.id = lci.conta_id
            WHERE lc.empresa_id = %s
            AND lc.data_lancamento >= %s
            AND lc.data_lancamento < %s
            AND lci.tipo = 'D'
            AND pc.codigo LIKE '3.01.02%'
            ORDER BY lc.data_lancamento
        """, (empresa_id, data_inicio, data_fim))
        
        total_credito_pis = Decimal(0)
        total_credito_cofins = Decimal(0)
        creditos_gerados = []
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            for lanc in lancamentos_aluguel:
                # Verificar se já existe crédito para este lançamento
                credito_existente = executar_query("""
                    SELECT id FROM creditos_tributarios
                    WHERE empresa_id = %s
                    AND mes = %s
                    AND ano = %s
                    AND tipo_credito = 'ALUGUEL'
                    AND descricao LIKE %s
                """, (empresa_id, mes, ano, f"%ID:{lanc['id']}%"))
                
                if credito_existente:
                    continue
                
                # Calcular créditos
                base_calculo = Decimal(str(lanc['valor']))
                credito_pis = (base_calculo * ALIQUOTA_PIS_NAO_CUMULATIVO) / 100
                credito_cofins = (base_calculo * ALIQUOTA_COFINS_NAO_CUMULATIVO) / 100
                
                # Registrar PIS
                cursor.execute("""
                    INSERT INTO creditos_tributarios (
                        empresa_id, mes, ano, tipo_credito, tributo,
                        documento_data, base_calculo, aliquota, valor_credito,
                        descricao, aprovado, data_aprovacao
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    empresa_id, mes, ano, 'ALUGUEL', 'PIS',
                    lanc['data_lancamento'], base_calculo, ALIQUOTA_PIS_NAO_CUMULATIVO, credito_pis,
                    f"Aluguel - {lanc['historico'][:100]} (ID:{lanc['id']})", True, date.today()
                ))
                
                total_credito_pis += credito_pis
                
                # Registrar COFINS
                cursor.execute("""
                    INSERT INTO creditos_tributarios (
                        empresa_id, mes, ano, tipo_credito, tributo,
                        documento_data, base_calculo, aliquota, valor_credito,
                        descricao, aprovado, data_aprovacao
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    empresa_id, mes, ano, 'ALUGUEL', 'COFINS',
                    lanc['data_lancamento'], base_calculo, ALIQUOTA_COFINS_NAO_CUMULATIVO, credito_cofins,
                    f"Aluguel - {lanc['historico'][:100]} (ID:{lanc['id']})", True, date.today()
                ))
                
                total_credito_cofins += credito_cofins
                
                creditos_gerados.append({
                    'historico': lanc['historico'],
                    'data': str(lanc['data_lancamento']),
                    'valor_pis': float(credito_pis),
                    'valor_cofins': float(credito_cofins)
                })
            
            conn.commit()
            
            return {
                'success': True,
                'tipo': 'ALUGUEL',
                'credito_pis': float(total_credito_pis),
                'credito_cofins': float(total_credito_cofins),
                'total_creditos': float(total_credito_pis + total_credito_cofins),
                'quantidade': len(creditos_gerados),
                'creditos': creditos_gerados
            }
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"Erro ao calcular créditos de aluguel: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def calcular_todos_creditos(empresa_id, mes, ano):
    """
    Calcula todos os tipos de créditos tributários do período
    
    Args:
        empresa_id: ID da empresa
        mes: Mês de referência
        ano: Ano de referência
        
    Returns:
        dict: Resumo de todos os créditos
    """
    try:
        resultados = {
            'insumos': calcular_creditos_insumos(empresa_id, mes, ano),
            'energia': calcular_creditos_energia(empresa_id, mes, ano),
            'aluguel': calcular_creditos_aluguel(empresa_id, mes, ano)
        }
        
        # Totalizar
        total_pis = sum([
            Decimal(str(r.get('credito_pis', 0))) 
            for r in resultados.values() 
            if r.get('success')
        ])
        
        total_cofins = sum([
            Decimal(str(r.get('credito_cofins', 0))) 
            for r in resultados.values() 
            if r.get('success')
        ])
        
        total_geral = total_pis + total_cofins
        
        return {
            'success': True,
            'mes': mes,
            'ano': ano,
            'detalhamento': resultados,
            'resumo': {
                'total_credito_pis': float(total_pis),
                'total_credito_cofins': float(total_cofins),
                'total_geral': float(total_geral)
            }
        }
    
    except Exception as e:
        logger.error(f"Erro ao calcular todos os créditos: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def listar_creditos_periodo(empresa_id, mes, ano, tributo=None):
    """
    Lista créditos tributários do período
    
    Args:
        empresa_id: ID da empresa
        mes: Mês
        ano: Ano
        tributo: Filtrar por PIS ou COFINS (opcional)
        
    Returns:
        list: Lista de créditos
    """
    filtros = ["empresa_id = %s", "mes = %s", "ano = %s"]
    parametros = [empresa_id, mes, ano]
    
    if tributo:
        filtros.append("tributo = %s")
        parametros.append(tributo)
    
    where_clause = " AND ".join(filtros)
    
    creditos = executar_query(
        f"""
        SELECT 
            id, tipo_credito, tributo,
            documento_numero, documento_data,
            base_calculo, aliquota, valor_credito,
            descricao, aprovado, utilizado
        FROM creditos_tributarios
        WHERE {where_clause}
        ORDER BY documento_data, tipo_credito, tributo
        """,
        parametros
    )
    
    return creditos


def obter_resumo_creditos(empresa_id, mes, ano):
    """
    Obtém resumo dos créditos tributários
    
    Returns:
        dict: Resumo por tipo e tributo
    """
    resumo = executar_query("""
        SELECT 
            tipo_credito,
            tributo,
            COUNT(*) as quantidade,
            SUM(valor_credito) as total_credito
        FROM creditos_tributarios
        WHERE empresa_id = %s
        AND mes = %s
        AND ano = %s
        AND aprovado = TRUE
        GROUP BY tipo_credito, tributo
        ORDER BY tipo_credito, tributo
    """, (empresa_id, mes, ano))
    
    # Organizar por tipo
    resultado = {}
    total_pis = Decimal(0)
    total_cofins = Decimal(0)
    
    for item in resumo:
        tipo = item['tipo_credito']
        if tipo not in resultado:
            resultado[tipo] = {
                'PIS': 0,
                'COFINS': 0,
                'TOTAL': 0
            }
        
        valor = Decimal(str(item['total_credito']))
        resultado[tipo][item['tributo']] = float(valor)
        resultado[tipo]['TOTAL'] = float(
            Decimal(str(resultado[tipo]['PIS'])) + 
            Decimal(str(resultado[tipo]['COFINS']))
        )
        
        if item['tributo'] == 'PIS':
            total_pis += valor
        else:
            total_cofins += valor
    
    return {
        'detalhamento': resultado,
        'totais': {
            'PIS': float(total_pis),
            'COFINS': float(total_cofins),
            'TOTAL': float(total_pis + total_cofins)
        }
    }

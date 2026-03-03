"""
📊 Blueprint de Relatórios
===========================

Gerencia endpoints de relatórios e análises financeiras.
Extraído de web_server.py na Fase 5 da otimização.

Inclui refatoração Fase 4: Uso de utils (parse_date, format_date_br, get_current_date_filename)

Relatórios disponíveis:
- Fluxo de caixa (realizado e projetado)
- Dashboard completo
- Análise de contas (a pagar/receber)
- Resumo por parceiros
- Análise por categorias
- Comparativo entre períodos
- Indicadores financeiros
- Inadimplência

Autor: Sistema de Otimização - Fase 5
Data: 20/01/2026
"""

from flask import Blueprint, request, jsonify
from auth_middleware import require_permission
from datetime import date, datetime, timedelta
from decimal import Decimal
from database_postgresql import StatusLancamento, TipoLancamento
import database_postgresql as db
from app.utils import parse_date, format_date_br, get_current_date_br, get_current_date_filename
from app.utils.cache_manager import cached, invalidate_cache

# Criar blueprint
relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/api/relatorios')


@relatorios_bp.route('/fluxo-caixa', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_fluxo_caixa():
    """
    Relatório de fluxo de caixa — lançamentos PAGOS no período.

    Filtra diretamente por data_pagamento no SQL para garantir precisão.

    Security:
        🔒 Validado empresa_id da sessão
    """
    from flask import session
    from database_postgresql import get_db_connection

    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403

    today = date.today()
    data_inicio_str = request.args.get('data_inicio', (today - timedelta(days=30)).isoformat())
    data_fim_str    = request.args.get('data_fim',    today.isoformat())

    # Parse robusto das datas (aceita formato YYYY-MM-DD)
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        data_inicio = today - timedelta(days=30)

    try:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        data_fim = today

    try:
        import psycopg2.extras
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT
                    id, tipo, descricao, valor,
                    data_pagamento,
                    categoria, subcategoria, conta_bancaria,
                    pessoa, associacao
                FROM lancamentos
                WHERE empresa_id = %s
                  AND LOWER(status) = 'pago'
                  AND data_pagamento IS NOT NULL
                  AND data_pagamento::date >= %s
                  AND data_pagamento::date <= %s
                ORDER BY data_pagamento, id
            """, (empresa_id, data_inicio, data_fim))
            rows = cursor.fetchall()
    except Exception as e:
        print(f"[fluxo-caixa] Erro SQL: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'erro': f'Erro ao consultar lançamentos: {e}'}), 500

    resultado = []
    for row in rows:
        # row é dict (RealDictCursor)
        tipo_raw = (row['tipo'] or '').lower()
        data_pgto_raw = row['data_pagamento']
        data_pgto_str = (
            data_pgto_raw.date().isoformat() if isinstance(data_pgto_raw, datetime)
            else data_pgto_raw.isoformat() if hasattr(data_pgto_raw, 'isoformat')
            else str(data_pgto_raw)
        )
        valor = float(row['valor'] or 0)

        if tipo_raw == 'transferencia':
            # Transferência: aparece como saída na conta origem
            resultado.append({
                'tipo': 'despesa',
                'descricao': f"{row['descricao']} (Saída)",
                'valor': valor,
                'data_pagamento': data_pgto_str,
                'categoria': row['categoria'] or '',
                'subcategoria': row['subcategoria'] or '',
                'pessoa': row['pessoa'] or '',
                'conta_bancaria': row['conta_bancaria'] or '',
                'associacao': row['associacao'] or '',
                'id': row['id'],
            })
            # e como entrada na conta destino (subcategoria = destino)
            resultado.append({
                'tipo': 'receita',
                'descricao': f"{row['descricao']} (Entrada)",
                'valor': valor,
                'data_pagamento': data_pgto_str,
                'categoria': row['categoria'] or '',
                'subcategoria': row['conta_bancaria'] or '',
                'pessoa': row['pessoa'] or '',
                'conta_bancaria': row['subcategoria'] or '',
                'associacao': row['associacao'] or '',
                'id': row['id'],
            })
        else:
            resultado.append({
                'tipo': tipo_raw if tipo_raw in ('receita', 'despesa') else tipo_raw,
                'descricao': row['descricao'] or '',
                'valor': valor,
                'data_pagamento': data_pgto_str,
                'categoria': row['categoria'] or '',
                'subcategoria': row['subcategoria'] or '',
                'pessoa': row['pessoa'] or '',
                'conta_bancaria': row['conta_bancaria'] or '',
                'associacao': row['associacao'] or '',
                'id': row['id'],
            })

    return jsonify(resultado)


@relatorios_bp.route('/dashboard', methods=['GET'])
@require_permission('relatorios_view')
def dashboard():
    """
    Dados para o dashboard
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
        from flask import session
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        # Pegar filtros opcionais
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        
        # 🔒 Passar empresa_id explicitamente
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
        # Filtrar lançamentos por cliente se necessário
        usuario = request.usuario
        if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
            lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
        
        # Calcular saldos
        saldo_total = Decimal('0')
        for c in contas:
            saldo_total += Decimal(str(c.saldo_inicial))
        
        for lanc in lancamentos:
            if lanc.status == StatusLancamento.PAGO and lanc.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(lanc.valor))
                if lanc.tipo == TipoLancamento.RECEITA:
                    saldo_total += valor_decimal
                else:
                    saldo_total -= valor_decimal
        
        # Contas pendentes
        hoje = date.today()
        contas_receber = Decimal('0')
        contas_pagar = Decimal('0')
        contas_vencidas = Decimal('0')
        
        for l in lancamentos:
            if l.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(l.valor))
                if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE:
                    contas_receber += valor_decimal
                if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE:
                    contas_pagar += valor_decimal
                # Converter datetime para date se necessário
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                if l.status == StatusLancamento.PENDENTE and data_venc < hoje:
                    contas_vencidas += valor_decimal
        
        # Dados para gráfico - últimos 12 meses ou filtrado por ano/mês
        from calendar import monthrange
        import locale
        
        # Tentar configurar locale para português
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
            except:
                pass
        
        meses_labels = []
        receitas_dados = []
        despesas_dados = []
        
        if ano and mes:
            # Apenas um mês específico
            _, ultimo_dia = monthrange(ano, mes)
            data_inicio = date(ano, mes, 1)
            data_fim = date(ano, mes, ultimo_dia)
            
            lancamentos_periodo = [
                l for l in lancamentos 
                if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA
                and data_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= data_fim
            ]
            
            receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
            despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
            
            meses_labels = [data_inicio.strftime('%b/%Y')]
            receitas_dados = [float(receitas_mes)]
            despesas_dados = [float(despesas_mes)]
        
        elif ano:
            # Todos os meses do ano
            for m in range(1, 13):
                _, ultimo_dia = monthrange(ano, m)
                data_inicio = date(ano, m, 1)
                data_fim = date(ano, m, ultimo_dia)
                
                lancamentos_periodo = [
                    l for l in lancamentos 
                    if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA
                    and data_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= data_fim
                ]
                
                receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
                despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
                
                meses_labels.append(data_inicio.strftime('%b/%Y'))
                receitas_dados.append(float(receitas_mes))
                despesas_dados.append(float(despesas_mes))
        
        else:
            # Últimos 12 meses
            data_ref = hoje
            for i in range(11, -1, -1):
                mes_ref = data_ref.month - i
                ano_ref = data_ref.year
                
                while mes_ref <= 0:
                    mes_ref += 12
                    ano_ref -= 1
                
                _, ultimo_dia = monthrange(ano_ref, mes_ref)
                data_inicio = date(ano_ref, mes_ref, 1)
                data_fim = date(ano_ref, mes_ref, ultimo_dia)
                
                lancamentos_periodo = [
                    l for l in lancamentos 
                    if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA
                    and data_inicio <= (l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento) <= data_fim
                ]
                
                receitas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
                despesas_mes = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
                
                meses_labels.append(data_inicio.strftime('%b/%Y'))
                receitas_dados.append(float(receitas_mes))
                despesas_dados.append(float(despesas_mes))
        
        return jsonify({
            'saldo_total': float(saldo_total),
            'contas_receber': float(contas_receber),
            'contas_pagar': float(contas_pagar),
            'contas_vencidas': float(contas_vencidas),
            'total_contas': len(contas),
            'total_lancamentos': len(lancamentos),
            'meses': meses_labels,
            'receitas': receitas_dados,
            'despesas': despesas_dados
        })
    except Exception as e:
        print(f"Erro no dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/dashboard-completo', methods=['GET'])
@require_permission('relatorios_view')
def dashboard_completo():
    """
    Dashboard completo com análises detalhadas - apenas lançamentos liquidados
    
    ⚡ OTIMIZADO COM CACHE (TTL: 5 minutos)
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
        from flask import session
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio or not data_fim:
            return jsonify({'error': 'Datas obrigatórias'}), 400
        
        data_inicio_obj = parse_date(data_inicio)
        data_fim_obj = parse_date(data_fim)
        
        # ⚡ Otimização: Buscar apenas lançamentos pagos do período
        filtros = {
            'status': 'pago',
            'data_inicio': data_inicio_obj,
            'data_fim': data_fim_obj
        }
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id, filtros=filtros)
        
        # Filtrar lançamentos por cliente se necessário
        usuario = request.usuario
        if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
            lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
        
        # Filtrar apenas lançamentos PAGOS/LIQUIDADOS no período (baseado na data de pagamento)
        # Excluir transferências dos relatórios
        lancamentos_periodo = []
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio_obj <= data_pag <= data_fim_obj:
                    lancamentos_periodo.append(l)
        
        # Calcular totais
        total_receitas = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.RECEITA)
        total_despesas = sum(Decimal(str(l.valor)) for l in lancamentos_periodo if l.tipo == TipoLancamento.DESPESA)
        saldo = total_receitas - total_despesas
        
        # Análise por categorias
        receitas_por_categoria = {}
        despesas_por_categoria = {}
        
        for l in lancamentos_periodo:
            categoria = l.categoria or 'Sem Categoria'
            valor = Decimal(str(l.valor))
            
            if l.tipo == TipoLancamento.RECEITA:
                if categoria not in receitas_por_categoria:
                    receitas_por_categoria[categoria] = Decimal('0')
                receitas_por_categoria[categoria] += valor
            else:
                if categoria not in despesas_por_categoria:
                    despesas_por_categoria[categoria] = Decimal('0')
                despesas_por_categoria[categoria] += valor
        
        # Top 5 categorias
        top_receitas = sorted(receitas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:5]
        top_despesas = sorted(despesas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return jsonify({
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim
            },
            'totais': {
                'receitas': float(total_receitas),
                'despesas': float(total_despesas),
                'saldo': float(saldo)
            },
            'top_receitas': [{'categoria': k, 'valor': float(v)} for k, v in top_receitas],
            'top_despesas': [{'categoria': k, 'valor': float(v)} for k, v in top_despesas],
            'total_lancamentos': len(lancamentos_periodo)
        })
    except Exception as e:
        print(f"Erro no dashboard completo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/fluxo-projetado', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_fluxo_projetado():
    """
    Relatório de fluxo de caixa PROJETADO (incluindo lançamentos pendentes futuros)
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
        from flask import session
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        # Receber filtros - padrão é projetar próximos X dias
        dias = request.args.get('dias')
        dias = int(dias) if dias else 30
        
        hoje = date.today()
        data_inicial = hoje
        data_final = hoje + timedelta(days=dias)
        periodo_texto = f"PROJEÇÃO - PRÓXIMOS {dias} DIAS"
        
        # 🔒 Passar empresa_id explicitamente
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
        # Filtrar lançamentos por cliente se necessário
        usuario = request.usuario
        if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
            lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
        
        # Saldo atual (saldo inicial + todos os lançamentos pagos até hoje)
        saldo_atual = Decimal('0')
        for c in contas:
            saldo_atual += Decimal(str(c.saldo_inicial))
        
        # Adicionar todas as receitas e despesas JÁ PAGAS até hoje (exceto transferências)
        for l in lancamentos:
            # Converter data_pagamento para date se for datetime
            if l.data_pagamento:
                if isinstance(l.data_pagamento, datetime):
                    data_pgto = l.data_pagamento.date()
                else:
                    data_pgto = l.data_pagamento
            else:
                data_pgto = None
            
            if l.status == StatusLancamento.PAGO and data_pgto and data_pgto <= hoje and l.tipo != TipoLancamento.TRANSFERENCIA:
                valor_decimal = Decimal(str(l.valor))
                if l.tipo == TipoLancamento.RECEITA:
                    saldo_atual += valor_decimal
                else:
                    saldo_atual -= valor_decimal
        
        # Buscar lançamentos PENDENTES para projeção (vencidos + futuros)
        lancamentos_futuros = []
        lancamentos_vencidos = []
        receitas_previstas = Decimal('0')
        despesas_previstas = Decimal('0')
        receitas_vencidas = Decimal('0')
        despesas_vencidas = Decimal('0')
        
        for l in lancamentos:
            if l.status == StatusLancamento.PENDENTE and l.tipo != TipoLancamento.TRANSFERENCIA:
                # Converter data_vencimento para date se for datetime
                if isinstance(l.data_vencimento, datetime):
                    data_venc = l.data_vencimento.date()
                else:
                    data_venc = l.data_vencimento
                
                valor_decimal = Decimal(str(l.valor))
                
                # Lançamentos vencidos (já passaram do vencimento)
                if data_venc < hoje:
                    lancamentos_vencidos.append(l)
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_vencidas += valor_decimal
                    else:
                        despesas_vencidas += valor_decimal
                
                # Lançamentos futuros (dentro do período de projeção)
                elif data_inicial <= data_venc <= data_final:
                    lancamentos_futuros.append(l)
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_previstas += valor_decimal
                    else:
                        despesas_previstas += valor_decimal
        
        # Calcular saldo projetado (incluindo vencidos)
        saldo_projetado = saldo_atual + (receitas_previstas + receitas_vencidas) - (despesas_previstas + despesas_vencidas)
        
        # Ordenar por data de vencimento
        lancamentos_vencidos.sort(key=lambda x: x.data_vencimento)
        lancamentos_futuros.sort(key=lambda x: x.data_vencimento)
        
        # Montar fluxo projetado dia a dia (VENCIDOS PRIMEIRO, depois futuros)
        fluxo = []
        saldo_acumulado = saldo_atual
        
        # Adicionar vencidos primeiro
        for lanc in lancamentos_vencidos:
            valor_decimal = Decimal(str(lanc.valor))
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_acumulado += valor_decimal
            else:
                saldo_acumulado -= valor_decimal
            
            # Calcular dias de atraso
            data_venc_date = lanc.data_vencimento.date() if isinstance(lanc.data_vencimento, datetime) else lanc.data_vencimento
            dias_atraso = (hoje - data_venc_date).days
            
            fluxo.append({
                'data_vencimento': lanc.data_vencimento.isoformat(),
                'descricao': lanc.descricao,
                'tipo': lanc.tipo.value,
                'valor': float(lanc.valor),
                'categoria': lanc.categoria,
                'subcategoria': lanc.subcategoria,
                'pessoa': lanc.pessoa,
                'conta_bancaria': lanc.conta_bancaria,
                'saldo_acumulado': float(saldo_acumulado),
                'status': 'VENCIDO',
                'dias_atraso': dias_atraso
            })
        
        # Adicionar lançamentos futuros
        for lanc in lancamentos_futuros:
            valor_decimal = Decimal(str(lanc.valor))
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_acumulado += valor_decimal
            else:
                saldo_acumulado -= valor_decimal
            
            fluxo.append({
                'data_vencimento': lanc.data_vencimento.isoformat(),
                'descricao': lanc.descricao,
                'tipo': lanc.tipo.value,
                'valor': float(lanc.valor),
                'categoria': lanc.categoria,
                'subcategoria': lanc.subcategoria,
                'pessoa': lanc.pessoa,
                'conta_bancaria': lanc.conta_bancaria,
                'saldo_acumulado': float(saldo_acumulado),
                'status': 'PENDENTE',
                'dias_atraso': 0
            })
        
        return jsonify({
            'periodo_texto': periodo_texto,
            'data_inicial': data_inicial.isoformat(),
            'data_final': data_final.isoformat(),
            'saldo_atual': float(saldo_atual),
            'receitas_previstas': float(receitas_previstas),
            'despesas_previstas': float(despesas_previstas),
            'receitas_vencidas': float(receitas_vencidas),
            'despesas_vencidas': float(despesas_vencidas),
            'saldo_projetado': float(saldo_projetado),
            'total_vencidos': len(lancamentos_vencidos),
            'total_futuros': len(lancamentos_futuros),
            'fluxo': fluxo
        })
    except Exception as e:
        print(f"Erro no fluxo projetado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/analise-contas', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_analise_contas():
    """
    Relatório de análise de contas a pagar e receber
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
    hoje = date.today()
    
    # Filtrar lançamentos por cliente se necessário
    usuario = request.usuario
    if usuario['tipo'] != 'admin' and usuario.get('cliente_id'):
        lancamentos = [l for l in lancamentos if getattr(l, 'pessoa', None) == usuario['cliente_id']]
    
    # Função auxiliar para converter datetime para date
    def get_date(data):
        return data.date() if hasattr(data, 'date') else data
    
    # Totais (excluindo transferências)
    total_receber = sum(l.valor for l in lancamentos 
                       if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE)
    total_pagar = sum(l.valor for l in lancamentos 
                     if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE)
    
    receber_vencidos = sum(l.valor for l in lancamentos 
                          if l.tipo == TipoLancamento.RECEITA and 
                          l.status == StatusLancamento.PENDENTE and 
                          get_date(l.data_vencimento) < hoje)
    pagar_vencidos = sum(l.valor for l in lancamentos 
                        if l.tipo == TipoLancamento.DESPESA and 
                        l.status == StatusLancamento.PENDENTE and 
                        get_date(l.data_vencimento) < hoje)
    
    # Aging (análise de vencimento) - excluindo transferências
    pendentes = [l for l in lancamentos if l.status == StatusLancamento.PENDENTE and l.tipo != TipoLancamento.TRANSFERENCIA]
    
    vencidos = sum(l.valor for l in pendentes if (get_date(l.data_vencimento) - hoje).days < 0)  # type: ignore
    ate_7 = sum(l.valor for l in pendentes if 0 <= (get_date(l.data_vencimento) - hoje).days <= 7)  # type: ignore
    ate_15 = sum(l.valor for l in pendentes if 7 < (get_date(l.data_vencimento) - hoje).days <= 15)  # type: ignore
    ate_30 = sum(l.valor for l in pendentes if 15 < (get_date(l.data_vencimento) - hoje).days <= 30)  # type: ignore
    ate_60 = sum(l.valor for l in pendentes if 30 < (get_date(l.data_vencimento) - hoje).days <= 60)  # type: ignore
    ate_90 = sum(l.valor for l in pendentes if 60 < (get_date(l.data_vencimento) - hoje).days <= 90)  # type: ignore
    acima_90 = sum(l.valor for l in pendentes if (get_date(l.data_vencimento) - hoje).days > 90)  # type: ignore
    
    return jsonify({
        'total_receber': float(total_receber),
        'total_pagar': float(total_pagar),
        'receber_vencidos': float(receber_vencidos),
        'pagar_vencidos': float(pagar_vencidos),
        'aging': {
            'vencidos': float(vencidos),
            'ate_7': float(ate_7),
            'ate_15': float(ate_15),
            'ate_30': float(ate_30),
            'ate_60': float(ate_60),
            'ate_90': float(ate_90),
            'acima_90': float(acima_90)
        }
    })


@relatorios_bp.route('/resumo-parceiros', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_resumo_parceiros():
    """
    Relatório de resumo por cliente/fornecedor
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        
        # Agrupar por pessoa
        resumo_clientes = {}
        resumo_fornecedores = {}
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim and l.pessoa:
                    valor = float(l.valor)
                    categoria = l.categoria or 'Sem categoria'
                    
                    if l.tipo == TipoLancamento.RECEITA:
                        if l.pessoa not in resumo_clientes:
                            resumo_clientes[l.pessoa] = {'total': 0, 'quantidade': 0, 'categorias': {}}
                        resumo_clientes[l.pessoa]['total'] += valor
                        resumo_clientes[l.pessoa]['quantidade'] += 1
                        # Contar por categoria
                        if categoria not in resumo_clientes[l.pessoa]['categorias']:
                            resumo_clientes[l.pessoa]['categorias'][categoria] = 0
                        resumo_clientes[l.pessoa]['categorias'][categoria] += valor
                    else:
                        if l.pessoa not in resumo_fornecedores:
                            resumo_fornecedores[l.pessoa] = {'total': 0, 'quantidade': 0, 'categorias': {}}
                        resumo_fornecedores[l.pessoa]['total'] += valor
                        resumo_fornecedores[l.pessoa]['quantidade'] += 1
                        # Contar por categoria
                        if categoria not in resumo_fornecedores[l.pessoa]['categorias']:
                            resumo_fornecedores[l.pessoa]['categorias'][categoria] = 0
                        resumo_fornecedores[l.pessoa]['categorias'][categoria] += valor
        
        # Adicionar categoria principal para cada cliente/fornecedor
        for pessoa, dados in resumo_clientes.items():
            if dados['categorias']:
                categoria_principal = max(dados['categorias'].items(), key=lambda x: x[1])
                dados['categoria_principal'] = categoria_principal[0]
            else:
                dados['categoria_principal'] = 'Sem categoria'
        
        for pessoa, dados in resumo_fornecedores.items():
            if dados['categorias']:
                categoria_principal = max(dados['categorias'].items(), key=lambda x: x[1])
                dados['categoria_principal'] = categoria_principal[0]
            else:
                dados['categoria_principal'] = 'Sem categoria'
        
        return jsonify({
            'clientes': resumo_clientes,
            'fornecedores': resumo_fornecedores,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/analise-categorias', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_analise_categorias():
    """
    Relatório de análise por categorias
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        data_inicio = request.args.get('data_inicio', (date.today() - timedelta(days=30)).isoformat())
        data_fim = request.args.get('data_fim', date.today().isoformat())
        
        data_inicio = datetime.fromisoformat(data_inicio).date()
        data_fim = datetime.fromisoformat(data_fim).date()
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        
        # Agrupar por categoria e subcategoria
        receitas = {}
        despesas = {}
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim:
                    categoria = l.categoria or 'Sem Categoria'
                    subcategoria = l.subcategoria or 'Sem Subcategoria'
                    valor = float(l.valor)
                    
                    if l.tipo == TipoLancamento.RECEITA:
                        if categoria not in receitas:
                            receitas[categoria] = {}
                        if subcategoria not in receitas[categoria]:
                            receitas[categoria][subcategoria] = {'total': 0, 'quantidade': 0}
                        receitas[categoria][subcategoria]['total'] += valor
                        receitas[categoria][subcategoria]['quantidade'] += 1
                    else:
                        if categoria not in despesas:
                            despesas[categoria] = {}
                        if subcategoria not in despesas[categoria]:
                            despesas[categoria][subcategoria] = {'total': 0, 'quantidade': 0}
                        despesas[categoria][subcategoria]['total'] += valor
                        despesas[categoria][subcategoria]['quantidade'] += 1
        
        return jsonify({
            'receitas': receitas,
            'despesas': despesas,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/comparativo-periodos', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_comparativo_periodos():
    """
    Relatório comparativo entre períodos
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        # Período 1
        data_inicio1 = request.args.get('data_inicio1')
        data_fim1 = request.args.get('data_fim1')
        
        # Período 2
        data_inicio2 = request.args.get('data_inicio2')
        data_fim2 = request.args.get('data_fim2')
        
        if not all([data_inicio1, data_fim1, data_inicio2, data_fim2]):
            return jsonify({'error': 'Parâmetros de datas obrigatórios'}), 400
        
        data_inicio1 = datetime.fromisoformat(data_inicio1).date()
        data_fim1 = datetime.fromisoformat(data_fim1).date()
        data_inicio2 = datetime.fromisoformat(data_inicio2).date()
        data_fim2 = datetime.fromisoformat(data_fim2).date()
        
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        
        def calcular_periodo(data_ini, data_fim):
            receitas = Decimal('0')
            despesas = Decimal('0')
            receitas_por_categoria = {}
            despesas_por_categoria = {}
            receitas_por_subcategoria = {}
            despesas_por_subcategoria = {}
            
            for l in lancamentos:
                if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                    data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                    if data_ini <= data_pag <= data_fim:
                        valor = Decimal(str(l.valor))
                        categoria = l.categoria or 'Sem categoria'
                        subcategoria = l.subcategoria or 'Sem subcategoria'
                        chave_completa = f"{categoria} > {subcategoria}"
                        
                        if l.tipo == TipoLancamento.RECEITA:
                            receitas += valor
                            receitas_por_categoria[categoria] = receitas_por_categoria.get(categoria, Decimal('0')) + valor
                            receitas_por_subcategoria[chave_completa] = receitas_por_subcategoria.get(chave_completa, Decimal('0')) + valor
                        else:
                            despesas += valor
                            despesas_por_categoria[categoria] = despesas_por_categoria.get(categoria, Decimal('0')) + valor
                            despesas_por_subcategoria[chave_completa] = despesas_por_subcategoria.get(chave_completa, Decimal('0')) + valor
            
            # Encontrar maiores por categoria
            maior_receita_cat = max(receitas_por_categoria.items(), key=lambda x: x[1]) if receitas_por_categoria else ('Nenhuma', Decimal('0'))
            maior_despesa_cat = max(despesas_por_categoria.items(), key=lambda x: x[1]) if despesas_por_categoria else ('Nenhuma', Decimal('0'))
            
            # Encontrar maiores por subcategoria
            maior_receita_sub = max(receitas_por_subcategoria.items(), key=lambda x: x[1]) if receitas_por_subcategoria else ('Nenhuma', Decimal('0'))
            maior_despesa_sub = max(despesas_por_subcategoria.items(), key=lambda x: x[1]) if despesas_por_subcategoria else ('Nenhuma', Decimal('0'))
            
            # Top 3 categorias
            top_receitas = sorted(receitas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
            top_despesas = sorted(despesas_por_categoria.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                'receitas': float(receitas),
                'despesas': float(despesas),
                'saldo': float(receitas - despesas),
                'maior_receita': {'categoria': maior_receita_cat[0], 'valor': float(maior_receita_cat[1])},
                'maior_despesa': {'categoria': maior_despesa_cat[0], 'valor': float(maior_despesa_cat[1])},
                'maior_receita_sub': {'subcategoria': maior_receita_sub[0], 'valor': float(maior_receita_sub[1])},
                'maior_despesa_sub': {'subcategoria': maior_despesa_sub[0], 'valor': float(maior_despesa_sub[1])},
                'top_receitas': [{'categoria': k, 'valor': float(v), 'percentual': float(v/receitas*100) if receitas > 0 else 0} for k, v in top_receitas],
                'top_despesas': [{'categoria': k, 'valor': float(v), 'percentual': float(v/despesas*100) if despesas > 0 else 0} for k, v in top_despesas],
                'qtd_categorias_receitas': len(receitas_por_categoria),
                'qtd_categorias_despesas': len(despesas_por_categoria)
            }
        
        periodo1 = calcular_periodo(data_inicio1, data_fim1)
        periodo2 = calcular_periodo(data_inicio2, data_fim2)
        
        # Calcular variações
        variacao_receitas = ((periodo2['receitas'] - periodo1['receitas']) / periodo1['receitas'] * 100) if periodo1['receitas'] > 0 else 0
        variacao_despesas = ((periodo2['despesas'] - periodo1['despesas']) / periodo1['despesas'] * 100) if periodo1['despesas'] > 0 else 0
        variacao_saldo = ((periodo2['saldo'] - periodo1['saldo']) / abs(periodo1['saldo']) * 100) if periodo1['saldo'] != 0 else 0
        
        return jsonify({
            'periodo1': {
                'datas': {'inicio': data_inicio1.isoformat(), 'fim': data_fim1.isoformat()},
                'dados': periodo1
            },
            'periodo2': {
                'datas': {'inicio': data_inicio2.isoformat(), 'fim': data_fim2.isoformat()},
                'dados': periodo2
            },
            'variacoes': {
                'receitas': round(variacao_receitas, 2),
                'despesas': round(variacao_despesas, 2),
                'saldo': round(variacao_saldo, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/indicadores', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_indicadores():
    """
    Relatório de indicadores financeiros
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        contas = db.listar_contas_por_empresa(empresa_id=empresa_id)
        
        # Obter filtros de data
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        hoje = date.today()
        
        if data_inicio_str and data_fim_str:
            inicio_mes = parse_date(data_inicio_str)
            fim_periodo = parse_date(data_fim_str)
        else:
            # Padrão: mês atual
            inicio_mes = date(hoje.year, hoje.month, 1)
            fim_periodo = hoje
        
        # Totais do mês atual
        receitas_mes = Decimal('0')
        despesas_mes = Decimal('0')
        
        # Totais a receber/pagar
        total_receber = Decimal('0')
        total_pagar = Decimal('0')
        
        # Vencidos
        vencidos_receber = Decimal('0')
        vencidos_pagar = Decimal('0')
        
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento and l.tipo != TipoLancamento.TRANSFERENCIA:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_pag >= inicio_mes and data_pag <= fim_periodo:
                    valor = Decimal(str(l.valor))
                    if l.tipo == TipoLancamento.RECEITA:
                        receitas_mes += valor
                    else:
                        despesas_mes += valor
            
            if l.status == StatusLancamento.PENDENTE:
                valor = Decimal(str(l.valor))
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                
                if l.tipo == TipoLancamento.RECEITA:
                    total_receber += valor
                    if data_venc < hoje:
                        vencidos_receber += valor
                else:
                    total_pagar += valor
                    if data_venc < hoje:
                        vencidos_pagar += valor
        
        # Saldo em caixa
        saldo_caixa = sum(Decimal(str(c.saldo_inicial)) for c in contas)
        
        # Liquidez = (Saldo + A Receber) / A Pagar
        liquidez = float((saldo_caixa + total_receber) / total_pagar) if total_pagar > 0 else 0
        
        # Margem líquida = (Receitas - Despesas) / Receitas * 100
        margem = float((receitas_mes - despesas_mes) / receitas_mes * 100) if receitas_mes > 0 else 0
        
        return jsonify({
            'saldo_caixa': float(saldo_caixa),
            'mes_atual': {
                'receitas': float(receitas_mes),
                'despesas': float(despesas_mes),
                'saldo': float(receitas_mes - despesas_mes)
            },
            'pendentes': {
                'receber': float(total_receber),
                'pagar': float(total_pagar)
            },
            'vencidos': {
                'receber': float(vencidos_receber),
                'pagar': float(vencidos_pagar)
            },
            'indicadores': {
                'liquidez': round(liquidez, 2),
                'margem_liquida': round(margem, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/inadimplencia', methods=['GET'])
@require_permission('relatorios_view')
def relatorio_inadimplencia():
    """
    Relatório de inadimplência
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
    from flask import session
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    try:
        lancamentos = db.listar_lancamentos(empresa_id=empresa_id)
        hoje = date.today()
        
        inadimplentes = []
        
        for l in lancamentos:
            # Excluir transferências e considerar apenas PENDENTES
            if l.tipo == TipoLancamento.TRANSFERENCIA:
                continue
                
            if l.status == StatusLancamento.PENDENTE:
                # Converter data_vencimento para date se for datetime
                data_venc = l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento
                
                # Verificar se está vencido (data anterior a hoje)
                if data_venc < hoje:
                    dias_atraso = (hoje - data_venc).days
                    inadimplentes.append({
                        'id': l.id,
                        'tipo': l.tipo.value.upper(),
                        'descricao': l.descricao,
                        'valor': float(l.valor),
                        'data_vencimento': data_venc.isoformat(),
                        'dias_atraso': dias_atraso,
                        'pessoa': l.pessoa or 'Não informado',
                        'categoria': l.categoria or 'Sem categoria'
                    })
        
        # Ordenar por dias de atraso (maior primeiro)
        inadimplentes.sort(key=lambda x: x['dias_atraso'], reverse=True)
        
        # Calcular totais
        total_inadimplente = sum(i['valor'] for i in inadimplentes)
        total_receitas_vencidas = sum(i['valor'] for i in inadimplentes if i['tipo'] == 'RECEITA')
        total_despesas_vencidas = sum(i['valor'] for i in inadimplentes if i['tipo'] == 'DESPESA')
        
        return jsonify({
            'inadimplentes': inadimplentes,
            'total': float(total_inadimplente),
            'total_receitas': float(total_receitas_vencidas),
            'total_despesas': float(total_despesas_vencidas),
            'quantidade': len(inadimplentes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RELATÓRIO DE CONTROLE DE HORAS
# ============================================================================

@relatorios_bp.route('/controle-horas', methods=['GET'])
@require_permission('contratos_view')
def relatorio_controle_horas():
    """
    Relatório de controle de horas dos contratos
    
    Retorna resumo geral e detalhamento por contrato com sessões
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        from flask import session
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Gerar relatório
        dados = db.gerar_relatorio_controle_horas(empresa_id=empresa_id)
        
        return jsonify({
            'success': True,
            'dados': dados
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório de controle de horas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@relatorios_bp.route('/controle-horas/exportar/pdf', methods=['GET'])
@require_permission('contratos_view')
def exportar_controle_horas_pdf():
    """Exporta relatório de controle de horas para PDF"""
    try:
        from flask import send_file, session
        from pdf_export import gerar_relatorio_controle_horas_pdf
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Buscar dados da empresa
        empresa = db.obter_empresa(empresa_id)
        nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'
        
        # Gerar dados do relatório
        dados = db.gerar_relatorio_controle_horas(empresa_id=empresa_id)
        
        # Gerar PDF
        buffer = gerar_relatorio_controle_horas_pdf(dados, nome_empresa)
        
        filename = f"controle_horas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@relatorios_bp.route('/controle-horas/exportar/excel', methods=['GET'])
@require_permission('contratos_view')
def exportar_controle_horas_excel():
    """Exporta relatório de controle de horas para Excel"""
    try:
        from flask import send_file, session
        from pdf_export import gerar_relatorio_controle_horas_excel
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Buscar dados da empresa
        empresa = db.obter_empresa(empresa_id)
        nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'
        
        # Gerar dados do relatório
        dados = db.gerar_relatorio_controle_horas(empresa_id=empresa_id)
        
        # Gerar Excel
        buffer = gerar_relatorio_controle_horas_excel(dados, nome_empresa)
        
        filename = f"controle_horas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro ao exportar Excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

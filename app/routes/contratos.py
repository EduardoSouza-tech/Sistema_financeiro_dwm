"""
🤝 Blueprint de Contratos
=========================

Gerencia endpoints relacionados a contratos.
Extraído de web_server.py na Fase 5 da otimização.

Autor: Sistema de Otimização - Fase 5
Data: 20/01/2026
"""

from flask import Blueprint, request, jsonify, session
from auth_middleware import require_permission, filtrar_por_cliente, get_usuario_logado
from auth_functions import obter_permissoes_usuario_empresa
import database_postgresql as db

# Criar blueprint
contratos_bp = Blueprint('contratos', __name__, url_prefix='/api/contratos')


@contratos_bp.route('', methods=['GET', 'POST'])
def contratos():
    """
    Gerenciar contratos - Listar todos ou criar novo
    
    Security:
        🔒 Validado empresa_id da sessão e permissões
    """
    # Validar autenticação
    usuario = get_usuario_logado()
    if not usuario:
        print("❌ [CONTRATOS] Usuário não autenticado")
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    # Validar empresa
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        print("❌ [CONTRATOS] Empresa não selecionada")
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    # Admin tem todas as permissões
    if usuario.get('tipo') == 'admin':
        print("✅ [CONTRATOS] Admin - permissão concedida")
    else:
        # Buscar permissões da empresa
        permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
        print(f"🔒 [CONTRATOS] Permissões da empresa {empresa_id}: {permissoes}")
        
        if 'contratos_view' not in permissoes:
            print("❌ [CONTRATOS] Sem permissão contratos_view")
            return jsonify({'error': 'Sem permissão para visualizar contratos'}), 403
    
    if request.method == 'GET':
        try:
            print(f"📋 [CONTRATOS] GET - empresa_id: {empresa_id}, usuario_id: {usuario.get('id')}")
            
            # 🔒 Passar empresa_id explicitamente
            contratos = db.listar_contratos(empresa_id=empresa_id)
            
            print(f"📋 [CONTRATOS] Total de contratos: {len(contratos)}")
            
            # Adicionar cliente_nome do join se não vier no contrato
            for contrato in contratos:
                if 'cliente_nome' not in contrato:
                    contrato['cliente_nome'] = contrato.get('cliente', '')
            
            # 🔧 FIX: Adicionar empresa_id ao dict do usuario para o filtro funcionar
            usuario_com_empresa = usuario.copy()
            usuario_com_empresa['empresa_id'] = empresa_id
            
            # Aplicar filtro por cliente se necessário
            contratos_filtrados = filtrar_por_cliente(contratos, usuario_com_empresa)
            
            print(f"📋 [CONTRATOS] Após filtro por cliente: {len(contratos_filtrados)}")
            
            return jsonify(contratos_filtrados)
        except Exception as e:
            print(f"❌ [CONTRATOS] Erro no GET: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    else:  # POST
        # Validação de permissão de edição para POST
        if usuario.get('tipo') != 'admin':
            permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
            if 'contratos_edit' not in permissoes:
                print("❌ [CONTRATOS] Sem permissão contratos_edit")
                return jsonify({'error': 'Sem permissão para criar contratos'}), 403
            
        try:
            data = request.json
            print(f"🔍 Criando contrato com dados: {data}")
            
            # Gerar número automaticamente se não fornecido
            if not data.get('numero'):
                data['numero'] = db.gerar_proximo_numero_contrato()
            
            # 🔒 Passar empresa_id explicitamente
            contrato_id = db.adicionar_contrato(empresa_id=empresa_id, dados=data)
            print(f"✅ Contrato criado com ID: {contrato_id}")
            return jsonify({
                'success': True,
                'message': 'Contrato criado com sucesso',
                'id': contrato_id
            }), 201
        except Exception as e:
            print(f"❌ Erro ao criar contrato: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@contratos_bp.route('/proximo-numero', methods=['GET'])
def proximo_numero_contrato():
    """Retorna o próximo número de contrato disponível"""
    # Validar autenticação
    usuario = get_usuario_logado()
    if not usuario:
        print("❌ [CONTRATOS] Usuário não autenticado")
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        print("❌ [CONTRATOS] Empresa não selecionada")
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    # Admin tem todas as permissões
    if usuario.get('tipo') == 'admin':
        print("✅ [CONTRATOS] Admin - permissão concedida")
    else:
        # Buscar permissões da empresa
        permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
        print(f"🔒 [CONTRATOS] Permissões da empresa {empresa_id}: {permissoes}")
        
        if 'contratos_view' not in permissoes:
            print("❌ [CONTRATOS] Sem permissão contratos_view")
            return jsonify({'error': 'Sem permissão para visualizar contratos'}), 403
    
    try:
        print("🔍 Gerando próximo número de contrato...")
        numero = db.gerar_proximo_numero_contrato()
        print(f"✅ Número gerado: {numero}")
        return jsonify({'numero': numero})
    except Exception as e:
        print(f"❌ Erro ao gerar número: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@contratos_bp.route('/<int:contrato_id>', methods=['GET', 'PUT', 'DELETE'])
def contrato_detalhes(contrato_id):
    """Buscar, atualizar ou excluir contrato específico"""
    # Validar autenticação
    usuario = get_usuario_logado()
    if not usuario:
        print("❌ [CONTRATOS] Usuário não autenticado")
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        print("❌ [CONTRATOS] Empresa não selecionada")
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    # Validar permissões baseado no método
    if usuario.get('tipo') != 'admin':
        permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
        print(f"🔒 [CONTRATOS] Permissões da empresa {empresa_id}: {permissoes}")
        
        if request.method == 'GET':
            if 'contratos_view' not in permissoes:
                print("❌ [CONTRATOS] Sem permissão contratos_view")
                return jsonify({'error': 'Sem permissão para visualizar contratos'}), 403
        else:  # PUT ou DELETE
            if 'contratos_edit' not in permissoes:
                print("❌ [CONTRATOS] Sem permissão contratos_edit")
                return jsonify({'error': 'Sem permissão para editar/excluir contratos'}), 403
    else:
        print("✅ [CONTRATOS] Admin - permissão concedida")
    
    if request.method == 'GET':
        try:
            
            print(f"🔍 Buscando contrato {contrato_id}")
            # 🔒 Passar empresa_id explicitamente
            contratos = db.listar_contratos(empresa_id=empresa_id)
            contrato = next((c for c in contratos if c.get('id') == contrato_id), None)
            
            if contrato:
                print(f"✅ Contrato {contrato_id} encontrado")
                return jsonify({'success': True, 'contrato': contrato})
            
            print(f"❌ Contrato {contrato_id} não encontrado")
            return jsonify({'success': False, 'error': 'Contrato não encontrado'}), 404
            
        except Exception as e:
            print(f"❌ Erro ao buscar contrato {contrato_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
            
    elif request.method == 'PUT':
        try:
            data = request.json
            print(f"🔍 Atualizando contrato {contrato_id} com dados: {data}")
            success = db.atualizar_contrato(contrato_id, data)
            if success:
                print(f"✅ Contrato {contrato_id} atualizado")
                return jsonify({'success': True, 'message': 'Contrato atualizado com sucesso'})
            print(f"❌ Contrato {contrato_id} não encontrado")
            return jsonify({'success': False, 'error': 'Contrato não encontrado'}), 404
        except Exception as e:
            print(f"❌ Erro ao atualizar contrato {contrato_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # DELETE
        try:
            print(f"🔍 Deletando contrato {contrato_id}")
            success = db.deletar_contrato(contrato_id)
            if success:
                print(f"✅ Contrato {contrato_id} deletado")
                return jsonify({'success': True, 'message': 'Contrato excluído com sucesso'})
            print(f"❌ Contrato {contrato_id} não encontrado")
            return jsonify({'success': False, 'error': 'Contrato não encontrado'}), 404
        except Exception as e:
            print(f"❌ Erro ao deletar contrato {contrato_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HISTÓRICO MENSAL
# ============================================================================

@contratos_bp.route('/<int:contrato_id>/historico-mes', methods=['PATCH'])
def atualizar_historico_mes(contrato_id):
    """Atualiza o estado de um mês no histórico do contrato (NF, pagamento, pular).
    Body: { "mes": "2025-04", "campo": "nf_emitida"|"pago"|"pulado", "valor": true|false }
    """
    usuario = get_usuario_logado()
    if not usuario:
        return jsonify({'error': 'Não autenticado'}), 401
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403

    data = request.json or {}
    mes = data.get('mes', '').strip()          # ex: "2025-04"
    campo = data.get('campo', '').strip()
    valor = data.get('valor')

    # Campos booleanos legados
    CAMPOS_BOOL = ('nf_emitida', 'pago', 'pulado')
    # Campos de string com valores permitidos (None = qualquer string, incluindo vazio)
    CAMPOS_STR = {
        'nf_status':         ('emitida', 'no_prazo', 'atrasada', 'na', ''),
        'pagamento_status':  ('pago', 'parcial', 'atrasado', 'nao_pago', ''),
        'entrega_status':    ('entregue', 'parcial', 'atrasada', 'nao_realizada', ''),
        'data_pagamento':    None,  # data livre (YYYY-MM-DD ou string vazia)
        'horas_ajuste':      None,  # número livre — horas usadas manuais para o mês
        'valor_mes':         None,  # número livre — valor/NF do mês (override)
    }
    # Campo especial: entrega por sessão
    CAMPO_SESSAO_ENTREGA = 'sessao_entrega'
    VALID_ENTREGA = ('entregue', 'parcial', 'atrasada', 'nao_realizada', '')

    import re
    if not re.match(r'^\d{4}-\d{2}$', mes) and mes != 'unico':
        return jsonify({'error': 'Mês inválido'}), 400
    if campo not in CAMPOS_BOOL and campo not in CAMPOS_STR and campo != CAMPO_SESSAO_ENTREGA:
        return jsonify({'error': f'Campo inválido: {campo}'}), 400
    if campo in CAMPOS_STR and CAMPOS_STR[campo] is not None:
        # Sanitização: aceitar apenas valores da lista permitida
        if valor not in CAMPOS_STR[campo] and valor is not None:
            return jsonify({'error': f'Valor inválido para {campo}: {valor}'}), 400

    try:
        import json
        from database_postgresql import get_db_connection
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT observacoes FROM contratos WHERE id = %s", (contrato_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Contrato não encontrado'}), 404

            try:
                obs = json.loads(row['observacoes']) if row['observacoes'] else {}
            except Exception:
                obs = {}

            if 'historico_mensal' not in obs:
                obs['historico_mensal'] = {}
            if mes not in obs['historico_mensal']:
                obs['historico_mensal'][mes] = {}

            if campo in CAMPOS_BOOL:
                obs['historico_mensal'][mes][campo] = bool(valor)
            elif campo in ('horas_ajuste', 'valor_mes'):
                # Campos numéricos: vazio/None remove (volta ao automático)
                if valor == '' or valor is None:
                    obs['historico_mensal'][mes].pop(campo, None)
                else:
                    try:
                        obs['historico_mensal'][mes][campo] = float(valor)
                    except (ValueError, TypeError):
                        return jsonify({'error': f'Valor numérico inválido para {campo}'}), 400
            elif campo == CAMPO_SESSAO_ENTREGA:
                # valor = {"sessao_id": "456", "status": "entregue"}
                try:
                    payload = json.loads(valor) if isinstance(valor, str) else valor
                    sessao_id = str(payload.get('sessao_id', ''))
                    status    = payload.get('status', '')
                except Exception:
                    return jsonify({'error': 'sessao_entrega: valor deve ser JSON {"sessao_id":..., "status":...}'}), 400
                if status not in VALID_ENTREGA:
                    return jsonify({'error': f'Status de entrega inválido: {status}'}), 400
                if 'sessoes_entrega' not in obs['historico_mensal'][mes]:
                    obs['historico_mensal'][mes]['sessoes_entrega'] = {}
                if status == '':
                    obs['historico_mensal'][mes]['sessoes_entrega'].pop(sessao_id, None)
                else:
                    obs['historico_mensal'][mes]['sessoes_entrega'][sessao_id] = status
            else:
                # String vazia ou None remove o campo para voltar ao modo automático
                if valor == '' or valor is None:
                    obs['historico_mensal'][mes].pop(campo, None)
                else:
                    obs['historico_mensal'][mes][campo] = str(valor)

            cursor.execute(
                "UPDATE contratos SET observacoes = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (json.dumps(obs), contrato_id)
            )
            sucesso = cursor.rowcount > 0

        if sucesso:
            return jsonify({'success': True, 'mes': mes, 'campo': campo})
        return jsonify({'error': 'Contrato não encontrado'}), 404
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@contratos_bp.route('/<int:contrato_id>/observacoes', methods=['PATCH'])
def atualizar_observacoes_raiz(contrato_id):
    """Atualiza campos raiz de observacoes (horas_acumuladas_inicial, horas_acumuladas_atual).
    Body: { "campo": "horas_acumuladas_inicial", "valor": 5.0 }
    """
    usuario = get_usuario_logado()
    if not usuario:
        return jsonify({'error': 'Não autenticado'}), 401
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403

    data   = request.json or {}
    campo  = data.get('campo', '').strip()
    valor  = data.get('valor')

    CAMPOS_PERMITIDOS = ('horas_acumuladas_inicial', 'horas_acumuladas_atual')
    if campo not in CAMPOS_PERMITIDOS:
        return jsonify({'error': f'Campo inválido: {campo}'}), 400

    # Converte para float; None / '' → 0
    try:
        valor_f = float(valor) if (valor is not None and valor != '') else 0.0
    except (ValueError, TypeError):
        return jsonify({'error': 'Valor numérico inválido'}), 400

    try:
        import json
        from database_postgresql import get_db_connection
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT observacoes FROM contratos WHERE id = %s", (contrato_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Contrato não encontrado'}), 404
            try:
                obs = json.loads(row['observacoes']) if row['observacoes'] else {}
            except Exception:
                obs = {}
            obs[campo] = valor_f
            cursor.execute(
                "UPDATE contratos SET observacoes = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (json.dumps(obs), contrato_id)
            )
            sucesso = cursor.rowcount > 0
        if sucesso:
            return jsonify({'success': True, 'campo': campo, 'valor': valor_f})
        return jsonify({'error': 'Contrato não encontrado'}), 404
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXPORTAÇÕES
# ============================================================================

@contratos_bp.route('/exportar/pdf', methods=['GET'])
@require_permission('contratos_view')
def exportar_contratos_pdf():
    """Exporta contratos para PDF"""
    try:
        from flask import send_file, session
        import database_postgresql as db
        from pdf_export import gerar_contratos_pdf
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Buscar dados da empresa
        empresa = db.obter_empresa(empresa_id)
        nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'
        
        # Buscar contratos
        contratos = db.listar_contratos(empresa_id=empresa_id)
        
        # Gerar PDF
        buffer = gerar_contratos_pdf(contratos, nome_empresa)
        
        filename = f"contratos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
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


@contratos_bp.route('/exportar/excel', methods=['GET'])
@require_permission('contratos_view')
def exportar_contratos_excel():
    """Exporta contratos para Excel"""
    try:
        from flask import send_file, session
        import database_postgresql as db
        from pdf_export import gerar_contratos_excel
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Buscar dados da empresa
        empresa = db.obter_empresa(empresa_id)
        nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'
        
        # Buscar contratos
        contratos = db.listar_contratos(empresa_id=empresa_id)
        
        # Gerar Excel
        buffer = gerar_contratos_excel(contratos, nome_empresa)
        
        filename = f"contratos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
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


# ============================================================================
# COMPENSAÇÃO DE HORAS ENTRE CONTRATOS
# ============================================================================

@contratos_bp.route('/<int:contrato_id>/status', methods=['PATCH'])
@require_permission('contratos_edit')
def atualizar_status_contrato(contrato_id: int):
    """Atualiza apenas o status de um contrato"""
    data = request.json or {}
    novo_status = data.get('status', '').strip()
    status_validos = {'Aberto', 'Editado', 'Entregue', 'ativo', 'inativo', 'cancelado'}
    if novo_status not in status_validos:
        return jsonify({'success': False, 'error': f'Status inválido: {novo_status}'}), 400

    empresa_id = session.get('empresa_id')
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE contratos SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (novo_status, contrato_id)
            )
            sucesso = cursor.rowcount > 0
        if sucesso:
            return jsonify({'success': True, 'status': novo_status})
        return jsonify({'success': False, 'error': 'Contrato não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contratos_bp.route('/<int:origem_id>/compensar-horas', methods=['POST'])
@require_permission('contratos_edit')
def compensar_horas_contratos(origem_id: int):
    """
    Transfere horas de um contrato para outro do mesmo cliente
    
    POST /api/contratos/32/compensar-horas
    {
        "contrato_destino_id": 33,
        "quantidade_horas": 10.5,
        "observacao": "Compensação por excesso em eventos"
    }
    
    Returns:
        200: Compensação realizada com sucesso
        400: Validação falhou (saldo insuficiente, clientes diferentes, etc.)
        403: Sem permissão
        500: Erro interno
    """
    try:
        # ✅ Usar request.usuario ao invés de session
        # O middleware @require_permission já garante que request.usuario existe
        usuario_id = request.usuario.get('id') if hasattr(request, 'usuario') else None
        empresa_id = session.get('empresa_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Usuário não identificado'}), 403
        
        data = request.json
        print(f"📦 Dados recebidos: {data}")
        
        destino_id = data.get('contrato_destino_id')
        quantidade_horas = data.get('quantidade_horas')
        observacao = data.get('observacao', '')
        
        # Validações de entrada
        if not destino_id:
            return jsonify({'success': False, 'error': 'Contrato destino não informado'}), 400
        
        if not quantidade_horas:
            return jsonify({'success': False, 'error': 'Quantidade de horas não informada'}), 400
        
        try:
            quantidade_horas = float(quantidade_horas)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Quantidade de horas inválida'}), 400
        
        if quantidade_horas <= 0:
            return jsonify({'success': False, 'error': 'Quantidade deve ser maior que zero'}), 400
        
        if origem_id == destino_id:
            return jsonify({'success': False, 'error': 'Origem e destino não podem ser iguais'}), 400
        
        print(f"✅ Validações básicas OK")
        print(f"   - Origem: {origem_id}")
        print(f"   - Destino: {destino_id}")
        print(f"   - Quantidade: {quantidade_horas}h")
        print(f"   - Observação: {observacao[:50]}..." if len(observacao) > 50 else f"   - Observação: {observacao}")
        
        # Executar compensação
        resultado = db.compensar_horas_contratos(
            empresa_id=empresa_id,
            origem_id=origem_id,
            destino_id=destino_id,
            quantidade_horas=quantidade_horas,
            observacao=observacao,
            usuario_id=usuario_id
        )
        
        print(f"✅ Compensação {resultado['compensacao_id']} realizada com sucesso!")
        print(f"   📤 {resultado['origem']['numero']}: {resultado['origem']['horas_restantes']}h restantes")
        print(f"   📥 {resultado['destino']['numero']}: {resultado['destino']['horas_restantes']}h restantes")
        
        return jsonify({
            'success': True,
            'message': f'Compensadas {quantidade_horas}h com sucesso',
            'data': resultado
        }), 200
        
    except ValueError as e:
        # Erros de validação de negócio
        print(f"⚠️ Validação falhou: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
        
    except Exception as e:
        print(f"❌ Erro ao compensar horas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500


@contratos_bp.route('/compensacoes-horas', methods=['GET'])
@require_permission('contratos_view')
def listar_compensacoes_horas():
    """
    Lista histórico de compensações de horas
    
    GET /api/contratos/compensacoes-horas?contrato_id=32
    
    Query params:
        contrato_id (opcional): Filtrar por contrato específico
    
    Returns:
        200: Lista de compensações
        403: Sem permissão
        500: Erro interno
    """
    try:
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
        
        contrato_id = request.args.get('contrato_id', type=int)
        
        compensacoes = db.listar_compensacoes_horas(
            empresa_id=empresa_id,
            contrato_id=contrato_id
        )
        
        return jsonify({
            'success': True,
            'data': compensacoes,
            'total': len(compensacoes)
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao listar compensações: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PARCELAS ====================

@contratos_bp.route('/<int:contrato_id>/parcelas', methods=['GET', 'POST'])
def parcelas_contrato(contrato_id):
    """GET: listar parcelas. POST: salvar parcelas (substitui tudo)."""
    usuario = get_usuario_logado()
    if not usuario:
        return jsonify({'error': 'Não autenticado'}), 401
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403

    if request.method == 'GET':
        try:
            parcelas = db.listar_parcelas_contrato(empresa_id=empresa_id, contrato_id=contrato_id)
            return jsonify({'success': True, 'data': parcelas})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    else:  # POST
        if usuario.get('tipo') != 'admin':
            permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
            if 'contratos_edit' not in permissoes:
                return jsonify({'error': 'Sem permissão'}), 403
        try:
            parcelas = request.json.get('parcelas', [])
            db.salvar_parcelas_contrato(empresa_id=empresa_id, contrato_id=contrato_id, parcelas=parcelas)
            return jsonify({'success': True, 'message': f'{len(parcelas)} parcela(s) salva(s)'})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@contratos_bp.route('/<int:contrato_id>/parcelas/<int:parcela_id>', methods=['PUT'])
def atualizar_parcela_contrato(contrato_id, parcela_id):
    """Atualiza uma parcela individual."""
    usuario = get_usuario_logado()
    if not usuario:
        return jsonify({'error': 'Não autenticado'}), 401
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403
    if usuario.get('tipo') != 'admin':
        permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
        if 'contratos_edit' not in permissoes:
            return jsonify({'error': 'Sem permissão'}), 403
    try:
        dados = request.json
        sucesso = db.atualizar_parcela(empresa_id=empresa_id, parcela_id=parcela_id, dados=dados)
        if sucesso:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Parcela não encontrada'}), 404
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

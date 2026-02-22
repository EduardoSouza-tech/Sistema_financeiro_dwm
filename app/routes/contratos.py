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
            
            # Adicionar cliente_id para cada contrato
            for contrato in contratos:
                contrato['cliente_id'] = contrato.get('cliente')
            
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
        empresa = db.buscar_empresa(empresa_id)
        nome_empresa = empresa.get('nome', 'Empresa') if empresa else 'Empresa'
        
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
        empresa = db.buscar_empresa(empresa_id)
        nome_empresa = empresa.get('nome', 'Empresa') if empresa else 'Empresa'
        
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

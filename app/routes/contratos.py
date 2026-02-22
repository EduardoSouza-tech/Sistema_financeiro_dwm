"""
🤝 Blueprint de Contratos
=========================

Gerencia endpoints relacionados a contratos.
Extraído de web_server.py na Fase 5 da otimização.

Autor: Sistema de Otimização - Fase 5
Data: 20/01/2026
"""

from flask import Blueprint, request, jsonify
from auth_middleware import require_permission, filtrar_por_cliente
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
    # Validar sessão e permissões
    from flask import session
    
    # Validar autenticação
    usuario = session.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    # Validar permissões
    permissoes = usuario.get('permissoes', [])
    if 'contratos_view' not in permissoes and 'admin' not in permissoes:
        return jsonify({'error': 'Sem permissão para visualizar contratos'}), 403
    
    # Validar empresa
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    if request.method == 'GET':
        try:
            print(f"📋 [CONTRATOS] GET - empresa_id: {empresa_id}, usuario_id: {usuario.get('id')}")
            
            # 🔒 Passar empresa_id explicitamente
            contratos = db.listar_contratos(empresa_id=empresa_id)
            
            print(f"📋 [CONTRATOS] Total de contratos: {len(contratos)}")
            
            # Adicionar cliente_id para cada contrato
            for contrato in contratos:
                contrato['cliente_id'] = contrato.get('cliente')
            
            # Aplicar filtro por cliente se necessário
            # Criar objeto request.usuario para compatibilidade
            class RequestUsuario:
                def __init__(self, user_data):
                    self.tipo = user_data.get('tipo')
                    self.cliente_id = user_data.get('cliente_id')
            
            request.usuario = RequestUsuario(usuario)
            contratos_filtrados = filtrar_por_cliente(contratos, request.usuario)
            
            print(f"📋 [CONTRATOS] Após filtro por cliente: {len(contratos_filtrados)}")
            
            return jsonify(contratos_filtrados)
        except Exception as e:
            print(f"❌ [CONTRATOS] Erro no GET: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    else:  # POST
        # Validar permissão de edição para POST
        if 'contratos_edit' not in permissoes and 'admin' not in permissoes:
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
    # Validar autenticação e permissões
    from flask import session
    
    usuario = session.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    permissoes = usuario.get('permissoes', [])
    if 'contratos_view' not in permissoes and 'admin' not in permissoes:
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
    # Validar autenticação e permissões
    from flask import session
    
    usuario = session.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    # Validar permissões baseado no método
    permissoes = usuario.get('permissoes', [])
    if request.method == 'GET':
        if 'contratos_view' not in permissoes and 'admin' not in permissoes:
            return jsonify({'error': 'Sem permissão para visualizar contratos'}), 403
    else:  # PUT ou DELETE
        if 'contratos_edit' not in permissoes and 'admin' not in permissoes:
            return jsonify({'error': 'Sem permissão para editar/excluir contratos'}), 403
    
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

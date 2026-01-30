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
@require_permission('contratos_view')
def contratos():
    """
    Gerenciar contratos - Listar todos ou criar novo
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    if request.method == 'GET':
        try:
            # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
            from flask import session
            empresa_id = session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
            # 🔒 Passar empresa_id explicitamente
            contratos = db.listar_contratos(empresa_id=empresa_id)
            
            # Adicionar cliente_id para cada contrato
            for contrato in contratos:
                contrato['cliente_id'] = contrato.get('cliente')
            
            # Aplicar filtro por cliente
            contratos_filtrados = filtrar_por_cliente(contratos, request.usuario)
            
            return jsonify(contratos_filtrados)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        try:
            # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
            from flask import session
            empresa_id = session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
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
@require_permission('contratos_view')
def proximo_numero_contrato():
    """Retorna o próximo número de contrato disponível"""
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
@require_permission('contratos_view')
def contrato_detalhes(contrato_id):
    """Buscar, atualizar ou excluir contrato específico"""
    if request.method == 'GET':
        try:
            # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
            from flask import session
            empresa_id = session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
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

"""
📋 Blueprint de Funções de Responsáveis
=========================================

Gerencia endpoints relacionados a funções/cargos de responsáveis por sessões.
(Fotógrafo, Videomaker, Editor, etc)

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

from flask import Blueprint, request, jsonify, session as flask_session
from auth_middleware import require_permission
import database_postgresql as db

# Criar blueprint
funcoes_bp = Blueprint('funcoes_responsaveis', __name__, url_prefix='/api/funcoes-responsaveis')


@funcoes_bp.route('', methods=['GET', 'POST'])
@require_permission('operacional_view')
def funcoes():
    """
    GET: Lista todas as funções
    POST: Cria nova função
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    if request.method == 'GET':
        try:
            empresa_id = flask_session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
            # Parâmetro opcional: incluir inativas
            incluir_inativas = request.args.get('incluir_inativas', 'false').lower() == 'true'
            
            funcoes = db.listar_funcoes_responsaveis(
                empresa_id=empresa_id,
                apenas_ativas=not incluir_inativas
            )
            
            print(f"✅ [GET /api/funcoes-responsaveis] Total: {len(funcoes)}")
            return jsonify(funcoes), 200
            
        except Exception as e:
            print(f"❌ Erro ao listar funções: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'erro': str(e)}), 500
    
    else:  # POST
        try:
            empresa_id = flask_session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
            data = request.get_json()
            
            # Validações
            if not data.get('nome'):
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            
            print(f"\n📝 [POST /api/funcoes-responsaveis]")
            print(f"   - nome: {data.get('nome')}")
            print(f"   - descricao: {data.get('descricao', '')}")
            
            funcao_id = db.adicionar_funcao_responsavel(
                empresa_id=empresa_id,
                dados=data
            )
            
            print(f"✅ Função criada: ID {funcao_id}")
            return jsonify({
                'success': True,
                'message': 'Função criada com sucesso',
                'id': funcao_id
            }), 201
            
        except Exception as e:
            print(f"❌ Erro ao criar função: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@funcoes_bp.route('/<int:funcao_id>', methods=['GET', 'PUT', 'DELETE'])
@require_permission('operacional_view')
def funcao_especifica(funcao_id):
    """
    GET: Busca função específica
    PUT: Atualiza função
    DELETE: Desativa função
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    empresa_id = flask_session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    if request.method == 'GET':
        try:
            funcao = db.obter_funcao_responsavel(
                empresa_id=empresa_id,
                funcao_id=funcao_id
            )
            
            if not funcao:
                return jsonify({'erro': 'Função não encontrada'}), 404
            
            return jsonify(funcao), 200
            
        except Exception as e:
            print(f"❌ Erro ao buscar função {funcao_id}: {e}")
            return jsonify({'erro': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data.get('nome'):
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            
            print(f"\n📝 [PUT /api/funcoes-responsaveis/{funcao_id}]")
            print(f"   - nome: {data.get('nome')}")
            
            sucesso = db.atualizar_funcao_responsavel(
                empresa_id=empresa_id,
                funcao_id=funcao_id,
                dados=data
            )
            
            if sucesso:
                print(f"✅ Função {funcao_id} atualizada")
                return jsonify({
                    'success': True,
                    'message': 'Função atualizada com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Função não encontrada'
                }), 404
                
        except Exception as e:
            print(f"❌ Erro ao atualizar função {funcao_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # DELETE
        try:
            print(f"\n🗑️ [DELETE /api/funcoes-responsaveis/{funcao_id}]")
            
            sucesso = db.deletar_funcao_responsavel(
                empresa_id=empresa_id,
                funcao_id=funcao_id
            )
            
            if sucesso:
                print(f"✅ Função {funcao_id} desativada")
                return jsonify({
                    'success': True,
                    'message': 'Função desativada com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Função não encontrada'
                }), 404
                
        except Exception as e:
            print(f"❌ Erro ao deletar função {funcao_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

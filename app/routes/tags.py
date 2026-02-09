"""
🏷️ Blueprint de Tags
=====================

Gerencia endpoints relacionados a tags para categorização de sessões.
(Urgente, VIP, Comercial, Social, etc)

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

from flask import Blueprint, request, jsonify, session as flask_session
from auth_middleware import require_permission
import database_postgresql as db

# Criar blueprint
tags_bp = Blueprint('tags', __name__, url_prefix='/api/tags')


@tags_bp.route('', methods=['GET', 'POST'])
@require_permission('operacional_view')
def tags():
    """
    GET: Lista todas as tags
    POST: Cria nova tag
    
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
            
            tags = db.listar_tags(
                empresa_id=empresa_id,
                apenas_ativas=not incluir_inativas
            )
            
            print(f"✅ [GET /api/tags] Total: {len(tags)}")
            return jsonify(tags), 200
            
        except Exception as e:
            print(f"❌ Erro ao listar tags: {e}")
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
            
            print(f"\n📝 [POST /api/tags]")
            print(f"   - nome: {data.get('nome')}")
            print(f"   - cor: {data.get('cor', '#3b82f6')}")
            print(f"   - icone: {data.get('icone', 'tag')}")
            
            tag_id = db.adicionar_tag(
                empresa_id=empresa_id,
                dados=data
            )
            
            print(f"✅ Tag criada: ID {tag_id}")
            return jsonify({
                'success': True,
                'message': 'Tag criada com sucesso',
                'id': tag_id
            }), 201
            
        except Exception as e:
            print(f"❌ Erro ao criar tag: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@tags_bp.route('/<int:tag_id>', methods=['GET', 'PUT', 'DELETE'])
@require_permission('operacional_view')
def tag_especifica(tag_id):
    """
    GET: Busca tag específica
    PUT: Atualiza tag
    DELETE: Desativa tag
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    empresa_id = flask_session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    if request.method == 'GET':
        try:
            tag = db.obter_tag(
                empresa_id=empresa_id,
                tag_id=tag_id
            )
            
            if not tag:
                return jsonify({'erro': 'Tag não encontrada'}), 404
            
            return jsonify(tag), 200
            
        except Exception as e:
            print(f"❌ Erro ao buscar tag {tag_id}: {e}")
            return jsonify({'erro': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data.get('nome'):
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            
            print(f"\n📝 [PUT /api/tags/{tag_id}]")
            print(f"   - nome: {data.get('nome')}")
            
            sucesso = db.atualizar_tag(
                empresa_id=empresa_id,
                tag_id=tag_id,
                dados=data
            )
            
            if sucesso:
                print(f"✅ Tag {tag_id} atualizada")
                return jsonify({
                    'success': True,
                    'message': 'Tag atualizada com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Tag não encontrada'
                }), 404
                
        except Exception as e:
            print(f"❌ Erro ao atualizar tag {tag_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # DELETE
        try:
            print(f"\n🗑️ [DELETE /api/tags/{tag_id}]")
            
            sucesso = db.deletar_tag(
                empresa_id=empresa_id,
                tag_id=tag_id
            )
            
            if sucesso:
                print(f"✅ Tag {tag_id} desativada")
                return jsonify({
                    'success': True,
                    'message': 'Tag desativada com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Tag não encontrada'
                }), 404
                
        except Exception as e:
            print(f"❌ Erro ao deletar tag {tag_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

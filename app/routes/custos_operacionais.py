"""
💰 Blueprint de Custos Operacionais
=====================================

Gerencia endpoints relacionados a custos operacionais reutilizáveis.
(Uber, Hotel, Alimentação, Equipamentos, etc)

Autor: Sistema Financeiro DWM
Data: 2026-02-08
"""

from flask import Blueprint, request, jsonify, session as flask_session
from auth_middleware import require_permission
import database_postgresql as db

# Criar blueprint
custos_bp = Blueprint('custos_operacionais', __name__, url_prefix='/api/custos-operacionais')


@custos_bp.route('', methods=['GET', 'POST'])
@require_permission('operacional_view')
def custos():
    """
    GET: Lista todos os custos operacionais
    POST: Cria novo custo
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    if request.method == 'GET':
        try:
            empresa_id = flask_session.get('empresa_id')
            if not empresa_id:
                return jsonify({'erro': 'Empresa não selecionada'}), 403
            
            # Parâmetros opcionais
            incluir_inativos = request.args.get('incluir_inativos', 'false').lower() == 'true'
            categoria = request.args.get('categoria')  # Filtro por categoria
            
            custos = db.listar_custos_operacionais(
                empresa_id=empresa_id,
                apenas_ativos=not incluir_inativos,
                categoria=categoria
            )
            
            print(f"✅ [GET /api/custos-operacionais] Total: {len(custos)}")
            if categoria:
                print(f"   - Filtrado por categoria: {categoria}")
            
            return jsonify(custos), 200
            
        except Exception as e:
            print(f"❌ Erro ao listar custos: {e}")
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
            
            if not data.get('categoria'):
                return jsonify({'success': False, 'error': 'Categoria é obrigatória'}), 400
            
            print(f"\n📝 [POST /api/custos-operacionais]")
            print(f"   - nome: {data.get('nome')}")
            print(f"   - categoria: {data.get('categoria')}")
            print(f"   - valor_padrao: {data.get('valor_padrao', 0)}")
            
            custo_id = db.adicionar_custo_operacional(
                empresa_id=empresa_id,
                dados=data
            )
            
            print(f"✅ Custo criado: ID {custo_id}")
            return jsonify({
                'success': True,
                'message': 'Custo criado com sucesso',
                'id': custo_id
            }), 201
            
        except Exception as e:
            print(f"❌ Erro ao criar custo: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@custos_bp.route('/<int:custo_id>', methods=['GET', 'PUT', 'DELETE'])
@require_permission('operacional_view')
def custo_especifico(custo_id):
    """
    GET: Busca custo específico
    PUT: Atualiza custo
    DELETE: Desativa custo
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    empresa_id = flask_session.get('empresa_id')
    if not empresa_id:
        return jsonify({'erro': 'Empresa não selecionada'}), 403
    
    if request.method == 'GET':
        try:
            custo = db.obter_custo_operacional(
                empresa_id=empresa_id,
                custo_id=custo_id
            )
            
            if not custo:
                return jsonify({'erro': 'Custo não encontrado'}), 404
            
            return jsonify(custo), 200
            
        except Exception as e:
            print(f"❌ Erro ao buscar custo {custo_id}: {e}")
            return jsonify({'erro': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data.get('nome'):
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            
            print(f"\n📝 [PUT /api/custos-operacionais/{custo_id}]")
            print(f"   - nome: {data.get('nome')}")
            
            sucesso = db.atualizar_custo_operacional(
                empresa_id=empresa_id,
                custo_id=custo_id,
                dados=data
            )
            
            if sucesso:
                print(f"✅ Custo {custo_id} atualizado")
                return jsonify({
                    'success': True,
                    'message': 'Custo atualizado com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Custo não encontrado'
                }), 404
                
        except Exception as e:
            print(f"❌ Erro ao atualizar custo {custo_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # DELETE
        try:
            print(f"\n🗑️ [DELETE /api/custos-operacionais/{custo_id}]")
            
            sucesso = db.deletar_custo_operacional(
                empresa_id=empresa_id,
                custo_id=custo_id
            )
            
            if sucesso:
                print(f"✅ Custo {custo_id} desativado")
                return jsonify({
                    'success': True,
                    'message': 'Custo desativado com sucesso'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Custo não encontrado'
                }), 404
                
        except Exception as e:
            print(f"❌ Erro ao deletar custo {custo_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@custos_bp.route('/categorias', methods=['GET'])
@require_permission('operacional_view')
def categorias():
    """
    GET: Lista categorias disponíveis
    
    Returns:
        List[str]: Categorias fixas
    """
    categorias_disponiveis = [
        'Transporte',
        'Hospedagem',
        'Alimentação',
        'Equipamento',
        'Outros'
    ]
    
    return jsonify(categorias_disponiveis), 200

"""
📅 Blueprint de Sessões
=======================

Gerencia endpoints relacionados a sessões de trabalho.
Extraído de web_server.py na Fase 5 da otimização.

Inclui correção P0: Mapeamento correto de campos frontend→backend
(data → data_sessao, quantidade_horas → duracao em minutos)

Autor: Sistema de Otimização - Fase 5
Data: 20/01/2026
"""

from flask import Blueprint, request, jsonify
from auth_middleware import require_permission, filtrar_por_cliente
import database_postgresql as db

# Criar blueprint
sessoes_bp = Blueprint('sessoes', __name__, url_prefix='/api/sessoes')


@sessoes_bp.route('', methods=['GET', 'POST'])
@require_permission('sessoes_view')
def sessoes():
    """Gerenciar sessões - Listar todas ou criar nova"""
    if request.method == 'GET':
        try:
            sessoes = db.listar_sessoes()
            
            # Adicionar cliente_id para cada sessão
            for sessao in sessoes:
                sessao['cliente_id'] = sessao.get('cliente')
            
            # Aplicar filtro por cliente
            sessoes_filtradas = filtrar_por_cliente(sessoes, request.usuario)
            
            return jsonify(sessoes_filtradas)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:  # POST
        print("=" * 80)
        print("🔥 REQUISIÇÃO RECEBIDA: POST /api/sessoes")
        print("=" * 80)
        try:
            data = request.json
            print(f"📦 Dados recebidos completos:")
            print(f"   - cliente_id: {data.get('cliente_id')}")
            print(f"   - contrato_id: {data.get('contrato_id')}")
            print(f"   - data: {data.get('data')}")
            print(f"   - horario: {data.get('horario')}")
            print(f"   - quantidade_horas: {data.get('quantidade_horas')}")
            print(f"   - endereco: {data.get('endereco')}")
            print(f"   - equipe: {len(data.get('equipe', []))} membros")
            print(f"   - responsaveis: {len(data.get('responsaveis', []))} responsáveis")
            print(f"   - equipamentos: {len(data.get('equipamentos', []))} equipamentos")
            
            # 🔧 CORREÇÃO P0: Mapear campos do frontend para o backend
            # Frontend envia: data, horario, quantidade_horas
            # Backend espera: data_sessao, duracao
            
            # Gerar título automático se não fornecido
            titulo = data.get('titulo', '').strip()
            if not titulo:
                from datetime import datetime
                data_sessao_str = data.get('data', '')
                cliente_id = data.get('cliente_id', '')
                # Gerar título mais descritivo
                titulo = f"Sessão - Cliente {cliente_id} - {data_sessao_str}"
                if not data_sessao_str:
                    titulo = f"Sessão - Cliente {cliente_id}"
            
            dados_mapeados = {
                'titulo': titulo,
                'data_sessao': data.get('data'),  # Frontend: 'data' → Backend: 'data_sessao'
                'duracao': int(data.get('quantidade_horas', 0)) * 60 if data.get('quantidade_horas') else None,  # Converter horas → minutos
                'contrato_id': data.get('contrato_id'),
                'cliente_id': data.get('cliente_id'),
                'valor': data.get('valor'),
                'observacoes': data.get('observacoes'),
                'equipe': data.get('equipe', []),
                'responsaveis': data.get('responsaveis', []),
                'equipamentos': data.get('equipamentos', [])
            }
            
            print(f"📡 Dados mapeados para o banco:")
            print(f"   - titulo: {dados_mapeados.get('titulo')}")
            print(f"   - data_sessao: {dados_mapeados.get('data_sessao')}")
            print(f"   - duracao: {dados_mapeados.get('duracao')} minutos")
            print(f"📡 Chamando db.adicionar_sessao...")
            
            sessao_id = db.adicionar_sessao(dados_mapeados)
            print(f"✅ Sessão criada com ID: {sessao_id}")
            return jsonify({'success': True, 'message': 'Sessão criada com sucesso', 'id': sessao_id}), 201
        except Exception as e:
            print(f"❌ ERRO ao criar sessão: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/<int:sessao_id>', methods=['GET', 'PUT', 'DELETE'])
@require_permission('sessoes_view')
def sessao_detalhes(sessao_id):
    """Buscar, atualizar ou excluir sessão específica"""
    if request.method == 'GET':
        try:
            print(f"🔍 Buscando sessão {sessao_id}")
            sessao = db.buscar_sessao(sessao_id)
            if sessao:
                print(f"✅ Sessão {sessao_id} encontrada")
                return jsonify({'success': True, 'data': sessao})
            print(f"❌ Sessão {sessao_id} não encontrada")
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 404
        except Exception as e:
            print(f"❌ Erro ao buscar sessão {sessao_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    elif request.method == 'PUT':
        try:
            data = request.json
            print(f"🔍 Atualizando sessão {sessao_id} com dados: {data}")
            success = db.atualizar_sessao(sessao_id, data)
            if success:
                print(f"✅ Sessão {sessao_id} atualizada")
                return jsonify({'success': True, 'message': 'Sessão atualizada com sucesso'})
            print(f"❌ Sessão {sessao_id} não encontrada")
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 404
        except Exception as e:
            print(f"❌ Erro ao atualizar sessão {sessao_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # DELETE
        try:
            print(f"🔍 Deletando sessão {sessao_id}")
            success = db.deletar_sessao(sessao_id)
            if success:
                print(f"✅ Sessão {sessao_id} deletada")
                return jsonify({'success': True, 'message': 'Sessão excluída com sucesso'})
            print(f"❌ Sessão {sessao_id} não encontrada")
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 404
        except Exception as e:
            print(f"❌ Erro ao deletar sessão {sessao_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

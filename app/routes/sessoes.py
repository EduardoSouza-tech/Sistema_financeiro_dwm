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
    """
    Gerenciar sessões - Listar todas ou criar nova
    
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
            
            import json
            # 🔒 Passar empresa_id explicitamente
            sessoes = db.listar_sessoes(empresa_id=empresa_id)
            
            print(f"\n🔍 [GET /api/sessoes] Total de sessões retornadas: {len(sessoes)}")
            
            # 🔧 Mapear campos do backend para o frontend
            for i, sessao in enumerate(sessoes):
                if i == 0:
                    print(f"\n📊 [SESSÃO 0] Campos disponíveis: {list(sessao.keys())}")
                    print(f"   - data: {sessao.get('data')}")
                    print(f"   - horario: {sessao.get('horario')}")
                    print(f"   - tipo_foto: {sessao.get('tipo_foto')}")
                
                # Mapear data_sessao → data (se data não existir ou for None)
                if not sessao.get('data') and sessao.get('data_sessao'):
                    sessao['data'] = sessao['data_sessao']
                
                # Converter duracao (minutos) → quantidade_horas
                if 'duracao' in sessao and sessao['duracao']:
                    sessao['quantidade_horas'] = sessao['duracao'] / 60
                
                # Extrair dados do dados_json
                if 'dados_json' in sessao and sessao['dados_json']:
                    try:
                        dados_json = json.loads(sessao['dados_json']) if isinstance(sessao['dados_json'], str) else sessao['dados_json']
                        if not sessao.get('horario'):
                            sessao['horario'] = dados_json.get('horario')
                        if 'tipo_foto' not in sessao or sessao.get('tipo_foto') is None:
                            sessao['tipo_foto'] = dados_json.get('tipo_foto', False)
                        if 'tipo_video' not in sessao or sessao.get('tipo_video') is None:
                            sessao['tipo_video'] = dados_json.get('tipo_video', False)
                        if 'tipo_mobile' not in sessao or sessao.get('tipo_mobile') is None:
                            sessao['tipo_mobile'] = dados_json.get('tipo_mobile', False)
                        if not sessao.get('tags'):
                            sessao['tags'] = dados_json.get('tags', '')
                        if not sessao.get('equipe'):
                            sessao['equipe'] = dados_json.get('equipe', [])
                        if not sessao.get('responsaveis'):
                            sessao['responsaveis'] = dados_json.get('responsaveis', [])
                        if not sessao.get('equipamentos'):
                            sessao['equipamentos'] = dados_json.get('equipamentos', [])
                        if not sessao.get('equipamentos_alugados'):
                            sessao['equipamentos_alugados'] = dados_json.get('equipamentos_alugados', [])
                        if not sessao.get('custos_adicionais'):
                            sessao['custos_adicionais'] = dados_json.get('custos_adicionais', [])
                    except Exception as e:
                        print(f"⚠️ Erro ao extrair dados_json: {e}")
                
                # Adicionar contrato_nome se não existir
                if 'contrato_numero' in sessao and not sessao.get('contrato_nome'):
                    sessao['contrato_nome'] = sessao['contrato_numero']
                
                if i == 0:
                    print(f"\n✅ [SESSÃO 0 APÓS MAPEAMENTO]")
                    print(f"   - data: {sessao.get('data')}")
                    print(f"   - horario: {sessao.get('horario')}")
                    print(f"   - tipo_foto: {sessao.get('tipo_foto')}")
                    print(f"   - endereco: {sessao.get('endereco')}")
            
            # Aplicar filtro por cliente
            sessoes_filtradas = filtrar_por_cliente(sessoes, request.usuario)
            
            print(f"✅ [GET /api/sessoes] Retornando {len(sessoes_filtradas)} sessões após filtro\n")
            
            return jsonify(sessoes_filtradas)
        except Exception as e:
            print(f"❌ Erro em GET /api/sessoes: {e}")
            import traceback
            traceback.print_exc()
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
            
            # 🔧 Mapear equipe: Frontend envia IDs, backend espera nomes
            equipe_original = data.get('equipe', [])
            equipe_mapeada = []
            
            print(f"🔍 Estrutura da equipe recebida: {equipe_original}")
            
            # Converter IDs de funcionários em objetos com nome
            if equipe_original:
                for item in equipe_original:
                    if isinstance(item, dict) and 'funcionario_id' in item:
                        # Dict com funcionario_id - buscar nome diretamente no banco
                        funcionario_id = int(item['funcionario_id'])
                        
                        # Query direta para buscar funcionário
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT nome FROM funcionarios WHERE id = %s", (funcionario_id,))
                        funcionario = cursor.fetchone()
                        cursor.close()
                        db.return_to_pool(conn)
                        
                        if funcionario:
                            nome_funcionario = funcionario['nome'] if isinstance(funcionario, dict) else funcionario[0]
                            equipe_mapeada.append({
                                'nome': nome_funcionario,
                                'funcao': item.get('funcao', 'Membro da Equipe'),
                                'pagamento': item.get('pagamento')
                            })
                    elif isinstance(item, dict) and 'nome' in item:
                        # Dict já tem nome - usar diretamente
                        equipe_mapeada.append(item)
                    elif isinstance(item, (int, str)):
                        # Apenas ID - buscar funcionário
                        funcionario_id = int(item)
                        
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT nome FROM funcionarios WHERE id = %s", (funcionario_id,))
                        funcionario = cursor.fetchone()
                        cursor.close()
                        db.return_to_pool(conn)
                        
                        if funcionario:
                            nome_funcionario = funcionario['nome'] if isinstance(funcionario, dict) else funcionario[0]
                            equipe_mapeada.append({
                                'nome': nome_funcionario,
                                'funcao': 'Membro da Equipe'
                            })
            
            # 🔒 VALIDAÇÃO DE SEGURANÇA - Obter empresa_id da sessão
            from flask import session
            empresa_id = session.get('empresa_id')
            if not empresa_id:
                return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
            
            dados_mapeados = {
                'titulo': titulo,
                'data_sessao': data.get('data'),  # Frontend: 'data' → Backend: 'data_sessao'
                'duracao': int(data.get('quantidade_horas', 0)) * 60 if data.get('quantidade_horas') else None,  # Converter horas → minutos
                'contrato_id': data.get('contrato_id'),
                'cliente_id': data.get('cliente_id'),
                'valor': data.get('valor'),
                'observacoes': data.get('observacoes', ''),
                'endereco': data.get('endereco', ''),
                'descricao': data.get('descricao', ''),
                'prazo_entrega': data.get('prazo_entrega'),
                'horario': data.get('horario'),
                'quantidade_horas': data.get('quantidade_horas'),
                'tipo_foto': data.get('tipo_foto', False),
                'tipo_video': data.get('tipo_video', False),
                'tipo_mobile': data.get('tipo_mobile', False),
                'tags': data.get('tags', ''),
                'equipe': equipe_mapeada,
                'responsaveis': data.get('responsaveis', []),
                'equipamentos': data.get('equipamentos', []),
                'equipamentos_alugados': data.get('equipamentos_alugados', []),
                'custos_adicionais': data.get('custos_adicionais', []),
                'empresa_id': empresa_id  # 🔒 Incluir empresa_id
            }
            
            print(f"📡 Dados mapeados para o banco:")
            print(f"   - titulo: {dados_mapeados.get('titulo')}")
            print(f"   - data_sessao: {dados_mapeados.get('data_sessao')}")
            print(f"   - duracao: {dados_mapeados.get('duracao')} minutos")
            print(f"   - equipe mapeada: {equipe_mapeada}")
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
            import json
            print(f"\n🔍 [GET /api/sessoes/{sessao_id}] Buscando sessão...")
            sessao = db.buscar_sessao(sessao_id)
            if sessao:
                print(f"📊 Campos disponíveis: {list(sessao.keys())}")
                print(f"   - data: {sessao.get('data')}")
                print(f"   - horario: {sessao.get('horario')}")
                print(f"   - tipo_foto: {sessao.get('tipo_foto')}")
                print(f"   - tipo_video: {sessao.get('tipo_video')}")
                print(f"   - tipo_mobile: {sessao.get('tipo_mobile')}")
                
                # Garantir dados_json extras
                if 'dados_json' in sessao and sessao['dados_json']:
                    try:
                        dados_json = json.loads(sessao['dados_json']) if isinstance(sessao['dados_json'], str) else sessao['dados_json']
                        if not sessao.get('equipamentos_alugados'):
                            sessao['equipamentos_alugados'] = dados_json.get('equipamentos_alugados', [])
                        if not sessao.get('custos_adicionais'):
                            sessao['custos_adicionais'] = dados_json.get('custos_adicionais', [])
                    except:
                        pass
                
                print(f"✅ Sessão {sessao_id} encontrada e retornada\n")
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

@sessoes_bp.route('/<int:sessao_id>/finalizar', methods=['POST'])
@require_permission('sessoes_edit')
def finalizar_sessao_route(sessao_id):
    """
    Finaliza uma sessão e deduz horas do contrato
    
    Body (JSON):
        {
            "horas_trabalhadas": 8.5  // opcional, usa duracao se não informado
        }
    
    Returns:
        {
            "success": true,
            "message": "Sessão finalizada com sucesso",
            "horas_trabalhadas": 8.5,
            "horas_deduzidas": 8.5,
            "horas_extras": 0,
            "saldo_restante": 71.5,
            "controle_horas_ativo": true
        }
    
    Security:
        🔒 RLS aplicado via empresa_id da sessão
    """
    try:
        # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
        from flask import session
        empresa_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Usuário não identificado'}), 403
        
        data = request.get_json() or {}
        horas_trabalhadas = data.get('horas_trabalhadas')  # Opcional
        
        print(f"\n📊 [POST /api/sessoes/{sessao_id}/finalizar]")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario_id: {usuario_id}")
        print(f"   - horas_trabalhadas: {horas_trabalhadas}")
        
        # Chamar função de finalizar
        resultado = db.finalizar_sessao(
            empresa_id=empresa_id,
            sessao_id=sessao_id,
            usuario_id=usuario_id,
            horas_trabalhadas=horas_trabalhadas
        )
        
        if resultado['success']:
            print(f"✅ Sessão {sessao_id} finalizada com sucesso")
            print(f"   - Horas trabalhadas: {resultado['horas_trabalhadas']}")
            print(f"   - Horas deduzidas: {resultado['horas_deduzidas']}")
            print(f"   - Horas extras: {resultado['horas_extras']}")
            print(f"   - Saldo restante: {resultado['saldo_restante']}")
            return jsonify(resultado), 200
        else:
            print(f"⚠️ Falha ao finalizar sessão: {resultado['message']}")
            return jsonify(resultado), 400
            
    except ValueError as e:
        print(f"❌ Erro de validação ao finalizar sessão {sessao_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Erro ao finalizar sessão {sessao_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/<int:sessao_id>/status', methods=['PUT'])
@require_permission('sessoes_edit')
def atualizar_status_route(sessao_id):
    """
    Atualiza o status de uma sessão
    
    Body (JSON):
        {
            "status": "agendada"  // rascunho, agendada, em_andamento, finalizada, cancelada, reaberta
        }
    
    Returns:
        {
            "success": true,
            "message": "Status alterado: rascunho → agendada",
            "status_anterior": "rascunho",
            "status_novo": "agendada"
        }
    """
    try:
        from flask import session
        empresa_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        data = request.get_json()
        novo_status = data.get('status')
        
        if not novo_status:
            return jsonify({'success': False, 'error': 'Campo "status" é obrigatório'}), 400
        
        print(f"\n📊 [PUT /api/sessoes/{sessao_id}/status]")
        print(f"   - status: {novo_status}")
        
        resultado = db.atualizar_status_sessao(
            empresa_id=empresa_id,
            sessao_id=sessao_id,
            novo_status=novo_status,
            usuario_id=usuario_id
        )
        
        if resultado['success']:
            print(f"✅ Status atualizado: {resultado['status_anterior']} → {resultado['status_novo']}")
            return jsonify(resultado), 200
        else:
            print(f"⚠️ Falha: {resultado['message']}")
            return jsonify(resultado), 400
            
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/<int:sessao_id>/cancelar', methods=['POST'])
@require_permission('sessoes_edit')
def cancelar_sessao_route(sessao_id):
    """
    Cancela uma sessão
    
    Body (JSON):
        {
            "motivo": "Cliente desmarcou"  // opcional
        }
    """
    try:
        from flask import session
        empresa_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'success': False, 'error': 'Autenticação inválida'}), 403
        
        data = request.get_json() or {}
        motivo = data.get('motivo')
        
        print(f"\n📊 [POST /api/sessoes/{sessao_id}/cancelar]")
        print(f"   - motivo: {motivo}")
        
        resultado = db.cancelar_sessao(
            empresa_id=empresa_id,
            sessao_id=sessao_id,
            usuario_id=usuario_id,
            motivo=motivo
        )
        
        if resultado['success']:
            print(f"✅ Sessão cancelada")
            return jsonify(resultado), 200
        else:
            print(f"⚠️ Falha: {resultado.get('message', 'Erro desconhecido')}")
            return jsonify(resultado), 400
            
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Erro ao cancelar sessão: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/<int:sessao_id>/reabrir', methods=['POST'])
@require_permission('sessoes_edit')
def reabrir_sessao_route(sessao_id):
    """
    Reabre uma sessão finalizada ou cancelada
    
    ⚠️ Se sessão foi finalizada, as horas NÃO são devolvidas ao contrato automaticamente.
    """
    try:
        from flask import session
        empresa_id = session.get('empresa_id')
        usuario_id = session.get('usuario_id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'success': False, 'error': 'Autenticação inválida'}), 403
        
        print(f"\n📊 [POST /api/sessoes/{sessao_id}/reabrir]")
        
        resultado = db.reabrir_sessao(
            empresa_id=empresa_id,
            sessao_id=sessao_id,
            usuario_id=usuario_id
        )
        
        if resultado['success']:
            print(f"✅ Sessão reaberta")
            return jsonify(resultado), 200
        else:
            print(f"⚠️ Falha: {resultado.get('message', 'Erro desconhecido')}")
            return jsonify(resultado), 400
            
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Erro ao reabrir sessão: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

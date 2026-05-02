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

from flask import Blueprint, request, jsonify, session
from auth_middleware import require_permission, filtrar_por_cliente, get_usuario_logado
from auth_functions import obter_permissoes_usuario_empresa
import database_postgresql as db

try:
    from app.utils import google_calendar_helper as _gcal
    _GCAL_AVAILABLE = True
except ImportError:
    _GCAL_AVAILABLE = False

import re as _re


def _sincronizar_horas_contrato(contrato_id, empresa_id):
    """Recalcula horas_utilizadas do contrato somando duracao das sessoes nao canceladas."""
    if not contrato_id or not empresa_id:
        return
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(empresa_id=empresa_id) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE contratos
                SET horas_utilizadas = (
                    SELECT COALESCE(SUM(duracao) / 60.0, 0)
                    FROM sessoes
                    WHERE contrato_id = %s AND status != 'cancelada'
                ),
                updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (contrato_id, contrato_id))
        print(f"✅ [SYNC] horas_utilizadas sincronizadas para contrato {contrato_id}")
    except Exception as e:
        print(f"⚠️ [SYNC] Erro ao sincronizar horas do contrato {contrato_id}: {e}")


def _parse_horario_time(horario: str) -> str:
    """Converte campo horario ('9 AS 17', '14H:00') para 'HH:MM'"""
    if not horario:
        return '00:00'
    part = horario.strip().split(' ')[0]
    part = _re.sub(r'[Hh]', '', part)
    if ':' in part:
        h, m = part.split(':', 1)
        return f"{int(h):02d}:{m.zfill(2)}"
    if part.isdigit():
        return f"{int(part):02d}:00"
    return '00:00'


def _sync_sessao_google(sessao_id: int, dados: dict, empresa_id: int, google_event_id: str = None) -> dict:
    """
    Cria ou atualiza evento no Google Calendar para a sessão.
    Retorna dict com 'event_id', 'token_expired' ou 'error'.
    """
    if not _GCAL_AVAILABLE:
        return {'skipped': True}
    try:
        if not _gcal.is_authorized(empresa_id=empresa_id):
            return {'skipped': True}
    except Exception:
        return {'skipped': True}

    # Obter cliente_nome da sessão (se disponível)
    try:
        _emp_id_sync = session.get('empresa_id') if session else None
        sessao = db.buscar_sessao(sessao_id, empresa_id=_emp_id_sync)
        cliente_nome = sessao.get('cliente_nome', 'Cliente') if sessao else 'Cliente'
        # Pegar google_event_id do banco se não foi passado
        if not google_event_id:
            google_event_id = sessao.get('google_event_id') if sessao else None
        equipe = (sessao.get('equipe') or []) if sessao else []
    except Exception:
        cliente_nome = 'Cliente'
        equipe = []

    # Montar attendees (fornecedores + funcionários com e-mail)
    try:
        from notification_service import build_attendees_from_equipe as _build_att
        _emp_for_att = session.get('empresa_id') if session else None
        _eid = _emp_for_att or empresa_id
        todos_attendees = _build_att(equipe, _eid)
    except Exception:
        todos_attendees = []
        _eid = empresa_id

    # Filtrar apenas quem AINDA NÃO recebeu convite (controle rígido no nosso banco)
    try:
        ja_convidados = db.get_emails_ja_convidados_gcal(_eid, sessao_id)
    except Exception:
        ja_convidados = set()
    novos_attendees = [
        a for a in todos_attendees
        if (a.get('email') or '').lower() not in ja_convidados
    ]
    send_upd = 'all' if novos_attendees else 'none'

    # Não sincronizar sessões com data no passado
    from datetime import date as _date
    try:
        sessao_date = _date.fromisoformat(str(dados.get('data', ''))[:10])
        if sessao_date < _date.today():
            print(f"⏭️ [Google Calendar] Sessão {sessao_id} ignorada — data no passado ({sessao_date})")
            return {'skipped': True}
    except (ValueError, TypeError):
        pass  # data inválida → continua

    session_data = {
        'title': f"{cliente_nome} - Sessão",
        'date': str(dados.get('data', ''))[:10],
        'time': _parse_horario_time(dados.get('horario', '')),
        'duration': int(float(dados.get('quantidade_horas', 1)) * 60),
        'description': dados.get('descricao', ''),
        'location': dados.get('endereco', ''),
        'attendees': todos_attendees,  # manter todos no evento GCal
    }

    try:
        if google_event_id:
            result = _gcal.update_calendar_event(
                google_event_id, session_data,
                empresa_id=empresa_id, send_updates=send_upd
            )
        else:
            result = _gcal.create_calendar_event(session_data, empresa_id=empresa_id)

        if result.get('token_expired'):
            print(f"⚠️ [Google Calendar] Token expirado para empresa {empresa_id}")
            return {'token_expired': True}

        if result.get('success') and result.get('event_id'):
            eid_result = result['event_id']
            if not google_event_id:
                db.salvar_google_event_id(sessao_id, eid_result)
            # Registrar convites enviados agora (todos se criação, novos se atualização)
            _to_log = todos_attendees if not google_event_id else novos_attendees
            if _to_log:
                db.registrar_gcal_convites(
                    _eid, sessao_id,
                    [a['email'] for a in _to_log], eid_result
                )
            print(f"✅ [Google Calendar] Evento {'atualizado' if google_event_id else 'criado'}: {eid_result}")
            return {'event_id': eid_result}

        if 'error' in result:
            print(f"⚠️ [Google Calendar] Erro (não crítico): {result['error']}")
            return {'error': result['error']}
    except Exception as e:
        print(f"⚠️ [Google Calendar] Exceção (não crítica): {e}")

    return {}


sessoes_bp = Blueprint('sessoes', __name__, url_prefix='/api/sessoes')


@sessoes_bp.route('', methods=['GET', 'POST'])
def sessoes():
    """
    Gerenciar sessões - Listar todas ou criar nova
    
    Security:
        🔒 Validado empresa_id da sessão e permissões
    """
    # Validar autenticação
    usuario = get_usuario_logado()
    if not usuario:
        print("❌ [SESSÕES] Usuário não autenticado")
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    # Validar empresa
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        print("❌ [SESSÕES] Empresa não selecionada")
        return jsonify({'error': 'Empresa não selecionada'}), 403
    
    # Validar permissões
    if usuario.get('tipo') != 'admin':
        permissoes = obter_permissoes_usuario_empresa(usuario['id'], empresa_id, db)
        print(f"🔒 [SESSÕES] Permissões da empresa {empresa_id}: {permissoes}")
        
        if request.method == 'GET':
            if 'sessoes_view' not in permissoes:
                print("❌ [SESSÕES] Sem permissão sessoes_view")
                return jsonify({'error': 'Sem permissão para visualizar sessões'}), 403
        else:  # POST
            if 'sessoes_edit' not in permissoes and 'sessoes_create' not in permissoes:
                print("❌ [SESSÕES] Sem permissão sessoes_edit/create")
                return jsonify({'error': 'Sem permissão para criar sessões'}), 403
    else:
        print("✅ [SESSÕES] Admin - permissão concedida")
    
    if request.method == 'GET':
        try:
            print(f"📋 [SESSÕES] GET - empresa_id: {empresa_id}, usuario_id: {usuario.get('id')}")
            
            # 🔒 VALIDAÇÃO DE SEGURANÇA OBRIGATÓRIA
            
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
            
            # 🔧 FIX: Adicionar empresa_id ao dict do usuario para o filtro funcionar
            usuario_com_empresa = usuario.copy()
            usuario_com_empresa['empresa_id'] = empresa_id
            
            # Aplicar filtro por cliente
            sessoes_filtradas = filtrar_por_cliente(sessoes, usuario_com_empresa)
            
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
            
            # 🔧 Mapear equipe: Frontend envia {pessoa_id, tipo_pessoa, id_pessoa, funcao, pagamento}
            equipe_original = data.get('equipe', [])
            equipe_mapeada = []

            print(f"🔍 Estrutura da equipe recebida: {equipe_original}")

            # Converter itens da equipe preservando tipo_pessoa e id_pessoa (necessário para e-mails)
            if equipe_original:
                for item in equipe_original:
                    try:
                        if not isinstance(item, dict):
                            # Formato legado: apenas ID numérico (funcionário)
                            func_id = int(item)
                            with db.get_db_connection(empresa_id=empresa_id) as conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT nome FROM funcionarios WHERE id = %s AND empresa_id = %s", (func_id, empresa_id))
                                row = cursor.fetchone()
                                cursor.close()
                            if row:
                                equipe_mapeada.append({'nome': row['nome'] if isinstance(row, dict) else row[0], 'funcao': 'Membro da Equipe', 'tipo_pessoa': 'func', 'id_pessoa': func_id, 'pessoa_id': f'func_{func_id}'})
                            continue

                        tipo_pessoa = item.get('tipo_pessoa')
                        id_pessoa = item.get('id_pessoa')
                        funcao = item.get('funcao', 'Membro da Equipe')
                        pagamento = item.get('pagamento')

                        if tipo_pessoa == 'forn' and id_pessoa:
                            # Fornecedor: buscar nome fantasia/razao_social/nome
                            forn_id = int(id_pessoa)
                            with db.get_db_connection(empresa_id=empresa_id) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT COALESCE(NULLIF(nome_fantasia,''), NULLIF(razao_social,''), nome) AS nome FROM fornecedores WHERE id = %s AND empresa_id = %s",
                                    (forn_id, empresa_id)
                                )
                                row = cursor.fetchone()
                                cursor.close()
                            nome = (row['nome'] if isinstance(row, dict) else row[0]) if row else f'Fornecedor {forn_id}'
                            equipe_mapeada.append({'nome': nome, 'funcao': funcao, 'pagamento': pagamento, 'tipo_pessoa': 'forn', 'id_pessoa': forn_id, 'pessoa_id': f'forn_{forn_id}'})

                        elif tipo_pessoa == 'func' and id_pessoa:
                            # Funcionário: buscar nome
                            func_id = int(id_pessoa)
                            with db.get_db_connection(empresa_id=empresa_id) as conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT nome FROM funcionarios WHERE id = %s AND empresa_id = %s", (func_id, empresa_id))
                                row = cursor.fetchone()
                                cursor.close()
                            nome = (row['nome'] if isinstance(row, dict) else row[0]) if row else f'Funcionário {func_id}'
                            equipe_mapeada.append({'nome': nome, 'funcao': funcao, 'pagamento': pagamento, 'tipo_pessoa': 'func', 'id_pessoa': func_id, 'pessoa_id': f'func_{func_id}'})

                        elif item.get('nome'):
                            # Já tem nome: preservar o item inteiro (compatibilidade com dados antigos)
                            equipe_mapeada.append(item)

                        elif item.get('funcionario_id'):
                            # Formato legado com funcionario_id
                            func_id = int(item['funcionario_id'])
                            with db.get_db_connection(empresa_id=empresa_id) as conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT nome FROM funcionarios WHERE id = %s AND empresa_id = %s", (func_id, empresa_id))
                                row = cursor.fetchone()
                                cursor.close()
                            if row:
                                nome = row['nome'] if isinstance(row, dict) else row[0]
                                equipe_mapeada.append({'nome': nome, 'funcao': funcao, 'pagamento': pagamento, 'tipo_pessoa': 'func', 'id_pessoa': func_id, 'pessoa_id': f'func_{func_id}'})

                    except Exception as e:
                        print(f"⚠️ Erro ao processar item da equipe: {e}")
                        continue
            
            # 🔒 VALIDAÇÃO DE SEGURANÇA - Obter empresa_id da sessão
            # (session já está importado no topo do arquivo)
            empresa_id_post = session.get('empresa_id')
            if not empresa_id_post:
                return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403
            
            dados_mapeados = {
                'titulo': titulo,
                'data': data.get('data'),  # coluna 'data' na tabela sessoes
                'duracao': int(float(data.get('quantidade_horas', 0)) * 60) if data.get('quantidade_horas') else None,  # Converter horas → minutos
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
                'status': data.get('status', 'agendada'),
                'empresa_id': empresa_id_post  # 🔒 Incluir empresa_id
            }
            
            print(f"📡 Dados mapeados para o banco:")
            print(f"   - titulo: {dados_mapeados.get('titulo')}")
            print(f"   - data: {dados_mapeados.get('data')}")
            print(f"   - duracao: {dados_mapeados.get('duracao')} minutos")
            print(f"   - equipe mapeada: {equipe_mapeada}")
            print(f"📡 Chamando db.adicionar_sessao...")
            
            sessao_id = db.adicionar_sessao(dados_mapeados)
            print(f"✅ Sessão criada com ID: {sessao_id}")

            # � Sincronizar horas do contrato (se vinculado)
            _sincronizar_horas_contrato(dados_mapeados.get('contrato_id'), empresa_id_post)

            # �📅 Auto-sincronizar com Google Calendar
            gcal = _sync_sessao_google(sessao_id, dados_mapeados, empresa_id_post)

            response_data = {'success': True, 'message': 'Sessão criada com sucesso', 'id': sessao_id}
            if gcal.get('token_expired'):
                response_data['google_calendar_token_expired'] = True
            elif gcal.get('event_id'):
                response_data['google_event_id'] = gcal['event_id']

            return jsonify(response_data), 201
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
            sessao = db.buscar_sessao(sessao_id, empresa_id=session.get('empresa_id'))
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
            empresa_id_put_rls = session.get('empresa_id')
            success = db.atualizar_sessao(sessao_id, data, empresa_id=empresa_id_put_rls)
            if success:
                print(f"✅ Sessão {sessao_id} atualizada")

                # � Sincronizar horas do contrato (se vinculado)
                contrato_id_put = data.get('contrato_id')
                if contrato_id_put:
                    _sincronizar_horas_contrato(contrato_id_put, session.get('empresa_id'))

                # �📅 Auto-sincronizar com Google Calendar
                empresa_id_put = session.get('empresa_id')
                gcal = _sync_sessao_google(sessao_id, data, empresa_id_put, google_event_id=data.get('google_event_id'))

                response_data = {'success': True, 'message': 'Sessão atualizada com sucesso'}
                if gcal.get('token_expired'):
                    response_data['google_calendar_token_expired'] = True
                elif gcal.get('event_id'):
                    response_data['google_event_id'] = gcal['event_id']

                return jsonify(response_data)
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
            # Buscar contrato_id antes de deletar para sincronizar depois
            empresa_id_del = session.get('empresa_id')
            sessao_atual = db.buscar_sessao(sessao_id, empresa_id=empresa_id_del)
            contrato_id_del = sessao_atual.get('contrato_id') if sessao_atual else None

            success = db.deletar_sessao(sessao_id, empresa_id=empresa_id_del)
            if success:
                print(f"✅ Sessão {sessao_id} deletada")
                # 🔄 Sincronizar horas do contrato
                if contrato_id_del:
                    _sincronizar_horas_contrato(contrato_id_del, empresa_id_del)
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
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Usuário não identificado'}), 403
        
        data = request.get_json() or {}
        horas_trabalhadas = data.get('horas_trabalhadas')  # Opcional
        numero_nf = data.get('numero_nf') or None  # Opcional
        
        print(f"\n📊 [POST /api/sessoes/{sessao_id}/finalizar]")
        print(f"   - Usuario: {usuario.get('username')}")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario_id: {usuario_id}")
        print(f"   - horas_trabalhadas: {horas_trabalhadas}")
        print(f"   - numero_nf: {numero_nf}")
        
        # Chamar função de finalizar
        resultado = db.finalizar_sessao(
            empresa_id=empresa_id,
            sessao_id=sessao_id,
            usuario_id=usuario_id,
            horas_trabalhadas=horas_trabalhadas,
            numero_nf=numero_nf
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
            "status": "agendada"  // rascunho, agendada, em_andamento, finalizada, concluida, cancelada, reaberta
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
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id:
            return jsonify({'success': False, 'error': 'Empresa não selecionada'}), 403
        
        data = request.get_json()
        novo_status = data.get('status')
        force = data.get('force', False)  # kanban envia force=True para mover livremente
        
        if not novo_status:
            return jsonify({'success': False, 'error': 'Campo "status" é obrigatório'}), 400
        
        print(f"\n📊 [PUT /api/sessoes/{sessao_id}/status]")
        print(f"   - Usuario: {usuario.get('username')}")
        print(f"   - status: {novo_status}")
        
        resultado = db.atualizar_status_sessao(
            empresa_id=empresa_id,
            sessao_id=sessao_id,
            novo_status=novo_status,
            usuario_id=usuario_id,
            force=force
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
        
        # 🔒 Obter dados do usuário logado
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'success': False, 'error': 'Autenticação inválida'}), 403
        
        data = request.get_json() or {}
        motivo = data.get('motivo')
        
        print(f"\n📊 [POST /api/sessoes/{sessao_id}/cancelar]")
        print(f"   - Usuario: {usuario.get('username')}")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario_id: {usuario_id}")
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
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'success': False, 'error': 'Autenticação inválida'}), 403
        
        print(f"\n📊 [POST /api/sessoes/{sessao_id}/reabrir]")
        print(f"   - Usuario: {usuario.get('username')}")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario_id: {usuario_id}")
        
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


# ============================================================================
# 📊 DASHBOARD E RELATÓRIOS (PARTE 9)
# ============================================================================

@sessoes_bp.route('/dashboard', methods=['GET'])
@require_permission('sessoes_view')
def dashboard_sessoes():
    """
    Dashboard completo de sessões com estatísticas e alertas
    
    Returns:
        {
            "estatisticas": {...},
            "top_clientes": [...],
            "sessoes_atencao": [...],
            "periodo_atual": {...}
        }
    
    Security:
        🔒 Filtrado por empresa_id da sessão
    """
    try:
        from flask import session
        from datetime import date, timedelta
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        print(f"\n📊 [GET /api/sessoes/dashboard] Empresa: {empresa_id}")
        
        # 1. Estatísticas gerais (view)
        estatisticas = db.execute_query("""
            SELECT 
                total_geral, total_pendentes, total_confirmadas, total_em_andamento,
                total_concluidas, total_entregues, total_canceladas,
                valor_total_ativo, ticket_medio, total_horas, media_horas,
                prazo_medio_dias, captadas_diretas, captadas_indicacao
            FROM vw_sessoes_estatisticas
            WHERE empresa_id = %s
        """, (empresa_id,), fetch_all=True, empresa_id=empresa_id)
        
        # 2. Top 10 clientes (view)
        top_clientes = db.execute_query("""
            SELECT 
                cliente_id, cliente_nome, total_sessoes, valor_total,
                ultima_sessao, taxa_conclusao_pct
            FROM vw_top_clientes_sessoes
            WHERE empresa_id = %s
            ORDER BY valor_total DESC
            LIMIT 10
        """, (empresa_id,), fetch_all=True, empresa_id=empresa_id)
        
        # 3. Sessões com atenção (view)
        sessoes_atencao = db.execute_query("""
            SELECT 
                id, cliente_nome, data, prazo_entrega, valor_total,
                dias_ate_prazo, urgencia, status
            FROM vw_sessoes_atencao
            WHERE empresa_id = %s
              AND urgencia IN ('ATRASADO', 'URGENTE - HOJE', 'URGENTE - 3 DIAS')
            ORDER BY prazo_entrega ASC
            LIMIT 20
        """, (empresa_id,), fetch_all=True, empresa_id=empresa_id)
        
        # 4. Estatísticas do período atual (últimos 30 dias) - função SQL
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()
        
        periodo_atual = db.execute_query("""
            SELECT * FROM obter_estatisticas_periodo(%s, %s, %s)
        """, (empresa_id, data_inicio, data_fim), fetch_all=True, empresa_id=empresa_id)
        
        print(f"✅ Dashboard gerado: {len(top_clientes)} clientes, {len(sessoes_atencao)} alertas")
        
        return jsonify({
            'success': True,
            'estatisticas': estatisticas[0] if estatisticas else {},
            'top_clientes': top_clientes,
            'sessoes_atencao': sessoes_atencao,
            'periodo_atual': periodo_atual[0] if periodo_atual else {}
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao gerar dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/estatisticas', methods=['GET'])
@require_permission('sessoes_view')
def estatisticas_periodo():
    """
    Estatísticas de sessões para um período customizado
    
    Query Parameters:
        - data_inicio (YYYY-MM-DD): Data inicial
        - data_fim (YYYY-MM-DD): Data final
    
    Security:
        🔒 Filtrado por empresa_id da sessão
    """
    try:
        from flask import session
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        
        if not data_inicio_str or not data_fim_str:
            return jsonify({'erro': 'Parâmetros data_inicio e data_fim são obrigatórios'}), 400
        
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        
        print(f"\n📊 [GET /api/sessoes/estatisticas] Empresa: {empresa_id}, Período: {data_inicio} a {data_fim}")
        
        # Usar função SQL para obter estatísticas
        resultado = db.execute_query("""
            SELECT * FROM obter_estatisticas_periodo(%s, %s, %s)
        """, (empresa_id, data_inicio, data_fim), fetch_all=True, empresa_id=empresa_id)
        
        if resultado:
            stats = resultado[0]
            print(f"✅ Estatísticas: {stats.get('total_sessoes', 0)} sessões, R$ {stats.get('faturamento_total', 0):.2f}")
            
            return jsonify({
                'success': True,
                'periodo': {'inicio': data_inicio_str, 'fim': data_fim_str},
                'estatisticas': stats
            }), 200
        else:
            return jsonify({
                'success': True,
                'periodo': {'inicio': data_inicio_str, 'fim': data_fim_str},
                'estatisticas': {}
            }), 200
        
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    except Exception as e:
        print(f"❌ Erro ao gerar estatísticas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/comparativo', methods=['GET'])
@require_permission('sessoes_view')
def comparativo_periodos():
    """
    Comparativo entre dois períodos com variação percentual
    
    Query Parameters:
        - p1_inicio, p1_fim: Período 1
        - p2_inicio, p2_fim: Período 2
    
    Example:
        /api/sessoes/comparativo?p1_inicio=2025-12-01&p1_fim=2025-12-31&p2_inicio=2026-01-01&p2_fim=2026-01-31
    
    Security:
        🔒 Filtrado por empresa_id da sessão
    """
    try:
        from flask import session
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        # Validar parâmetros
        parametros = ['p1_inicio', 'p1_fim', 'p2_inicio', 'p2_fim']
        valores = {}
        
        for param in parametros:
            valor = request.args.get(param)
            if not valor:
                return jsonify({'erro': f'Parâmetro {param} é obrigatório'}), 400
            
            try:
                valores[param] = datetime.strptime(valor, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'erro': f'Formato inválido para {param}. Use YYYY-MM-DD'}), 400
        
        print(f"\n📊 [GET /api/sessoes/comparativo] Empresa: {empresa_id}")
        print(f"   Período 1: {valores['p1_inicio']} a {valores['p1_fim']}")
        print(f"   Período 2: {valores['p2_inicio']} a {valores['p2_fim']}")
        
        # Usar função SQL para comparativo
        resultado = db.execute_query("""
            SELECT * FROM comparativo_periodos(%s, %s, %s, %s, %s)
        """, (empresa_id, valores['p1_inicio'], valores['p1_fim'], 
              valores['p2_inicio'], valores['p2_fim']), fetch_all=True, empresa_id=empresa_id)
        
        print(f"✅ Comparativo gerado: {len(resultado)} métricas")
        
        return jsonify({
            'success': True,
            'periodo1': {'inicio': str(valores['p1_inicio']), 'fim': str(valores['p1_fim'])},
            'periodo2': {'inicio': str(valores['p2_inicio']), 'fim': str(valores['p2_fim'])},
            'comparativo': resultado
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao gerar comparativo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/periodo', methods=['GET'])
@require_permission('sessoes_view')
def sessoes_por_periodo():
    """
    Sessões agregadas por período (mês/semana/dia)
    
    Query Parameters:
        - data_inicio (YYYY-MM-DD): Data inicial
        - data_fim (YYYY-MM-DD): Data final
        - agregacao (month|week|day): Tipo de agregação (padrão: month)
    
    Security:
        🔒 Filtrado por empresa_id da sessão
    """
    try:
        from flask import session
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        agregacao = request.args.get('agregacao', 'month')
        
        if not data_inicio_str or not data_fim_str:
            return jsonify({'erro': 'Parâmetros data_inicio e data_fim são obrigatórios'}), 400
        
        if agregacao not in ['month', 'week', 'day']:
            return jsonify({'erro': 'agregacao deve ser month, week ou day'}), 400
        
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        
        print(f"\n📊 [GET /api/sessoes/periodo] Empresa: {empresa_id}, Agregação: {agregacao}")
        
        # Usar view de período
        campo_periodo = {
            'month': 'mes',
            'week': 'semana',
            'day': 'dia'
        }[agregacao]
        
        resultado = db.execute_query(f"""
            SELECT 
                {campo_periodo} as periodo,
                total_sessoes,
                concluidas,
                canceladas,
                faturamento_bruto,
                faturamento_entregue,
                total_comissoes,
                lucro_liquido,
                media_ticket,
                total_horas
            FROM vw_sessoes_por_periodo
            WHERE empresa_id = %s
              AND {campo_periodo} BETWEEN %s AND %s
            ORDER BY {campo_periodo} ASC
        """, (empresa_id, data_inicio, data_fim), fetch_all=True, empresa_id=empresa_id)
        
        print(f"✅ Retornados {len(resultado)} períodos")
        
        return jsonify({
            'success': True,
            'agregacao': agregacao,
            'data': resultado
        }), 200
        
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    except Exception as e:
        print(f"❌ Erro ao buscar período: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 💰 INTEGRAÇÃO COM CONTAS A RECEBER (PARTE 10)
# ============================================================================

@sessoes_bp.route('/<int:sessao_id>/gerar-lancamento', methods=['POST'])
@require_permission('sessoes_edit')
def gerar_lancamento_sessao(sessao_id):
    """
    Gera manualmente um lançamento de receita para uma sessão
    
    Path Parameters:
        - sessao_id: ID da sessão
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        from flask import session
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'erro': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'erro': 'Autenticação inválida'}), 403
        
        print(f"\n💰 [POST /api/sessoes/{sessao_id}/gerar-lancamento]")
        print(f"   - Usuario: {usuario.get('username')}")
        
        # Verificar se sessão pertence à empresa
        sessao = db.buscar_sessao(sessao_id, empresa_id=empresa_id)
        if not sessao:
            return jsonify({'erro': 'Sessão não encontrada'}), 404
        
        if sessao.get('empresa_id') != empresa_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        # Verificar se já tem lançamento
        if sessao.get('lancamento_id'):
            return jsonify({
                'success': False,
                'message': 'Sessão já possui lançamento vinculado',
                'lancamento_id': sessao['lancamento_id']
            }), 400
        
        # Chamar função SQL para gerar lançamento
        resultado = db.execute_query("""
            SELECT gerar_lancamento_sessao(%s, %s) as lancamento_id
        """, (sessao_id, usuario_id), fetch_one=True, empresa_id=empresa_id)
        
        if resultado and resultado.get('lancamento_id'):
            lancamento_id = resultado['lancamento_id']
            print(f"✅ Lançamento {lancamento_id} gerado para sessão {sessao_id}")
            
            return jsonify({
                'success': True,
                'message': 'Lançamento gerado com sucesso',
                'lancamento_id': lancamento_id
            }), 200
        else:
            raise Exception('Falha ao gerar lançamento')
        
    except Exception as e:
        print(f"❌ Erro ao gerar lançamento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/<int:sessao_id>/estornar-lancamento', methods=['POST'])
@require_permission('sessoes_edit')
def estornar_lancamento_sessao(sessao_id):
    """
    Estorna/cancela o lançamento vinculado a uma sessão
    
    Path Parameters:
        - sessao_id: ID da sessão
    
    Body Parameters (JSON):
        - deletar (bool): Se TRUE, deleta o lançamento; se FALSE, apenas cancela
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        from flask import session
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'erro': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'erro': 'Autenticação inválida'}), 403
        
        dados = request.get_json() or {}
        deletar = dados.get('deletar', False)
        
        print(f"\n💰 [POST /api/sessoes/{sessao_id}/estornar-lancamento] Deletar: {deletar}")
        
        # Verificar se sessão pertence à empresa
        sessao = db.buscar_sessao(sessao_id, empresa_id=empresa_id)
        if not sessao:
            return jsonify({'erro': 'Sessão não encontrada'}), 404
        
        if sessao.get('empresa_id') != empresa_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        # Verificar se tem lançamento
        if not sessao.get('lancamento_id'):
            return jsonify({
                'success': False,
                'message': 'Sessão não possui lançamento vinculado'
            }), 400
        
        # Chamar função SQL para estornar
        resultado = db.execute_query("""
            SELECT estornar_lancamento_sessao(%s, %s) as sucesso
        """, (sessao_id, deletar), fetch_one=True, empresa_id=empresa_id)
        
        if resultado and resultado.get('sucesso'):
            acao = 'deletado' if deletar else 'cancelado'
            print(f"✅ Lançamento {acao} para sessão {sessao_id}")
            
            return jsonify({
                'success': True,
                'message': f'Lançamento {acao} com sucesso'
            }), 200
        else:
            raise Exception('Falha ao estornar lançamento')
        
    except Exception as e:
        print(f"❌ Erro ao estornar lançamento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/integracao', methods=['GET'])
@require_permission('sessoes_view')
def visualizar_integracao():
    """
    Visualiza o relacionamento entre sessões e lançamentos
    
    Query Parameters:
        - situacao (str): Filtro por situação (SEM LANÇAMENTO, PAGO, A RECEBER, etc.)
    
    Security:
        🔒 Filtrado por empresa_id da sessão
    """
    try:
        from flask import session
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        situacao = request.args.get('situacao')
        
        print(f"\n💰 [GET /api/sessoes/integracao] Empresa: {empresa_id}, Situação: {situacao}")
        
        # Buscar dados da view
        query = """
            SELECT 
                sessao_id, sessao_titulo, data, cliente_id, cliente_nome,
                sessao_valor, sessao_status, prazo_entrega, gerar_lancamento_automatico,
                lancamento_id, lancamento_tipo, lancamento_descricao, lancamento_valor,
                lancamento_vencimento, lancamento_pagamento, lancamento_status,
                lancamento_categoria, situacao,
                sessao_criada_em, sessao_atualizada_em, lancamento_criado_em
            FROM vw_sessoes_lancamentos
            WHERE empresa_id = %s
        """
        
        params = [empresa_id]
        
        if situacao:
            query += " AND situacao = %s"
            params.append(situacao)
        
        query += " ORDER BY data DESC LIMIT 100"
        
        resultado = db.execute_query(query, tuple(params), fetch_all=True, empresa_id=empresa_id)
        
        print(f"✅ Retornados {len(resultado)} registros")
        
        return jsonify({
            'success': True,
            'data': resultado
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao visualizar integração: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/analise-financeira', methods=['GET'])
@require_permission('sessoes_view')
def analise_financeira_integracao():
    """
    Análise financeira da integração sessões → contas a receber
    
    Returns:
        - Total de sessões
        - Sessões com/sem lançamento
        - Valores recebidos/a receber
        - Taxas de lançamento e recebimento
    
    Security:
        🔒 Filtrado por empresa_id da sessão
    """
    try:
        from flask import session
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'erro': 'Empresa não selecionada'}), 403
        
        print(f"\n💰 [GET /api/sessoes/analise-financeira] Empresa: {empresa_id}")
        
        # Buscar análise da view
        resultado = db.execute_query("""
            SELECT 
                total_sessoes, sessoes_entregues, sessoes_com_lancamento,
                sessoes_sem_lancamento, valor_total_entregue, valor_ja_recebido,
                valor_a_receber, valor_nao_lancado, taxa_lancamento_pct,
                taxa_recebimento_pct
            FROM vw_sessoes_financeiro
            WHERE empresa_id = %s
        """, (empresa_id,), fetch_one=True, empresa_id=empresa_id)
        
        if not resultado:
            # Se não há dados, retornar zeros
            resultado = {
                'total_sessoes': 0,
                'sessoes_entregues': 0,
                'sessoes_com_lancamento': 0,
                'sessoes_sem_lancamento': 0,
                'valor_total_entregue': 0,
                'valor_ja_recebido': 0,
                'valor_a_receber': 0,
                'valor_nao_lancado': 0,
                'taxa_lancamento_pct': 0,
                'taxa_recebimento_pct': 0
            }
        
        print(f"✅ Análise: {resultado.get('total_sessoes', 0)} sessões, "
              f"{resultado.get('taxa_lancamento_pct', 0)}% com lançamento")
        
        return jsonify({
            'success': True,
            'analise': resultado
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao gerar análise financeira: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@sessoes_bp.route('/<int:sessao_id>/configurar-lancamento-automatico', methods=['PATCH'])
@require_permission('sessoes_edit')
def configurar_lancamento_automatico(sessao_id):
    """
    Ativa/desativa geração automática de lançamento para uma sessão
    
    Path Parameters:
        - sessao_id: ID da sessão
    
    Body Parameters (JSON):
        - ativar (bool): TRUE para ativar, FALSE para desativar
    
    Security:
        🔒 Validado empresa_id da sessão
    """
    try:
        from flask import session
        
        # Obter usuario_id corretamente via get_usuario_logado()
        usuario = get_usuario_logado()
        if not usuario:
            return jsonify({'erro': 'Usuário não autenticado'}), 401
        
        empresa_id = session.get('empresa_id')
        usuario_id = usuario.get('id')
        
        if not empresa_id or not usuario_id:
            return jsonify({'erro': 'Autenticação inválida'}), 403
        
        dados = request.get_json() or {}
        ativar = dados.get('ativar', True)
        
        print(f"\n💰 [PATCH /api/sessoes/{sessao_id}/configurar-lancamento-automatico] Ativar: {ativar}")
        print(f"   - Usuario: {usuario.get('username')}")
        print(f"   - empresa_id: {empresa_id}")
        print(f"   - usuario_id: {usuario_id}")
        print(f"   - Usuario: {usuario.get('username')}")
        
        # Verificar se sessão pertence à empresa
        sessao = db.buscar_sessao(sessao_id, empresa_id=empresa_id)
        if not sessao:
            return jsonify({'erro': 'Sessão não encontrada'}), 404
        
        if sessao.get('empresa_id') != empresa_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        # Atualizar configuração
        db.execute_query("""
            UPDATE sessoes
            SET gerar_lancamento_automatico = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
        """, (ativar, sessao_id, empresa_id), fetch_all=False, empresa_id=empresa_id)
        
        status = 'ativada' if ativar else 'desativada'
        print(f"✅ Geração automática {status} para sessão {sessao_id}")
        
        return jsonify({
            'success': True,
            'message': f'Geração automática {status} com sucesso',
            'ativado': ativar
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao configurar geração automática: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# EXPORTAÇÕES
# ============================================================================

@sessoes_bp.route('/exportar/pdf', methods=['GET'])
@require_permission('sessoes_view')
def exportar_sessoes_pdf():
    """Exporta sessões para PDF"""
    try:
        from flask import send_file, session
        import database_postgresql as db
        from pdf_export import gerar_sessoes_pdf
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Buscar dados da empresa
        empresa = db.obter_empresa(empresa_id)
        nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'
        
        # Buscar sessões
        sessoes = db.listar_sessoes(empresa_id=empresa_id)
        
        # Gerar PDF
        buffer = gerar_sessoes_pdf(sessoes, nome_empresa)
        
        filename = f"sessoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
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


@sessoes_bp.route('/exportar/excel', methods=['GET'])
@require_permission('sessoes_view')
def exportar_sessoes_excel():
    """Exporta sessões para Excel"""
    try:
        from flask import send_file, session
        import database_postgresql as db
        from pdf_export import gerar_sessoes_excel
        from datetime import datetime
        
        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403
        
        # Buscar dados da empresa
        empresa = db.obter_empresa(empresa_id)
        nome_empresa = empresa.get('razao_social', 'Empresa') if empresa else 'Empresa'
        
        # Buscar sessões
        sessoes = db.listar_sessoes(empresa_id=empresa_id)
        
        # Gerar Excel
        buffer = gerar_sessoes_excel(sessoes, nome_empresa)
        
        filename = f"sessoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
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
# RELATÓRIO DE EQUIPE
# ============================================================================

@sessoes_bp.route('/relatorio-equipe', methods=['GET'])
@require_permission('sessoes_view')
def relatorio_equipe_sessoes():
    """
    Relatório de produção e pagamento da equipe em um período.

    Query params:
        data_inicio  – YYYY-MM-DD  (obrigatório)
        data_fim     – YYYY-MM-DD  (obrigatório)

    Retorna por membro:
        - nome, funcao, tipo (func/forn)
        - total_sessoes       – número de sessões em que participou
        - valor_total_pagar   – soma de pagamento combinado
        - sessoes             – lista de sessões com data, cliente, valor, status,
                                 data_pagamento_cliente, data_pagamento_equipe (+1 dia)
        - status_pagamento    – 'pago' | 'aguardando' | 'pendente' (conforme lançamentos)
    """
    try:
        import json
        from datetime import datetime, timedelta
        from database_postgresql import get_db_connection

        empresa_id = session.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não selecionada'}), 403

        data_inicio = request.args.get('data_inicio')
        data_fim    = request.args.get('data_fim')

        if not data_inicio or not data_fim:
            return jsonify({'error': 'Parâmetros data_inicio e data_fim são obrigatórios'}), 400

        # Validar datas
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            dt_fim    = datetime.strptime(data_fim,    '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

        if dt_inicio > dt_fim:
            return jsonify({'error': 'data_inicio deve ser anterior a data_fim'}), 400

        with get_db_connection(empresa_id=empresa_id) as conn:
            cur = conn.cursor()

            # 1. Buscar sessões no período com dados do cliente e lançamento associado
            cur.execute("""
                SELECT
                    s.id,
                    s.data,
                    s.dados_json,
                    s.valor,
                    s.status,
                    c.nome AS cliente_nome,
                    -- lançamento de receita associado (via campo associacao = 'sessao_<id>')
                    l.data_vencimento  AS lc_vencimento,
                    l.data_pagamento   AS lc_data_pago,
                    l.status           AS lc_status
                FROM sessoes s
                LEFT JOIN clientes c  ON c.id = s.cliente_id
                LEFT JOIN lancamentos l
                       ON l.empresa_id = s.empresa_id
                      AND l.tipo       = 'receita'
                      AND l.associacao = CONCAT('sessao_', s.id::text)
                WHERE s.empresa_id = %s
                  AND s.data BETWEEN %s AND %s
                ORDER BY s.data
            """, (empresa_id, dt_inicio, dt_fim))
            sessoes_rows = cur.fetchall()

            # 2. Cache de nomes: funcionários e fornecedores por id
            cur.execute("SELECT id, nome FROM funcionarios WHERE empresa_id = %s", (empresa_id,))
            func_map = {r['id']: r['nome'] for r in cur.fetchall()}

            cur.execute("""
                SELECT id,
                       COALESCE(NULLIF(nome_fantasia,''), NULLIF(razao_social,''), nome) AS nome
                FROM fornecedores WHERE empresa_id = %s
            """, (empresa_id,))
            forn_map = {r['id']: r['nome'] for r in cur.fetchall()}

        # 3. Agregar por membro
        membros: dict = {}  # chave: pessoa_id único

        def _resolve_nome(item, func_map, forn_map):
            tipo = item.get('tipo_pessoa') or ('forn' if str(item.get('pessoa_id', '')).startswith('forn_') else 'func')
            pid  = item.get('id_pessoa') or item.get('funcionario_id')
            nome = item.get('nome', '')

            if tipo == 'forn' and pid and pid in forn_map:
                return forn_map[pid], tipo
            if tipo == 'func' and pid and pid in func_map:
                return func_map[pid], tipo
            return nome or f'ID {pid}', tipo

        for row in sessoes_rows:
            sessao_id = row['id']
            dados_json = row['dados_json'] or {}
            if isinstance(dados_json, str):
                try:
                    dados_json = json.loads(dados_json)
                except Exception:
                    dados_json = {}

            data_sessao       = row['data'].isoformat() if row['data'] else None
            cliente_nome      = row['cliente_nome'] or '-'
            valor_sessao      = float(row['valor']) if row['valor'] else 0.0
            status_sessao     = row['status'] or 'rascunho'

            # Data de pagamento do cliente: usa lançamento se disponível, senão data da sessão
            if row['lc_vencimento']:
                data_pgto_cliente = row['lc_vencimento'].isoformat()
            else:
                data_pgto_cliente = data_sessao  # fallback

            # Data de pagamento da equipe = +1 dia após o cliente pagar
            if data_pgto_cliente:
                try:
                    dt_pgto_c = datetime.strptime(data_pgto_cliente, '%Y-%m-%d').date()
                    data_pgto_equipe = (dt_pgto_c + timedelta(days=1)).isoformat()
                except Exception:
                    data_pgto_equipe = None
            else:
                data_pgto_equipe = None

            # Status do lançamento (pago / pendente / aguardando)
            lc_status = row['lc_status']
            if lc_status in ('pago', 'recebido'):
                status_pgto_cliente = 'pago'
            elif row['lc_vencimento'] and datetime.now().date() > row['lc_vencimento']:
                status_pgto_cliente = 'vencido'
            else:
                status_pgto_cliente = 'pendente'

            sessao_info = {
                'sessao_id':             sessao_id,
                'data':                  data_sessao,
                'cliente':               cliente_nome,
                'valor_sessao':          valor_sessao,
                'status_sessao':         status_sessao,
                'data_pagamento_cliente': data_pgto_cliente,
                'data_pagamento_equipe':  data_pgto_equipe,
                'status_pagamento_cliente': status_pgto_cliente,
            }

            equipe = dados_json.get('equipe', [])
            responsaveis = dados_json.get('responsaveis', [])

            # Processar membros da equipe (têm pagamento combinado)
            for item in equipe:
                if not isinstance(item, dict):
                    continue
                nome, tipo = _resolve_nome(item, func_map, forn_map)
                funcao    = item.get('funcao', '')
                pagamento = 0.0
                try:
                    pagamento = float(item.get('pagamento') or 0)
                except (TypeError, ValueError):
                    pagamento = 0.0

                pessoa_id = item.get('pessoa_id') or f"{tipo}_{item.get('id_pessoa') or item.get('funcionario_id') or nome}"
                chave = f"{pessoa_id}_{funcao}"

                if chave not in membros:
                    membros[chave] = {
                        'pessoa_id':           pessoa_id,
                        'nome':                nome,
                        'funcao':              funcao,
                        'tipo':                tipo,
                        'papel':               'equipe',
                        'total_sessoes':       0,
                        'valor_total_pagar':   0.0,
                        'sessoes':             [],
                    }
                membros[chave]['total_sessoes']     += 1
                membros[chave]['valor_total_pagar'] += pagamento
                membros[chave]['sessoes'].append({
                    **sessao_info,
                    'valor_pagar': pagamento,
                })

            # Processar responsáveis (sem pagamento combinado)
            for item in responsaveis:
                if not isinstance(item, dict):
                    continue
                nome, tipo = _resolve_nome(item, func_map, forn_map)
                funcao = item.get('funcao', '')

                pessoa_id = item.get('pessoa_id') or f"{tipo}_{item.get('id_pessoa') or item.get('funcionario_id') or nome}"
                chave = f"resp_{pessoa_id}_{funcao}"

                if chave not in membros:
                    membros[chave] = {
                        'pessoa_id':           pessoa_id,
                        'nome':                nome,
                        'funcao':              funcao,
                        'tipo':                tipo,
                        'papel':               'responsavel',
                        'total_sessoes':       0,
                        'valor_total_pagar':   0.0,
                        'sessoes':             [],
                    }
                membros[chave]['total_sessoes'] += 1
                membros[chave]['sessoes'].append({
                    **sessao_info,
                    'valor_pagar': 0.0,
                })

        resultado = sorted(membros.values(), key=lambda x: (-x['valor_total_pagar'], x['nome']))

        return jsonify({
            'success':       True,
            'data_inicio':   data_inicio,
            'data_fim':      data_fim,
            'total_sessoes': len(sessoes_rows),
            'membros':       resultado,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


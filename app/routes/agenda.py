"""
===============================================
ROTAS DE AGENDA E NOTIFICAÇÕES
===============================================
Gerenciamento de configurações de e-mail e Google Calendar
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session
import json
import os
import sys

# Adicionar pasta pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar helper do Google Calendar
try:
    from app.utils import google_calendar_helper
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    print("⚠️ Google Calendar helper não disponível. Instale as dependências:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

agenda_bp = Blueprint('agenda', __name__, url_prefix='/api')

# Arquivo para armazenar configurações (fallback local / dev)
CONFIG_FILE = 'config/email_settings.json'

_CONFIG_TABLE_ENSURED = False

def ensure_config_dir():
    """Garantir que o diretório de configuração existe"""
    os.makedirs('config', exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers de persistência no PostgreSQL
# ---------------------------------------------------------------------------

def _ensure_config_table(cur):
    """Cria a tabela config_sistema se ainda não existir (idempotente)."""
    global _CONFIG_TABLE_ENSURED
    if _CONFIG_TABLE_ENSURED:
        return
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config_sistema (
            chave TEXT PRIMARY KEY,
            valor TEXT,
            atualizado_em TIMESTAMP DEFAULT NOW()
        )
    """)
    _CONFIG_TABLE_ENSURED = True

def _load_from_db():
    """
    Carrega as configurações de e-mail/agenda salvas no PostgreSQL.
    Retorna dict vazio em caso de erro (não interrompe startup).
    """
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_config_table(cur)
            cur.execute(
                "SELECT valor FROM config_sistema WHERE chave = 'agenda_email_settings'"
            )
            row = cur.fetchone()
            if row and row['valor']:
                return json.loads(row['valor'])
    except Exception as e:
        print(f"⚠️ Não foi possível carregar config do banco: {e}")
    return {}

def _save_to_db(settings):
    """
    Persiste as configurações no PostgreSQL (sobrevive a redeploys no Railway).
    """
    try:
        from database_postgresql import get_db_connection
        value = json.dumps(settings, ensure_ascii=False)
        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            _ensure_config_table(cur)
            cur.execute("""
                INSERT INTO config_sistema (chave, valor, atualizado_em)
                VALUES ('agenda_email_settings', %s, NOW())
                ON CONFLICT (chave) DO UPDATE
                    SET valor = EXCLUDED.valor, atualizado_em = NOW()
            """, (value,))
    except Exception as e:
        print(f"⚠️ Não foi possível salvar config no banco: {e}")
        raise

# ---------------------------------------------------------------------------

def load_email_settings():
    """
    Carregar configurações de e-mail.
    Prioridade: env vars (Railway) > PostgreSQL > config/email_settings.json > defaults
    """
    # 1. Tentar arquivo local (fallback / dev local)
    file_settings = {}
    try:
        ensure_config_dir()
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_settings = json.load(f)
    except Exception:
        pass

    # 2. DB sobrescreve o arquivo (persiste no Railway após redeploys)
    db_settings = _load_from_db()
    if db_settings:
        file_settings.update(db_settings)

    smtp_host     = os.getenv('SMTP_HOST')      or file_settings.get('smtp_host', '')
    smtp_port     = int(os.getenv('SMTP_PORT', 0)) or file_settings.get('smtp_port', 587)
    smtp_user     = os.getenv('SMTP_USER')      or file_settings.get('smtp_user', '')
    smtp_password = os.getenv('SMTP_PASSWORD')  or file_settings.get('smtp_password', '')
    smtp_from     = os.getenv('SMTP_FROM_EMAIL') or file_settings.get('smtp_from_email', smtp_user)
    smtp_name     = os.getenv('SMTP_FROM_NAME')  or file_settings.get('smtp_from_name', 'Sistema Financeiro DWM')
    smtp_enabled  = bool(smtp_host and smtp_user and smtp_password)
    if os.getenv('EMAIL_NOTIFICATIONS_ENABLED', '').lower() == 'false':
        smtp_enabled = False

    return {
        'notification_emails': file_settings.get('notification_emails', []),
        'google_calendar_enabled': file_settings.get('google_calendar_enabled', False),
        'google_calendar_id': file_settings.get('google_calendar_id'),
        'google_credentials': file_settings.get('google_credentials'),
        'smtp_enabled': smtp_enabled,
        'smtp_host': smtp_host,
        'smtp_port': smtp_port,
        'smtp_user': smtp_user,
        'smtp_password': smtp_password,
        'smtp_from_email': smtp_from,
        'smtp_from_name': smtp_name,
    }

def save_email_settings(settings):
    """
    Salvar configurações.
    Primário: PostgreSQL (persiste no Railway) — inclui smtp_password.
    Secundário: arquivo local (dev/fallback) — exclui smtp_password.
    """
    # Salvar TUDO no banco, incluindo senha (dados do próprio usuário, tráfego HTTPS)
    _save_to_db(settings)

    # No arquivo local, excluir a senha (compatibilidade / segurança de disco)
    safe_file = {k: v for k, v in settings.items() if k not in ('smtp_password',)}
    try:
        ensure_config_dir()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(safe_file, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Não foi possível salvar {CONFIG_FILE}: {e}")

@agenda_bp.route('/email-settings', methods=['GET'])
def get_email_settings():
    """Obter configurações de e-mail"""
    try:
        settings = load_email_settings()
        safe_settings = {
            'notification_emails': settings.get('notification_emails', []),
            'google_calendar_enabled': settings.get('google_calendar_enabled', False),
            'google_calendar_id': settings.get('google_calendar_id'),
            'smtp_enabled': settings.get('smtp_enabled', False),
            'smtp_host': settings.get('smtp_host', ''),
            'smtp_port': settings.get('smtp_port', 587),
            'smtp_user': settings.get('smtp_user', ''),
            'smtp_from_email': settings.get('smtp_from_email', ''),
            'smtp_from_name': settings.get('smtp_from_name', ''),
            # Indica se está configurado via variável de ambiente (Railway)
            'smtp_via_env': bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_USER') and os.getenv('SMTP_PASSWORD')),
        }
        return jsonify(safe_settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/email-settings', methods=['POST'])
def update_email_settings():
    """Atualizar configurações de e-mail"""
    try:
        data = request.json
        
        # Carregar configurações existentes
        settings = load_email_settings()
        
        # Atualizar
        settings['notification_emails'] = data.get('notification_emails', [])
        settings['google_calendar_enabled'] = data.get('google_calendar_enabled', False)
        settings['google_calendar_id'] = data.get('google_calendar_id')
        
        # Salvar
        save_email_settings(settings)
        
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/authorize', methods=['GET'])
def google_calendar_authorize():
    """Iniciar fluxo OAuth2 do Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500
        
        # Gerar URL de autorização
        authorization_url, state = google_calendar_helper.get_authorization_url()
        
        # CORREÇÃO: Salvar state com timestamp para validação de expiração
        import time
        session['google_oauth_state'] = state
        session['google_oauth_state_timestamp'] = time.time()
        
        # Redirecionar para autorização do Google
        return redirect(authorization_url)
    except Exception as e:
        print(f"❌ Erro ao autorizar: {e}")
        return redirect(url_for('index') + '?message=google_auth_error')

@agenda_bp.route('/google-calendar/callback', methods=['GET'])
def google_calendar_callback():
    """Callback do OAuth2 do Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return redirect(url_for('index') + '?message=google_auth_error')
        
        # Obter código de autorização
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        # Verificar se houve erro
        if error:
            print(f"❌ Erro na autorização: {error}")
            return redirect(url_for('index') + f'?message=google_auth_failed&error={error}')
        
        if not code:
            return redirect(url_for('index') + '?message=google_auth_failed&error=no_code')
        
        # Validar state — logar divergência mas não bloquear se sessão foi perdida
        saved_state = session.get('google_oauth_state')
        state_timestamp = session.get('google_oauth_state_timestamp', 0)

        if saved_state and state != saved_state:
            print(f"❌ State inválido: {state} != {saved_state}")
            return redirect(url_for('index') + '?message=google_auth_failed&error=invalid_state')

        if saved_state is None:
            print(f"⚠️ [OAuth] google_oauth_state ausente da sessão — sessão pode ter sido perdida, continuando")

        import time
        if saved_state and time.time() - state_timestamp > 600:  # 10 minutos
            print(f"❌ State expirado: {time.time() - state_timestamp}s")
            session.pop('google_oauth_state', None)
            session.pop('google_oauth_state_timestamp', None)
            return redirect(url_for('index') + '?message=google_auth_failed&error=state_expired')
        
        # Limpar state da sessão após uso
        session.pop('google_oauth_state', None)
        session.pop('google_oauth_state_timestamp', None)
        
        # Trocar código por tokens
        empresa_id_oauth = session.get('empresa_id', 1)
        creds_data = google_calendar_helper.exchange_code_for_tokens(code, state, empresa_id=empresa_id_oauth)
        
        if 'error' in creds_data:
            return redirect(url_for('index') + f'?message=google_auth_failed&error={creds_data["error"]}')
        
        # Atualizar configurações para marcar como habilitado
        settings = load_email_settings()
        settings['google_calendar_enabled'] = True
        save_email_settings(settings)
        
        # Limpar state da sessão
        session.pop('google_oauth_state', None)
        
        return redirect(url_for('index') + '?message=google_auth_success')
    
    except Exception as e:
        print(f"❌ Erro no callback: {e}")
        return redirect(url_for('index') + f'?message=google_auth_error&error={str(e)}')

def _parse_horario_time(horario: str) -> str:
    """
    Parse horario field to HH:MM string.
    Handles formats: '9 AS 17', '14H:00', '14H AS 17H', '9:00', '14:00', '09:00'
    Returns: zero-padded HH:MM string, e.g. '09:00', '14:00'
    """
    import re
    if not horario:
        return '00:00'
    # Take the first token (before first space)
    part = horario.strip().split(' ')[0]
    # Remove any 'H' or 'h' characters (e.g. '14H:00' -> '14:00', '14H' -> '14')
    part = re.sub(r'[Hh]', '', part)
    # If it has a colon, split into hour/minute and zero-pad
    if ':' in part:
        h, m = part.split(':', 1)
        return f"{int(h):02d}:{m.zfill(2)}"
    # Otherwise it's just an hour number
    if part.isdigit():
        return f"{int(part):02d}:00"
    return '00:00'


@agenda_bp.route('/google-calendar/sync', methods=['POST'])
def google_calendar_sync():
    """Sincronizar sessões com Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500
        
        # Verificar se está autorizado
        empresa_id = session.get('empresa_id', 1)
        if not google_calendar_helper.is_authorized(empresa_id):
            return jsonify({'error': 'Não autorizado. Configure Google Calendar primeiro.'}), 401
        
        settings = load_email_settings()
        if not settings.get('google_calendar_enabled'):
            return jsonify({'error': 'Google Calendar não habilitado'}), 400
        
        # Obter sessões do banco
        try:
            import database_postgresql as db
            sessoes = db.listar_sessoes(empresa_id=empresa_id)
        except Exception as e:
            print(f"❌ Erro ao buscar sessões: {e}")
            return jsonify({'error': 'Erro ao buscar sessões do banco'}), 500
        
        events_created = 0
        events_updated = 0
        errors = []
        token_expired = False
        
        # Sincronizar cada sessão com Google Calendar
        for sessao in sessoes:
            # Pular sessões canceladas
            if sessao.get('status') == 'cancelada':
                continue
            
            try:
                session_data = {
                    'title': f"{sessao.get('cliente_nome', 'Cliente')} - Sessão",
                    'date': str(sessao.get('data', ''))[:10],
                    'time': _parse_horario_time(sessao.get('horario', '')),
                    'duration': int(float(sessao.get('quantidade_horas', 1)) * 60),
                    'description': sessao.get('descricao', ''),
                    'location': sessao.get('endereco', '')
                }
                
                # Verificar se já existe evento no Google (através de google_event_id salvo)
                google_event_id = sessao.get('google_event_id')
                
                if google_event_id:
                    # Atualizar evento existente
                    result = google_calendar_helper.update_calendar_event(google_event_id, session_data, empresa_id=empresa_id)
                    if 'error' not in result:
                        events_updated += 1
                    else:
                        if result.get('token_expired'):
                            token_expired = True
                        errors.append(f"Sessão {sessao.get('id')}: {result['error']}")
                else:
                    # Criar novo evento
                    result = google_calendar_helper.create_calendar_event(session_data, empresa_id=empresa_id)
                    if 'error' not in result:
                        events_created += 1
                        # Salvar google_event_id no banco
                        if result.get('event_id'):
                            import database_postgresql as _db
                            _db.salvar_google_event_id(sessao.get('id'), result['event_id'], empresa_id=empresa_id)
                    else:
                        if result.get('token_expired'):
                            token_expired = True
                        errors.append(f"Sessão {sessao.get('id')}: {result['error']}")
            except Exception as e:
                errors.append(f"Sessão {sessao.get('id')}: {str(e)}")
        
        return jsonify({
            'success': True, 
            'message': f'Sincronização concluída: {events_created} criados, {events_updated} atualizados',
            'events_created': events_created,
            'events_updated': events_updated,
            'errors': errors[:5] if errors else [],
            'google_oauth_expired': token_expired
        })
    except Exception as e:
        print(f"❌ Erro ao sincronizar: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/event/create', methods=['POST'])
def create_google_calendar_event():
    """Criar evento individual no Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500
        
        empresa_id = session.get('empresa_id', 1)
        if not google_calendar_helper.is_authorized(empresa_id):
            return jsonify({'error': 'Não autorizado'}), 401
        
        session_data = request.json
        result = google_calendar_helper.create_calendar_event(session_data, empresa_id=empresa_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Erro ao criar evento: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/event/<event_id>', methods=['PUT'])
def update_google_calendar_event(event_id):
    """Atualizar evento no Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500
        
        empresa_id = session.get('empresa_id', 1)
        if not google_calendar_helper.is_authorized(empresa_id):
            return jsonify({'error': 'Não autorizado'}), 401
        
        session_data = request.json
        result = google_calendar_helper.update_calendar_event(event_id, session_data, empresa_id=empresa_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Erro ao atualizar evento: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/event/<event_id>', methods=['DELETE'])
def delete_google_calendar_event(event_id):
    """Deletar evento do Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500
        
        empresa_id = session.get('empresa_id', 1)
        if not google_calendar_helper.is_authorized(empresa_id):
            return jsonify({'error': 'Não autorizado'}), 401
        
        result = google_calendar_helper.delete_calendar_event(event_id, empresa_id=empresa_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Erro ao deletar evento: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/dedup', methods=['POST'])
def google_calendar_dedup():
    """Remove eventos duplicados do Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500

        empresa_id = session.get('empresa_id', 1)
        if not google_calendar_helper.is_authorized(empresa_id):
            return jsonify({'error': 'Não autorizado'}), 401

        result = google_calendar_helper.deduplicate_events(empresa_id=empresa_id)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)
    except Exception as e:
        print(f"❌ Erro ao deduplicar: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/status', methods=['GET'])
def google_calendar_status():
    """Verificar status da autorização do Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'authorized': False, 'available': False})

        empresa_id = session.get('empresa_id', 1)
        is_auth = google_calendar_helper.is_authorized(empresa_id)
        settings = load_email_settings()

        # Diagnóstico: verificar se credenciais existem na tabela (sem descriptografar)
        creds_exist_db = False
        creds_exist_file = False
        try:
            import database_postgresql as _db
            with _db.get_db_connection(empresa_id=empresa_id) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT empresa_id, updated_at FROM google_calendar_credentials WHERE empresa_id = %s",
                    (empresa_id,)
                )
                row = cur.fetchone()
                cur.close()
            creds_exist_db = row is not None
        except Exception as e:
            print(f"⚠️ [Status] Erro ao checar DB: {e}")

        import os as _os
        creds_exist_file = _os.path.exists(google_calendar_helper.CREDENTIALS_FILE)

        return jsonify({
            'authorized': is_auth,
            'available': True,
            'enabled': settings.get('google_calendar_enabled', False),
            'empresa_id': empresa_id,
            'creds_in_db': creds_exist_db,
            'creds_in_file': creds_exist_file,
        })
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/notifications/send-reminders', methods=['POST'])
def send_session_reminders():
    """
    Envia lembretes de sessões próximas com deduplicação (não reenvía o mesmo item no mesmo dia).
    Retorna resumo do que foi enviado/pulado.
    """
    import notification_service

    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403

    data = request.json or {}
    days_ahead = int(data.get('days_ahead', 3))
    force = bool(data.get('force', True))  # manual sempre força o envio

    try:
        result = notification_service.send_upcoming_session_reminders(empresa_id, days_ahead=days_ahead, force=force)
        sent    = result.get('sent', 0)
        skipped = result.get('skipped', 0)
        error   = result.get('error', 0)
        total   = result.get('total_upcoming', 0)

        if error > 0:
            return jsonify({
                'success': False,
                'message': result.get('error_msg', 'Erro ao enviar lembretes'),
                'result': result,
            })

        if sent == 0 and total == 0:
            return jsonify({
                'success': True,
                'message': result.get('error_msg', f'Nenhuma sessão nos próximos {days_ahead} dias.'),
                'result': result,
            })

        if sent == 0 and skipped > 0:
            return jsonify({
                'success': True,
                'message': f'Lembretes já enviados hoje para todas as {skipped} sessão(ões) próximas. Nenhum reenvio necessário.',
                'result': result,
            })

        return jsonify({
            'success': True,
            'message': (
                f'✅ {sent} lembrete(s) enviado(s)!'
                + (f' ({skipped} já haviam sido notificados hoje e foram pulados)' if skipped else '')
            ),
            'result': result,
        })
    except Exception as e:
        print(f"❌ Erro ao enviar lembretes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@agenda_bp.route('/notifications/log', methods=['GET'])
def notifications_log():
    """Retorna o histórico de notificações da empresa."""
    import notification_service

    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return jsonify({'success': False, 'error': 'Empresa não identificada'}), 403

    limit = int(request.args.get('limit', 50))
    try:
        logs = notification_service.get_notifications_log(empresa_id, limit=limit)
        return jsonify({'success': True, 'logs': logs, 'total': len(logs)})
    except Exception as e:
        print(f"❌ Erro ao buscar log: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agenda_bp.route('/notifications/test', methods=['POST'])
def test_notifications():
    """Testar envio de notificações (endpoint manual)"""
    import io
    import contextlib
    import notification_service

    empresa_id = session.get('empresa_id', 1)

    # Capturar prints do serviço para incluir no retorno
    log_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(log_buffer):
            notification_service.send_notification_batch(empresa_id)
        log_output = log_buffer.getvalue()
        print(log_output, end='')  # também mostrar no log do servidor

        # Se nenhuma linha de sucesso no log, determinar causa
        if '✅ E-mail enviado' in log_output:
            return jsonify({
                'success': True,
                'message': 'E-mail enviado com sucesso! Verifique sua caixa de entrada.',
                'log': log_output
            })
        elif '❌ Erro ao enviar via Resend' in log_output or '❌ Erro ao enviar e-mail' in log_output:
            # Extrair linha de erro para mensagem mais precisa
            erro_linha = next((l for l in log_output.splitlines() if '❌ Erro ao enviar' in l), '')
            return jsonify({
                'success': False,
                'message': f'Erro ao enviar via Resend. Detalhes: {erro_linha}',
                'log': log_output
            })
        elif '⚠️ SMTP não configurado' in log_output:
            return jsonify({
                'success': False,
                'message': 'SMTP não configurado. Preencha host, usuário e senha SMTP nas configurações.',
                'log': log_output
            })
        elif '⚠️ Nenhum e-mail configurado' in log_output:
            return jsonify({
                'success': False,
                'message': 'Nenhum e-mail destinatário configurado. Adicione e-mails na aba Notificações.',
                'log': log_output
            })
        else:
            # Sem sessões/contratos para notificar — testar envio direto
            settings = load_email_settings()
            recipients = settings.get('notification_emails', [])
            if not recipients:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum e-mail destinatário configurado. Adicione e-mails na aba Notificações.',
                    'log': log_output
                })
            # Verificar se há algum provedor configurado (Resend ou SMTP)
            import os as _os
            resend_ok = bool(_os.getenv('RESEND_API_KEY'))
            smtp_ok = bool(settings.get('smtp_enabled') and settings.get('smtp_host'))
            if not resend_ok and not smtp_ok:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum provedor de e-mail configurado (RESEND_API_KEY ou SMTP).',
                    'log': log_output
                })
            # Enviar e-mail de teste direto (sem dados de agenda, só para confirmar envio)
            log_buffer2 = io.StringIO()
            with contextlib.redirect_stdout(log_buffer2):
                sent = notification_service.send_email_notification(
                    recipients,
                    '✅ Teste de Notificação — Sistema Financeiro DWM',
                    '<p>Este é um e-mail de teste enviado pelo Sistema Financeiro DWM.</p>'
                    '<p>Se você recebeu este e-mail, as notificações estão configuradas corretamente!</p>',
                    'Teste de notificação — Sistema Financeiro DWM.'
                )
            log_output2 = log_buffer2.getvalue()
            print(log_output2, end='')
            combined_log = log_output + log_output2
            if sent:
                return jsonify({
                    'success': True,
                    'message': f'E-mail de teste enviado para {len(recipients)} destinatário(s)! Verifique sua caixa de entrada.',
                    'log': combined_log
                })
            else:
                erro_linha = next((l for l in log_output2.splitlines() if '❌' in l), '')
                return jsonify({
                    'success': False,
                    'message': f'Falha ao enviar e-mail. {erro_linha}',
                    'log': combined_log
                })
    except Exception as e:
        print(f"❌ Erro ao testar notificações: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agenda_bp.route('/notifications/settings', methods=['GET', 'POST'])
def notification_settings():
    """Gerenciar configurações de notificações (SMTP)"""
    if request.method == 'GET':
        try:
            settings = load_email_settings()
            # Não expor senha
            safe_settings = {
                'smtp_enabled': settings.get('smtp_enabled', False),
                'smtp_host': settings.get('smtp_host', ''),
                'smtp_port': settings.get('smtp_port', 587),
                'smtp_user': settings.get('smtp_user', ''),
                'smtp_from_email': settings.get('smtp_from_email', ''),
                'smtp_from_name': settings.get('smtp_from_name', 'Sistema Financeiro DWM'),
                'notification_emails': settings.get('notification_emails', [])
            }
            return jsonify(safe_settings)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:  # POST
        try:
            data = request.json
            settings = load_email_settings()
            
            # Atualizar configurações SMTP
            settings['smtp_enabled'] = data.get('smtp_enabled', False)
            settings['smtp_host'] = data.get('smtp_host', '')
            settings['smtp_port'] = data.get('smtp_port', 587)
            settings['smtp_user'] = data.get('smtp_user', '')
            settings['smtp_from_email'] = data.get('smtp_from_email', '')
            settings['smtp_from_name'] = data.get('smtp_from_name', 'Sistema Financeiro DWM')
            
            # Atualizar senha somente se fornecida
            if data.get('smtp_password'):
                settings['smtp_password'] = data.get('smtp_password')
            
            save_email_settings(settings)
            
            return jsonify({
                'success': True,
                'message': 'Configurações de notificações salvas'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@agenda_bp.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """Verificar status do scheduler de notificações"""
    try:
        import notification_scheduler
        
        status = notification_scheduler.get_scheduler_status()
        return jsonify(status)
    except Exception as e:
        print(f"❌ Erro ao verificar scheduler: {e}")
        return jsonify({'error': str(e), 'running': False}), 500

@agenda_bp.route('/scheduler/start', methods=['POST'])
def scheduler_start():
    """Iniciar scheduler de notificações"""
    try:
        import notification_scheduler
        
        success = notification_scheduler.start_scheduler()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Scheduler iniciado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Scheduler já está rodando'
            })
    except Exception as e:
        print(f"❌ Erro ao iniciar scheduler: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/scheduler/stop', methods=['POST'])
def scheduler_stop():
    """Parar scheduler de notificações"""
    try:
        import notification_scheduler
        
        success = notification_scheduler.stop_scheduler()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Scheduler parado'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Scheduler não está rodando'
            })
    except Exception as e:
        print(f"❌ Erro ao parar scheduler: {e}")
        return jsonify({'error': str(e)}), 500
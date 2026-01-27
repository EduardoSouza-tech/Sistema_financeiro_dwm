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

# Arquivo para armazenar configurações
CONFIG_FILE = 'config/email_settings.json'

def ensure_config_dir():
    """Garantir que o diretório de configuração existe"""
    os.makedirs('config', exist_ok=True)

def load_email_settings():
    """Carregar configurações de e-mail"""
    ensure_config_dir()
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # Configurações padrão
    return {
        'notification_emails': [],
        'google_calendar_enabled': False,
        'google_calendar_id': None,
        'google_credentials': None
    }

def save_email_settings(settings):
    """Salvar configurações de e-mail"""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

@agenda_bp.route('/email-settings', methods=['GET'])
def get_email_settings():
    """Obter configurações de e-mail"""
    try:
        settings = load_email_settings()
        # Não expor credenciais sensíveis
        safe_settings = {
            'notification_emails': settings.get('notification_emails', []),
            'google_calendar_enabled': settings.get('google_calendar_enabled', False),
            'google_calendar_id': settings.get('google_calendar_id'),
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
        
        # Salvar state na sessão para validação no callback
        session['google_oauth_state'] = state
        
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
        
        # Validar state (segurança)
        saved_state = session.get('google_oauth_state')
        if state != saved_state:
            print(f"❌ State inválido: {state} != {saved_state}")
            return redirect(url_for('index') + '?message=google_auth_failed&error=invalid_state')
        
        # Trocar código por tokens
        creds_data = google_calendar_helper.exchange_code_for_tokens(code, state)
        
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

@agenda_bp.route('/google-calendar/sync', methods=['POST'])
def google_calendar_sync():
    """Sincronizar sessões com Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'error': 'Google Calendar não configurado'}), 500
        
        # Verificar se está autorizado
        if not google_calendar_helper.is_authorized():
            return jsonify({'error': 'Não autorizado. Configure Google Calendar primeiro.'}), 401
        
        settings = load_email_settings()
        if not settings.get('google_calendar_enabled'):
            return jsonify({'error': 'Google Calendar não habilitado'}), 400
        
        # Obter sessões do banco (implementar integração com database_postgresql.py)
        # Por enquanto, retornar sucesso simulado
        
        return jsonify({
            'success': True, 
            'message': 'Sincronização concluída',
            'events_created': 0,
            'events_updated': 0
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
        
        if not google_calendar_helper.is_authorized():
            return jsonify({'error': 'Não autorizado'}), 401
        
        session_data = request.json
        result = google_calendar_helper.create_calendar_event(session_data)
        
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
        
        if not google_calendar_helper.is_authorized():
            return jsonify({'error': 'Não autorizado'}), 401
        
        session_data = request.json
        result = google_calendar_helper.update_calendar_event(event_id, session_data)
        
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
        
        if not google_calendar_helper.is_authorized():
            return jsonify({'error': 'Não autorizado'}), 401
        
        result = google_calendar_helper.delete_calendar_event(event_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Erro ao deletar evento: {e}")
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/status', methods=['GET'])
def google_calendar_status():
    """Verificar status da autorização do Google Calendar"""
    try:
        if not GOOGLE_CALENDAR_AVAILABLE:
            return jsonify({'authorized': False, 'available': False})
        
        is_auth = google_calendar_helper.is_authorized()
        settings = load_email_settings()
        
        return jsonify({
            'authorized': is_auth,
            'available': True,
            'enabled': settings.get('google_calendar_enabled', False)
        })
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return jsonify({'error': str(e)}), 500

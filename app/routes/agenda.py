"""
===============================================
ROTAS DE AGENDA E NOTIFICAÇÕES
===============================================
Gerenciamento de configurações de e-mail e Google Calendar
"""

from flask import Blueprint, request, jsonify, redirect, url_for
import json
import os

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
        # TODO: Implementar OAuth2 completo do Google
        # Por enquanto, redirecionar de volta com mensagem
        return redirect(url_for('index') + '?message=google_auth_pending')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/callback', methods=['GET'])
def google_calendar_callback():
    """Callback do OAuth2 do Google Calendar"""
    try:
        # TODO: Processar código de autorização e obter tokens
        code = request.args.get('code')
        
        if code:
            # Aqui você processaria o código e salvaria os tokens
            return redirect(url_for('index') + '?message=google_auth_success')
        else:
            return redirect(url_for('index') + '?message=google_auth_failed')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/google-calendar/sync', methods=['POST'])
def google_calendar_sync():
    """Sincronizar sessões com Google Calendar"""
    try:
        settings = load_email_settings()
        
        if not settings.get('google_calendar_enabled'):
            return jsonify({'error': 'Google Calendar não habilitado'}), 400
        
        # TODO: Implementar sincronização real com Google Calendar API
        # Por enquanto, retornar sucesso simulado
        
        return jsonify({
            'success': True, 
            'message': 'Sincronização iniciada',
            'note': 'Implementação completa do Google Calendar API em desenvolvimento'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

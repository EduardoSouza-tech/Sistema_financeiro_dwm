"""
Google Calendar Helper
Funções para integração com Google Calendar API
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

# Arquivo para armazenar credenciais
CREDENTIALS_FILE = 'config/google_credentials.json'

def ensure_config_dir():
    """Garantir que o diretório de configuração existe"""
    os.makedirs('config', exist_ok=True)

def get_authorization_url():
    """
    Gerar URL de autorização do Google OAuth 2.0
    Returns: tuple (authorization_url, state)
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=config.GOOGLE_SCOPES,
        redirect_uri=config.GOOGLE_REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Força nova autorização para garantir refresh_token
    )
    
    return authorization_url, state

def exchange_code_for_tokens(code, state=None):
    """
    Trocar código de autorização por tokens de acesso
    Args:
        code: Código de autorização retornado pelo Google
        state: Estado da sessão (opcional)
    Returns: dict com tokens
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=config.GOOGLE_SCOPES,
        redirect_uri=config.GOOGLE_REDIRECT_URI
    )
    
    if state:
        flow.state = state
    
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    
    # Salvar credenciais
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }
    
    ensure_config_dir()
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(creds_data, f, indent=2)
    
    return creds_data

def get_credentials():
    """
    Obter credenciais salvas e renovar se necessário
    Returns: Credentials object ou None
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    
    try:
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
        
        credentials = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )
        
        # Verificar se o token expirou e renovar
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            # Salvar novo token
            creds_data['token'] = credentials.token
            creds_data['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
            with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(creds_data, f, indent=2)
        
        return credentials
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
        return None

def get_calendar_service():
    """
    Obter serviço do Google Calendar
    Returns: Resource object ou None
    """
    credentials = get_credentials()
    if not credentials:
        return None
    
    try:
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Erro ao criar serviço do Calendar: {e}")
        return None

def create_calendar_event(session_data):
    """
    Criar evento no Google Calendar
    Args:
        session_data: dict com dados da sessão
            {
                'title': 'Nome da sessão',
                'date': '2026-01-27',
                'time': '14:00',
                'duration': 240,  # minutos
                'description': 'Descrição',
                'location': 'Endereço'
            }
    Returns: dict com event_id ou None
    """
    service = get_calendar_service()
    if not service:
        return {'error': 'Não autorizado. Configure Google Calendar primeiro.'}
    
    try:
        # Construir data/hora de início e fim
        start_datetime_str = f"{session_data['date']}T{session_data.get('time', '00:00')}:00"
        start_datetime = datetime.fromisoformat(start_datetime_str)
        
        duration = session_data.get('duration', 60)  # minutos
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        event = {
            'summary': session_data.get('title', 'Sessão de Fotografia'),
            'location': session_data.get('location', ''),
            'description': session_data.get('description', ''),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 dia antes
                    {'method': 'popup', 'minutes': 60},        # 1 hora antes
                ],
            },
        }
        
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        
        return {
            'success': True,
            'event_id': event_result['id'],
            'event_link': event_result.get('htmlLink')
        }
    
    except HttpError as error:
        print(f"❌ Erro HTTP ao criar evento: {error}")
        return {'error': f'Erro ao criar evento: {error}'}
    except Exception as e:
        print(f"❌ Erro ao criar evento: {e}")
        return {'error': str(e)}

def update_calendar_event(event_id, session_data):
    """
    Atualizar evento existente no Google Calendar
    Args:
        event_id: ID do evento no Google Calendar
        session_data: dict com dados atualizados da sessão
    Returns: dict com sucesso ou erro
    """
    service = get_calendar_service()
    if not service:
        return {'error': 'Não autorizado'}
    
    try:
        # Buscar evento atual
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Atualizar campos
        if 'title' in session_data:
            event['summary'] = session_data['title']
        
        if 'location' in session_data:
            event['location'] = session_data['location']
        
        if 'description' in session_data:
            event['description'] = session_data['description']
        
        if 'date' in session_data and 'time' in session_data:
            start_datetime_str = f"{session_data['date']}T{session_data['time']}:00"
            start_datetime = datetime.fromisoformat(start_datetime_str)
            
            duration = session_data.get('duration', 60)
            end_datetime = start_datetime + timedelta(minutes=duration)
            
            event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            }
            event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            }
        
        updated_event = service.events().update(
            calendarId='primary', 
            eventId=event_id, 
            body=event
        ).execute()
        
        return {
            'success': True,
            'event_id': updated_event['id'],
            'event_link': updated_event.get('htmlLink')
        }
    
    except HttpError as error:
        print(f"❌ Erro HTTP ao atualizar evento: {error}")
        return {'error': f'Erro ao atualizar evento: {error}'}
    except Exception as e:
        print(f"❌ Erro ao atualizar evento: {e}")
        return {'error': str(e)}

def delete_calendar_event(event_id):
    """
    Deletar evento do Google Calendar
    Args:
        event_id: ID do evento
    Returns: dict com sucesso ou erro
    """
    service = get_calendar_service()
    if not service:
        return {'error': 'Não autorizado'}
    
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {'success': True, 'message': 'Evento removido com sucesso'}
    
    except HttpError as error:
        print(f"❌ Erro HTTP ao deletar evento: {error}")
        return {'error': f'Erro ao deletar evento: {error}'}
    except Exception as e:
        print(f"❌ Erro ao deletar evento: {e}")
        return {'error': str(e)}

def list_calendar_events(start_date=None, end_date=None, max_results=100):
    """
    Listar eventos do Google Calendar
    Args:
        start_date: Data de início (formato: YYYY-MM-DD)
        end_date: Data de fim (formato: YYYY-MM-DD)
        max_results: Número máximo de resultados
    Returns: list de eventos ou dict com erro
    """
    service = get_calendar_service()
    if not service:
        return {'error': 'Não autorizado'}
    
    try:
        # Se não forneceu datas, usar período padrão (próximos 30 dias)
        if not start_date:
            start_date = datetime.now().isoformat() + 'Z'
        else:
            start_date = f"{start_date}T00:00:00Z"
        
        if end_date:
            end_date = f"{end_date}T23:59:59Z"
        
        params = {
            'calendarId': 'primary',
            'timeMin': start_date,
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        if end_date:
            params['timeMax'] = end_date
        
        events_result = service.events().list(**params).execute()
        events = events_result.get('items', [])
        
        return {
            'success': True,
            'events': events,
            'count': len(events)
        }
    
    except HttpError as error:
        print(f"❌ Erro HTTP ao listar eventos: {error}")
        return {'error': f'Erro ao listar eventos: {error}'}
    except Exception as e:
        print(f"❌ Erro ao listar eventos: {e}")
        return {'error': str(e)}

def is_authorized():
    """
    Verificar se o usuário está autorizado
    Returns: bool
    """
    return get_credentials() is not None

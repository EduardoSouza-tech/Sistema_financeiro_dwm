"""
Google Calendar Helper
Funções para integração com Google Calendar API

Persistência de credenciais OAuth:
  - Railway (produção): PostgreSQL (tabela google_calendar_credentials)
  - Desenvolvimento local: config/google_credentials.json (fallback)
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

# Arquivo local (usado apenas em desenvolvimento, ignorado no Railway)
CREDENTIALS_FILE = 'config/google_credentials.json'

# Permite que a resposta OAuth do Google contenha escopos adicionais
# (openid, userinfo.email, userinfo.profile) sem que requests-oauthlib
# lance MismatchingStateError / ScopeChanged.
os.environ.setdefault('OAUTHLIB_RELAX_TOKEN_SCOPE', '1')

# ---------------------------------------------------------------
# Helpers de persistência: DB primeiro, arquivo como fallback
# ---------------------------------------------------------------

def _save_credentials_db(creds_data: dict, empresa_id: int = 1):
    """Salvar credenciais OAuth no PostgreSQL"""
    try:
        import database_postgresql as db
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO google_calendar_credentials (empresa_id, credentials_json, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (empresa_id)
                DO UPDATE SET credentials_json = EXCLUDED.credentials_json,
                              updated_at = NOW()
            """, (empresa_id, json.dumps(creds_data)))
            cur.close()
        print("✅ [Google Calendar] Credenciais salvas no PostgreSQL")
        return True
    except Exception as e:
        print(f"⚠️ [Google Calendar] Falha ao salvar no DB: {e}")
        return False

def _load_credentials_db(empresa_id: int = 1):
    """Carregar credenciais OAuth do PostgreSQL"""
    try:
        import database_postgresql as db
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT credentials_json FROM google_calendar_credentials WHERE empresa_id = %s",
                (empresa_id,)
            )
            row = cur.fetchone()
            cur.close()
        if row:
            data = row['credentials_json'] if isinstance(row['credentials_json'], dict) else json.loads(row['credentials_json'])
            print("✅ [Google Calendar] Credenciais carregadas do PostgreSQL")
            return data
    except Exception as e:
        print(f"⚠️ [Google Calendar] Falha ao carregar do DB: {e}")
    return None

def _delete_credentials_db(empresa_id: int = 1):
    """Remover credenciais do PostgreSQL"""
    try:
        import database_postgresql as db
        with db.get_db_connection(empresa_id=empresa_id) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM google_calendar_credentials WHERE empresa_id = %s", (empresa_id,))
            cur.close()
    except Exception as e:
        print(f"⚠️ [Google Calendar] Falha ao remover credenciais: {e}")

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
        prompt='consent'  # Força nova autorização para garantir refresh_token
    )
    
    return authorization_url, state

def exchange_code_for_tokens(code, state=None, empresa_id: int = 1):
    """
    Trocar código de autorização por tokens de acesso
    Args:
        code: Código de autorização retornado pelo Google
        state: Estado da sessão (opcional)
        empresa_id: ID da empresa (para isolamento multi-tenant)
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
    
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': list(credentials.scopes) if credentials.scopes else [],
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }
    
    # 1. Salvar no PostgreSQL (Railway-safe)
    if not _save_credentials_db(creds_data, empresa_id):
        # 2. Fallback: arquivo local (desenvolvimento)
        try:
            ensure_config_dir()
            with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(creds_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Também não salvou em arquivo: {e}")
    
    return creds_data

def get_credentials(empresa_id: int = 1):
    """
    Obter credenciais OAuth salvas e renovar se necessário.
    Tenta PostgreSQL primeiro, fallback para arquivo local.
    Returns: Credentials object ou None
    """
    # 1. Tentar PostgreSQL (Railway-safe)
    creds_data = _load_credentials_db(empresa_id)

    # 2. Fallback para arquivo local (desenvolvimento)
    if not creds_data:
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                    creds_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao ler arquivo de credenciais: {e}")
    
    if not creds_data:
        return None
    
    try:
        expiry_str = creds_data.get('expiry')
        expiry = None
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
            except (ValueError, TypeError):
                expiry = None

        credentials = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes'),
            expiry=expiry
        )
        
        # Renovar token se expirado
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            creds_data['token'] = credentials.token
            # Atualizar refresh_token caso o Google tenha rotacionado
            if credentials.refresh_token:
                creds_data['refresh_token'] = credentials.refresh_token
            creds_data['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
            # Persistir token renovado
            if not _save_credentials_db(creds_data, empresa_id):
                try:
                    ensure_config_dir()
                    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(creds_data, f, indent=2)
                except Exception:
                    pass
        
        return credentials
    except Exception as e:
        print(f"❌ Erro ao carregar credenciais: {e}")
        return None

def get_calendar_service(empresa_id: int = 1):
    """
    Obter serviço do Google Calendar
    Returns: Resource object ou None
    """
    credentials = get_credentials(empresa_id)
    if not credentials:
        return None
    
    try:
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Erro ao criar serviço do Calendar: {e}")
        return None

def _get_calendar_id(empresa_id: int = 1) -> str:
    """
    Retorna o calendar_id configurado para a empresa, ou 'primary' como fallback.
    """
    try:
        import database_postgresql as _db
        with _db.get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT valor FROM config_sistema WHERE chave = 'agenda_email_settings'"
            )
            row = cur.fetchone()
            if row and row['valor']:
                import json as _json
                settings = _json.loads(row['valor']) if isinstance(row['valor'], str) else row['valor']
                cal_id = settings.get('google_calendar_id', '').strip()
                if cal_id:
                    return cal_id
    except Exception:
        pass
    return 'primary'

def create_calendar_event(session_data, empresa_id: int = 1):
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
        empresa_id: ID da empresa (multi-tenant)
    Returns: dict com event_id ou None
    """
    service = get_calendar_service(empresa_id)
    if not service:
        return {'error': 'Não autorizado. Configure Google Calendar primeiro.'}
    
    try:
        # Construir data/hora de início e fim
        start_datetime_str = f"{session_data['date']}T{session_data.get('time', '00:00')}:00"
        start_datetime = datetime.fromisoformat(start_datetime_str)
        
        duration = session_data.get('duration', 60)  # minutos
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        # Montar attendees (fornecedores + funcionários da equipe)
        raw_attendees = session_data.get('attendees', [])
        attendees = []
        for a in raw_attendees:
            if isinstance(a, str):
                if a:
                    attendees.append({'email': a})
            elif isinstance(a, dict) and a.get('email'):
                attendees.append(a)

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

        if attendees:
            event['attendees'] = attendees
            event['guestsCanSeeOtherGuests'] = False

        calendar_id = _get_calendar_id(empresa_id)
        send_updates = 'all' if attendees else 'none'
        try:
            event_result = service.events().insert(
                calendarId=calendar_id, body=event, sendUpdates=send_updates
            ).execute()
        except HttpError as insert_err:
            # Se o calendar_id configurado não existe, tentar com 'primary'
            if insert_err.resp.status == 404 and calendar_id != 'primary':
                print(f"⚠️ Calendar '{calendar_id}' não encontrado (404), usando 'primary'")
                event_result = service.events().insert(
                    calendarId='primary', body=event, sendUpdates=send_updates
                ).execute()
            else:
                raise

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
        err_str = str(e)
        if 'invalid_grant' in err_str or 'Token has been expired or revoked' in err_str:
            return {'error': 'Token do Google Calendar expirou. Reconecte nas configurações.', 'token_expired': True}
        return {'error': err_str}

def update_calendar_event(event_id, session_data, empresa_id: int = 1,
                          send_updates: str = None):
    """
    Atualizar evento existente no Google Calendar.
    Args:
        event_id: ID do evento no Google Calendar
        session_data: dict com dados atualizados da sessão
        empresa_id: ID da empresa (multi-tenant)
        send_updates: 'all' | 'none' | None (auto: envia só se há novos attendees)
    Returns: dict com sucesso ou erro
    """
    service = get_calendar_service(empresa_id)
    if not service:
        return {'error': 'Não autorizado'}
    
    try:
        calendar_id = _get_calendar_id(empresa_id)
        # Buscar evento atual; se não encontrado no calendário configurado, tenta 'primary'
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except HttpError as get_err:
            if get_err.resp.status == 404:
                if calendar_id != 'primary':
                    print(f"⚠️ Evento '{event_id}' não encontrado em '{calendar_id}', tentando 'primary'")
                    try:
                        calendar_id = 'primary'
                        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
                    except HttpError as get_err2:
                        if get_err2.resp.status == 404:
                            print(f"⚠️ Evento '{event_id}' não encontrado em nenhum calendário (orphan)")
                            return {'error': f'Evento não encontrado: {event_id}', 'not_found': True}
                        raise
                else:
                    print(f"⚠️ Evento '{event_id}' não encontrado em 'primary' (orphan)")
                    return {'error': f'Evento não encontrado: {event_id}', 'not_found': True}
            else:
                raise
        
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

        # Capturar e-mails existentes NO GOOGLE antes de alterar qualquer coisa
        # (DEVE ser feito antes do bloco de attendees abaixo)
        old_attendee_emails = {
            (a.get('email') or '').lower()
            for a in event.get('attendees', [])
        }

        # Atualizar attendees (fornecedores + funcionários da equipe)
        raw_attendees = session_data.get('attendees', [])
        new_attendees = []
        if raw_attendees is not None:
            for a in raw_attendees:
                if isinstance(a, str):
                    if a:
                        new_attendees.append({'email': a})
                elif isinstance(a, dict) and a.get('email'):
                    new_attendees.append(a)
            if new_attendees:
                event['attendees'] = new_attendees
                event['guestsCanSeeOtherGuests'] = False
            else:
                event.pop('attendees', None)

        # Determinar sendUpdates:
        # - Se o caller passou explicitamente, usar.
        # - Caso contrário, calcular: só 'all' se há e-mails novos vs o Google.
        if send_updates is None:
            new_emails = {(a.get('email') or '').lower() for a in new_attendees}
            truly_new = new_emails - old_attendee_emails
            send_updates = 'all' if truly_new else 'none'
            if truly_new:
                print(f"  📧 Novos convidados no Google (vs evento atual): {truly_new}")
            else:
                print(f"  📧 Nenhum novo convidado — sendUpdates=none")

        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates=send_updates,
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
        err_str = str(e)
        if 'invalid_grant' in err_str or 'Token has been expired or revoked' in err_str:
            return {'error': 'Token do Google Calendar expirou. Reconecte nas configurações.', 'token_expired': True}
        return {'error': err_str}

def delete_calendar_event(event_id, empresa_id: int = 1):
    """
    Deletar evento do Google Calendar
    Args:
        event_id: ID do evento
        empresa_id: ID da empresa (multi-tenant)
    Returns: dict com sucesso ou erro
    """
    service = get_calendar_service(empresa_id)
    if not service:
        return {'error': 'Não autorizado'}
    
    try:
        calendar_id = _get_calendar_id(empresa_id)
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {'success': True, 'message': 'Evento removido com sucesso'}
    
    except HttpError as error:
        print(f"❌ Erro HTTP ao deletar evento: {error}")
        return {'error': f'Erro ao deletar evento: {error}'}
    except Exception as e:
        print(f"❌ Erro ao deletar evento: {e}")
        return {'error': str(e)}

def list_calendar_events(start_date=None, end_date=None, max_results=100, empresa_id: int = 1):
    """
    Listar eventos do Google Calendar
    Args:
        start_date: Data de início (formato: YYYY-MM-DD)
        end_date: Data de fim (formato: YYYY-MM-DD)
        max_results: Número máximo de resultados
        empresa_id: ID da empresa (multi-tenant)
    Returns: list de eventos ou dict com erro
    """
    service = get_calendar_service(empresa_id)
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
        
        calendar_id = _get_calendar_id(empresa_id)
        params = {
            'calendarId': calendar_id,
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

def is_authorized(empresa_id: int = 1):
    """
    Verificar se o usuário está autorizado
    Args:
        empresa_id: ID da empresa (multi-tenant)
    Returns: bool
    """
    return get_credentials(empresa_id) is not None


def deduplicate_events(empresa_id: int = 1) -> dict:
    """
    Remove eventos duplicados do Google Calendar.
    Estratégia: busca todas as sessões do DB, para cada sessão busca eventos
    no Google Calendar no mesmo dia com título idêntico e elimina os extras,
    mantendo o evento cujo ID está salvo em google_event_id (ou o mais recente).
    Returns: dict com contagem de removidos e erros
    """
    service = get_calendar_service(empresa_id)
    if not service:
        return {'error': 'Não autorizado'}

    try:
        import database_postgresql as _db
        sessoes = _db.listar_sessoes(empresa_id=empresa_id)
    except Exception as e:
        return {'error': f'Erro ao buscar sessões: {e}'}

    removed = 0
    errors = []
    calendar_id = _get_calendar_id(empresa_id)

    for sessao in sessoes:
        if sessao.get('status') == 'cancelada':
            continue

        data_str = str(sessao.get('data', ''))[:10]
        if not data_str:
            continue

        titulo_esperado = f"{sessao.get('cliente_nome', 'Cliente')} - Sessão"
        google_event_id_salvo = sessao.get('google_event_id')

        try:
            # Buscar todos os eventos deste dia no Google Calendar
            time_min = f"{data_str}T00:00:00Z"
            time_max = f"{data_str}T23:59:59Z"

            result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                maxResults=50
            ).execute()
            eventos_do_dia = result.get('items', [])

            # Filtrar apenas os que têm o mesmo título (criados por este sistema)
            duplicados = [e for e in eventos_do_dia if e.get('summary', '') == titulo_esperado]

            if len(duplicados) <= 1:
                continue  # Sem duplicata, pular

            # Decidir qual manter: o que está salvo no DB, ou o primeiro encontrado
            id_a_manter = google_event_id_salvo
            if not id_a_manter or not any(e['id'] == id_a_manter for e in duplicados):
                id_a_manter = duplicados[0]['id']

            # Deletar os outros
            for evento in duplicados:
                if evento['id'] == id_a_manter:
                    continue
                try:
                    service.events().delete(calendarId=calendar_id, eventId=evento['id']).execute()
                    removed += 1
                    print(f"🗑️ [Dedup] Removido evento duplicado {evento['id']} (sessão {sessao.get('id')})")
                except HttpError as del_err:
                    if del_err.resp.status == 410:  # Already deleted
                        removed += 1
                    else:
                        errors.append(f"Sessão {sessao.get('id')}: erro ao remover {evento['id']}: {del_err}")

            # Garantir que o google_event_id no DB aponta para o evento mantido
            if google_event_id_salvo != id_a_manter:
                try:
                    _db.salvar_google_event_id(sessao.get('id'), id_a_manter, empresa_id=empresa_id)
                except Exception:
                    pass

        except HttpError as e:
            errors.append(f"Sessão {sessao.get('id')}: {e}")
        except Exception as e:
            errors.append(f"Sessão {sessao.get('id')}: {e}")

    return {
        'success': True,
        'removed': removed,
        'errors': errors[:5] if errors else []
    }

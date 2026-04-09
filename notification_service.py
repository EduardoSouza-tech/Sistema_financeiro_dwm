"""
Sistema de Notificações Automáticas
Envia alertas sobre contratos e sessões via e-mail e Google Calendar
"""

import os
import json
import smtplib
import urllib.request
import urllib.error
try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict


def _fmt_date(value) -> str:
    """Converte data de yyyy-mm-dd para dd/mm/yyyy. Retorna o valor original se falhar."""
    if not value:
        return 'Não informada'
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return str(value)
import database_postgresql as db
from app.utils import google_calendar_helper

# ---------------------------------------------------------------------------
# Log de notificações enviadas (tabela notificacoes_log)
# ---------------------------------------------------------------------------

def _ensure_log_table():
    """Cria a tabela notificacoes_log se não existir (idempotente)."""
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notificacoes_log (
                    id            SERIAL PRIMARY KEY,
                    empresa_id    INTEGER NOT NULL,
                    tipo          VARCHAR(50) NOT NULL,
                    referencia_id INTEGER,
                    referencia_data DATE,
                    destinatarios TEXT NOT NULL,
                    assunto       TEXT NOT NULL,
                    status        VARCHAR(20) NOT NULL DEFAULT 'enviado',
                    erro_detalhe  TEXT,
                    enviado_em    TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_notif_log_empresa_tipo
                ON notificacoes_log(empresa_id, tipo, referencia_id, enviado_em)
            """)
    except Exception as e:
        print(f"⚠️ Erro ao criar tabela notificacoes_log: {e}")


def log_notification_sent(empresa_id: int, tipo: str, referencia_id,
                          referencia_data, destinatarios: List[str],
                          assunto: str, status: str, erro_detalhe: str = None):
    """Registra no banco um e-mail enviado (ou tentativa com erro)."""
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO notificacoes_log
                    (empresa_id, tipo, referencia_id, referencia_data,
                     destinatarios, assunto, status, erro_detalhe)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                empresa_id, tipo, referencia_id,
                referencia_data if referencia_data else None,
                json.dumps(destinatarios, ensure_ascii=False),
                assunto, status, erro_detalhe,
            ))
    except Exception as e:
        print(f"⚠️ Erro ao registrar log de notificação: {e}")


def was_notified_today(empresa_id: int, tipo: str, referencia_id) -> bool:
    """Retorna True se já existe um envio bem-sucedido deste tipo/item hoje."""
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 1 FROM notificacoes_log
                WHERE empresa_id   = %s
                  AND tipo         = %s
                  AND referencia_id = %s
                  AND status        = 'enviado'
                  AND enviado_em   >= CURRENT_DATE
                  AND enviado_em   <  CURRENT_DATE + INTERVAL '1 day'
                LIMIT 1
            """, (empresa_id, tipo, referencia_id))
            return cur.fetchone() is not None
    except Exception as e:
        print(f"⚠️ Erro ao verificar deduplicação: {e}")
        # CORREÇÃO: Em caso de erro na verificação, assumir que já foi notificado
        # para evitar spam de e-mails em caso de problemas de conexão com banco
        return True   # Previne envio múltiplo em caso de falha


def get_notifications_log(empresa_id: int, limit: int = 50) -> List[Dict]:
    """Retorna o histórico de notificações da empresa (mais recentes primeiro)."""
    _ensure_log_table()
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(allow_global=True) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, tipo, referencia_id, referencia_data,
                       destinatarios, assunto, status, erro_detalhe,
                       TO_CHAR(enviado_em AT TIME ZONE 'America/Sao_Paulo',
                               'DD/MM/YYYY HH24:MI') AS enviado_em_fmt
                FROM notificacoes_log
                WHERE empresa_id = %s
                ORDER BY enviado_em DESC
                LIMIT %s
            """, (empresa_id, limit))
            rows = cur.fetchall()
            result = []
            for row in rows:
                dest = row['destinatarios']
                if isinstance(dest, str):
                    try:
                        dest = json.loads(dest)
                    except Exception:
                        pass
                result.append({
                    'id':              row['id'],
                    'tipo':            row['tipo'],
                    'referencia_id':   row['referencia_id'],
                    'referencia_data': str(row['referencia_data']) if row['referencia_data'] else None,
                    'destinatarios':   dest,
                    'assunto':         row['assunto'],
                    'status':          row['status'],
                    'erro_detalhe':    row['erro_detalhe'],
                    'enviado_em':      row['enviado_em_fmt'],
                })
            return result
    except Exception as e:
        print(f"⚠️ Erro ao buscar log de notificações: {e}")
        return []


def _get_fornecedor_emails_from_equipe(equipe: list, empresa_id: int) -> List[str]:
    """
    Extrai e-mails dos fornecedores listados na equipe de uma sessão.
    Itens com tipo_pessoa='forn' ou pessoa_id iniciando com 'forn_' são fornecedores.
    Apenas e-mails válidos (não-vazios) são retornados.
    """
    if not equipe:
        return []
    forn_ids = []
    for item in equipe:
        if not isinstance(item, dict):
            continue
        tipo = item.get('tipo_pessoa', '')
        pessoa_id = str(item.get('pessoa_id', ''))
        id_pessoa = item.get('id_pessoa')
        if tipo == 'forn' or pessoa_id.startswith('forn_'):
            try:
                fid = int(id_pessoa) if id_pessoa is not None else int(pessoa_id.replace('forn_', ''))
                forn_ids.append(fid)
            except (ValueError, TypeError):
                pass
    if not forn_ids:
        return []
    emails = []
    try:
        from database_postgresql import get_db_connection
        with get_db_connection(empresa_id=empresa_id) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT email FROM fornecedores WHERE id = ANY(%s) AND empresa_id = %s AND email IS NOT NULL AND email <> ''",
                (forn_ids, empresa_id)
            )
            for row in cur.fetchall():
                email = (row['email'] or '').strip()
                if email and email not in emails:
                    emails.append(email)
    except Exception as e:
        print(f"⚠️ Erro ao buscar e-mails de fornecedores da equipe: {e}")
    return emails


def send_upcoming_session_reminders(empresa_id: int, days_ahead: int = 3, force: bool = False) -> Dict:
    """
    Envia lembretes para sessões próximas.
    force=True pula a deduplicação diária (uso manual).
    force=False (padrão) respeita o limite de 1 e-mail por sessão por dia (uso automático).
    Retorna resumo: {'sent': N, 'skipped': N, 'error': N, 'sessions': [...]}
    """
    _ensure_log_table()
    settings = load_email_settings()
    recipients = settings.get('notification_emails', [])

    result = {'sent': 0, 'skipped': 0, 'error': 0, 'sessions': [], 'total_upcoming': 0}

    upcoming = check_upcoming_sessions(empresa_id, days_ahead=days_ahead)
    result['total_upcoming'] = len(upcoming)

    if not upcoming:
        result['error_msg'] = f'Nenhuma sessão agendada nos próximos {days_ahead} dias'
        return result

    # Separar sessões já notificadas hoje das que ainda precisam de lembrete
    to_notify = []
    for sessao in upcoming:
        sessao_id = sessao.get('id')
        if not force and sessao_id and was_notified_today(empresa_id, 'lembrete_sessao', sessao_id):
            result['skipped'] += 1
            result['sessions'].append({
                'id': sessao_id,
                'acao': 'pulado',
                'motivo': 'já notificado hoje',
                'data': sessao.get('data'),
                'cliente': sessao.get('cliente_nome'),
            })
        else:
            to_notify.append(sessao)

    if not to_notify:
        return result

    # --- Envio em lote para notification_emails (se configurados) ---
    if recipients:
        assunto = f"\U0001f4c5 Lembrete \u2014 {len(to_notify)} Sessões nos Próximos {days_ahead} Dias"
        html = create_notification_html(
            f"\U0001f4c5 Lembrete: {len(to_notify)} Sessões nos Próximos {days_ahead} Dias",
            to_notify,
            'sessoes_proximas'
        )
        ok = send_email_notification(recipients, assunto, html)
        status_log = 'enviado' if ok else 'erro'
        erro_detalhe = None if ok else 'Falha ao enviar via Resend/SMTP'

        for sessao in to_notify:
            sessao_id  = sessao.get('id')
            sessao_dt  = sessao.get('data')
            log_notification_sent(
                empresa_id, 'lembrete_sessao', sessao_id,
                sessao_dt, recipients, assunto, status_log, erro_detalhe,
            )
            result['sessions'].append({
                'id':      sessao_id,
                'acao':    status_log,
                'data':    sessao_dt,
                'cliente': sessao.get('cliente_nome'),
            })

        if ok:
            result['sent'] = len(to_notify)
        else:
            result['error'] = len(to_notify)
            result['error_msg'] = erro_detalhe
    else:
        result['error_msg'] = 'Nenhum e-mail destinatário configurado'

    # --- Envio individual para fornecedores da equipe de cada sessão ---
    # Roda sempre, independente de notification_emails estar configurado ou não.
    # Cada sessão gera um e-mail separado apenas para os fornecedores daquela sessão.
    for sessao in to_notify:
        sessao_id = sessao.get('id')

        # Deduplicação: não reenviar para fornecedores desta sessão se já foi feito hoje
        if not force and sessao_id and was_notified_today(empresa_id, 'lembrete_sessao_fornecedor', sessao_id):
            print(f"  ⏭️ Fornecedores da sessão {sessao_id} já notificados hoje")
            continue

        forn_emails = _get_fornecedor_emails_from_equipe(
            sessao.get('equipe', []), empresa_id
        )
        if not forn_emails:
            continue

        data_fmt = _fmt_date(sessao.get('data'))
        assunto_forn = (
            f"\U0001f4c5 Lembrete de Sessão — "
            f"{sessao.get('cliente_nome', 'Cliente')} em "
            f"{data_fmt}"
        )
        html_forn = create_notification_html(
            f"\U0001f4c5 Lembrete: Sessão em {data_fmt}",
            [sessao],
            'sessoes_proximas'
        )
        ok_forn = send_email_notification(forn_emails, assunto_forn, html_forn)
        status_forn = 'enviado' if ok_forn else 'erro'
        erro_forn = None if ok_forn else 'Falha ao enviar via Resend/SMTP'
        log_notification_sent(
            empresa_id, 'lembrete_sessao_fornecedor', sessao_id,
            sessao.get('data'), forn_emails, assunto_forn, status_forn, erro_forn,
        )
        if ok_forn:
            result['sent'] += len(forn_emails)
        print(f"  {'✅' if ok_forn else '❌'} Fornecedores notificados para sessão "
              f"{sessao_id}: {forn_emails}")

    return result

# ---------------------------------------------------------------------------
# Usar load_email_settings do blueprint de agenda (que persiste no PostgreSQL)
def load_email_settings():
    """
    Delega para app.routes.agenda.load_email_settings, que consulta o PostgreSQL
    antes do arquivo local — garantindo persistência entre redeploys no Railway.
    """
    try:
        from app.routes.agenda import load_email_settings as _load
        return _load()
    except Exception as e:
        print(f"⚠️ Erro ao importar load_email_settings do agenda: {e}")
        # Fallback mínimo via env vars
        smtp_host     = os.getenv('SMTP_HOST', '')
        smtp_port     = int(os.getenv('SMTP_PORT', 587))
        smtp_user     = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        smtp_from     = os.getenv('SMTP_FROM_EMAIL', smtp_user)
        smtp_name     = os.getenv('SMTP_FROM_NAME', 'Sistema Financeiro DWM')
        smtp_enabled  = bool(smtp_host and smtp_user and smtp_password)
        return {
            'notification_emails': [],
            'google_calendar_enabled': False,
            'smtp_enabled': smtp_enabled,
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'smtp_user': smtp_user,
            'smtp_password': smtp_password,
            'smtp_from_email': smtp_from,
            'smtp_from_name': smtp_name,
        }

def _send_via_resend(recipients: List[str], subject: str, html_content: str,
                     plain_content: str, from_email: str, from_name: str) -> bool:
    """
    Envia e-mail via Resend HTTP API (porta 443 — nunca bloqueada pelo Railway).
    Requer env var RESEND_API_KEY.
    """
    api_key = os.getenv('RESEND_API_KEY', '')
    if not api_key:
        return False

    payload = {
        'from': f'{from_name} <{from_email}>',
        'to': recipients,
        'subject': subject,
        'html': html_content,
    }
    if plain_content:
        payload['text'] = plain_content

    if _REQUESTS_AVAILABLE:
        try:
            resp = _requests.post(
                'https://api.resend.com/emails',
                json=payload,
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                print(f"✅ E-mail enviado via Resend para {len(recipients)} destinatário(s)")
                return True
            print(f"❌ Erro ao enviar via Resend: HTTP {resp.status_code} | from={from_email} | body={resp.text}")
            return False
        except Exception as e:
            print(f"❌ Erro ao enviar via Resend: {e}")
            return False

    # fallback urllib (caso requests não esteja disponível)
    encoded_payload = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=encoded_payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            if status in (200, 201):
                print(f"✅ E-mail enviado via Resend para {len(recipients)} destinatário(s)")
                return True
            body = resp.read().decode()
            print(f"❌ Resend retornou status {status}: {body}")
            return False
    except urllib.error.HTTPError as e:
        body = ''
        try:
            body = e.read().decode('utf-8', errors='replace')
        except Exception:
            pass
        print(f"❌ Erro ao enviar via Resend: HTTP {e.code} {e.reason} | from={from_email} | body={body}")
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar via Resend: {e}")
        return False


def send_email_notification(recipients: List[str], subject: str, html_content: str, plain_content: str = None):
    """
    Enviar notificação por e-mail.
    Estratégia:
      1. Se RESEND_API_KEY estiver configurada → usa Resend (HTTPS, Railway-safe)
      2. Caso contrário → tenta SMTP (porta 587/465, pode ser bloqueada em alguns PaaS)
    """
    if not recipients:
        print("⚠️ Nenhum destinatário especificado")
        return False

    settings = load_email_settings()
    from_email = settings.get('smtp_from_email', '')
    from_name  = settings.get('smtp_from_name', 'Sistema Financeiro DWM')

    # -- Tentativa 1: Resend (HTTPS) --
    if os.getenv('RESEND_API_KEY'):
        # Resend exige remetente do domínio verificado — não pode ser @gmail.com
        resend_from = os.getenv('RESEND_FROM_EMAIL', from_email)
        resend_name = os.getenv('RESEND_FROM_NAME', from_name)
        return _send_via_resend(recipients, subject, html_content,
                                plain_content or '', resend_from, resend_name)

    # -- Tentativa 2: SMTP direto --
    if not settings.get('smtp_enabled'):
        print("⚠️ SMTP não configurado e RESEND_API_KEY não definida")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = f"{from_name} <{from_email}>"
        msg['To']      = ', '.join(recipients)
        msg['Subject'] = subject

        if plain_content:
            msg.attach(MIMEText(plain_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        server = smtplib.SMTP(settings['smtp_host'], settings['smtp_port'])
        server.starttls()
        server.login(settings['smtp_user'], settings['smtp_password'])
        server.send_message(msg)
        server.quit()

        print(f"✅ E-mail enviado via SMTP para {len(recipients)} destinatário(s)")
        return True

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False

def _resolve_kit_names(empresa_id: int, kit_ids: list) -> str:
    """
    Recebe uma lista de IDs ou dicts de kits e retorna string com os nomes.
    Ex: [9, 8] -> 'Canon EOS R5, Tripé'
    """
    if not kit_ids:
        return 'Não informado'
    # Se já são dicts com 'nome', apenas concatenar
    if all(isinstance(e, dict) for e in kit_ids):
        nomes = [e.get('nome', '') for e in kit_ids if e.get('nome')]
        return ', '.join(nomes) if nomes else 'Não informado'
    # IDs numéricos: buscar nomes no banco
    ids = [int(e) for e in kit_ids if str(e).isdigit()]
    if not ids:
        return ', '.join(str(e) for e in kit_ids)
    try:
        from database_postgresql import get_db_connection
        placeholders = ','.join(['%s'] * len(ids))
        with get_db_connection(empresa_id=empresa_id) as conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT id, nome FROM kits_equipamentos WHERE id IN ({placeholders})",
                ids,
            )
            rows = cur.fetchall()
        if not rows:
            # Tentar tabela alternativa 'kits'
            with get_db_connection(empresa_id=empresa_id) as conn:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT id, nome FROM kits WHERE id IN ({placeholders})",
                    ids,
                )
                rows = cur.fetchall()
        id_to_name = {r['id']: r['nome'] for r in rows}
        nomes = [id_to_name.get(i, f'Kit #{i}') for i in ids]
        return ', '.join(nomes)
    except Exception as e:
        print(f"⚠️ Erro ao resolver nomes de kits: {e}")
        return ', '.join(str(e) for e in kit_ids)


def create_notification_html(title: str, items: List[Dict], notification_type: str) -> str:
    """
    Criar HTML para notificação
    Args:
        title: Título da notificação
        items: Lista de itens (sessões ou contratos)
        notification_type: 'sessoes_proximas', 'sessoes_atrasadas', 'contratos_proximos', etc.
    Returns:
        HTML formatado
    """
    # Determinar cor baseada no tipo
    colors = {
        'sessoes_proximas': '#f39c12',
        'sessoes_atrasadas': '#e74c3c',
        'sessoes_abertas': '#3498db',
        'contratos_proximos': '#f39c12',
        'contratos_vencidos': '#e74c3c'
    }
    color = colors.get(notification_type, '#3498db')
    
    # Criar HTML dos itens
    items_html = ""
    for item in items:
        if 'data' in item:  # Sessão
            # Equipamentos próprios (lista de dicts com 'nome' ou strings)
            equipamentos = item.get('equipamentos') or []
            if equipamentos:
                # Pode ser lista de IDs (int) ou dicts com 'nome' — resolver ambos
                has_ids = any(not isinstance(e, dict) for e in equipamentos)
                if has_ids:
                    empresa_id_item = item.get('empresa_id')
                    equip_str = _resolve_kit_names(empresa_id_item, equipamentos)
                else:
                    nomes = [e.get('nome', '') for e in equipamentos if e.get('nome')]
                    equip_str = ', '.join(nomes) or 'Não informado'
            else:
                equip_str = 'Não informado'

            items_html += f"""
            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid {color}; margin-bottom: 10px; border-radius: 4px;">
                <div style="font-weight: bold; color: #2c3e50; margin-bottom: 5px;">
                    📅 {_fmt_date(item['data'])} - {item.get('horario', 'Horário não definido')}
                </div>
                <div style="color: #34495e; margin-bottom: 3px;">
                    👤 Cliente: <strong>{item.get('cliente_nome', 'Não informado')}</strong>
                </div>
                <div style="color: #7f8c8d; font-size: 13px;">
                    📍 Local: {item.get('endereco', 'Não informado')}
                </div>
                <div style="color: #7f8c8d; font-size: 13px;">
                    📝 Tipo: {item.get('tipo_captacao', 'Não informado')}
                </div>
                <div style="color: #7f8c8d; font-size: 13px;">
                    🎒 Equipamento(s): {equip_str}
                </div>
            </div>
            """
        else:  # Contrato
            items_html += f"""
            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid {color}; margin-bottom: 10px; border-radius: 4px;">
                <div style="font-weight: bold; color: #2c3e50; margin-bottom: 5px;">
                    📄 Contrato Nº {item.get('numero', 'S/N')}
                </div>
                <div style="color: #34495e; margin-bottom: 3px;">
                    👤 Cliente: <strong>{item.get('cliente_nome', 'Não informado')}</strong>
                </div>
                <div style="color: #7f8c8d; font-size: 13px;">
                    📅 Validade: {_fmt_date(item.get('data_fim'))}
                </div>
                <div style="color: #7f8c8d; font-size: 13px;">
                    ⏱️ Horas: {item.get('horas_utilizadas', 0)} / {item.get('horas_totais', 0)}
                </div>
            </div>
            """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f6fa;">
        <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 700;">
                    {title}
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">
                    Sistema Financeiro DWM - Sistema de Notificações
                </p>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px;">
                <p style="color: #2c3e50; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                    Você recebeu este e-mail porque há <strong>{len(items)} item(ns)</strong> que requer(em) sua atenção:
                </p>
                
                {items_html}
                
                <div style="margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 6px; text-align: center;">
                    <p style="margin: 0; color: #7f8c8d; font-size: 13px;">
                        📧 Este é um e-mail automático. Não responda a esta mensagem.
                    </p>
                    <p style="margin: 10px 0 0 0; color: #7f8c8d; font-size: 13px;">
                        Para gerenciar suas notificações, acesse o sistema e vá em <strong>Agenda de Fotografia → Configurações</strong>
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #34495e; padding: 20px; text-align: center;">
                <p style="color: #ecf0f1; margin: 0; font-size: 12px;">
                    © {datetime.now().year} Sistema Financeiro DWM | Todos os direitos reservados
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def check_upcoming_sessions(empresa_id: int, days_ahead: int = 3) -> List[Dict]:
    """
    Verificar sessões próximas
    Args:
        empresa_id: ID da empresa
        days_ahead: Quantos dias à frente verificar
    Returns:
        Lista de sessões próximas
    """
    try:
        # Buscar todas as sessões
        all_sessions = db.listar_sessoes(empresa_id=empresa_id)
        
        today = datetime.now().date()
        limit_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        for sessao in all_sessions:
            # Excluir apenas canceladas — finalizadas com data futura ainda precisam de lembrete
            if sessao.get('status') != 'cancelada':
                try:
                    sessao_date = datetime.strptime(str(sessao['data'])[:10], '%Y-%m-%d').date()
                    if today <= sessao_date <= limit_date:
                        upcoming.append(sessao)
                except:
                    pass
        
        return upcoming
    except Exception as e:
        print(f"❌ Erro ao verificar sessões próximas: {e}")
        return []

def check_overdue_sessions(empresa_id: int) -> List[Dict]:
    """
    Verificar sessões atrasadas
    Args:
        empresa_id: ID da empresa
    Returns:
        Lista de sessões atrasadas
    """
    try:
        all_sessions = db.listar_sessoes(empresa_id=empresa_id)
        
        today = datetime.now().date()
        
        overdue = []
        for sessao in all_sessions:
            # Excluir apenas canceladas e finalizadas (sessão atrasada = não realizada ainda)
            if sessao.get('status') not in ['finalizada', 'cancelada']:
                try:
                    sessao_date = datetime.strptime(str(sessao['data'])[:10], '%Y-%m-%d').date()
                    if sessao_date < today:
                        overdue.append(sessao)
                except:
                    pass
        
        return overdue
    except Exception as e:
        print(f"❌ Erro ao verificar sessões atrasadas: {e}")
        return []

def check_open_sessions(empresa_id: int) -> List[Dict]:
    """
    Verificar sessões em aberto (pendentes)
    Args:
        empresa_id: ID da empresa
    Returns:
        Lista de sessões em aberto
    """
    try:
        all_sessions = db.listar_sessoes(empresa_id=empresa_id)
        
        open_sessions = []
        for sessao in all_sessions:
            if sessao.get('status') == 'pendente':
                open_sessions.append(sessao)
        
        return open_sessions
    except Exception as e:
        print(f"❌ Erro ao verificar sessões em aberto: {e}")
        return []

def check_upcoming_contracts(empresa_id: int, days_ahead: int = 30) -> List[Dict]:
    """
    Verificar contratos próximos do vencimento
    Args:
        empresa_id: ID da empresa
        days_ahead: Quantos dias à frente verificar
    Returns:
        Lista de contratos próximos do vencimento
    """
    try:
        all_contracts = db.listar_contratos(empresa_id=empresa_id)
        
        today = datetime.now().date()
        limit_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        for contrato in all_contracts:
            if contrato.get('status') == 'ativo' and contrato.get('data_fim'):
                try:
                    end_date = datetime.strptime(contrato['data_fim'], '%Y-%m-%d').date()
                    if today <= end_date <= limit_date:
                        upcoming.append(contrato)
                except:
                    pass
        
        return upcoming
    except Exception as e:
        print(f"❌ Erro ao verificar contratos próximos: {e}")
        return []

def check_expired_contracts(empresa_id: int) -> List[Dict]:
    """
    Verificar contratos vencidos
    Args:
        empresa_id: ID da empresa
    Returns:
        Lista de contratos vencidos
    """
    try:
        all_contracts = db.listar_contratos(empresa_id=empresa_id)
        
        today = datetime.now().date()
        
        expired = []
        for contrato in all_contracts:
            if contrato.get('status') == 'ativo' and contrato.get('data_fim'):
                try:
                    end_date = datetime.strptime(contrato['data_fim'], '%Y-%m-%d').date()
                    if end_date < today:
                        expired.append(contrato)
                except:
                    pass
        
        return expired
    except Exception as e:
        print(f"❌ Erro ao verificar contratos vencidos: {e}")
        return []

def send_notification_batch(empresa_id: int):
    """
    Enviar lote de notificações para uma empresa.
    Usa deduplicação por sessão/contrato (não reenvía o mesmo item no mesmo dia).
    Registra cada envio na tabela notificacoes_log.
    """
    _ensure_log_table()
    settings = load_email_settings()
    recipients = settings.get('notification_emails', [])

    if not recipients:
        print(f"⚠️ Nenhum e-mail configurado para empresa {empresa_id}")
        return

    print(f"🔍 Verificando notificações para empresa {empresa_id}...")

    def _send_and_log(items, tipo, assunto, titulo, notif_type):
        """Filtra itens ainda não notificados hoje, envia e registra."""
        novos = [i for i in items
                 if not was_notified_today(empresa_id, tipo, i.get('id'))]
        if not novos:
            print(f"  ⏭️ {tipo}: todos os {len(items)} já notificados hoje")
            return
        html = create_notification_html(titulo, novos, notif_type)
        ok   = send_email_notification(recipients, assunto.format(N=len(novos)), html)
        status = 'enviado' if ok else 'erro'
        erro   = None if ok else 'Falha ao enviar via Resend/SMTP'
        for item in novos:
            log_notification_sent(
                empresa_id, tipo, item.get('id'),
                item.get('data') or item.get('data_fim'),
                recipients, assunto.format(N=len(novos)), status, erro,
            )
        print(f"  {'✅' if ok else '❌'} {tipo}: {len(novos)} enviado(s)")

    # Sessões próximas (3 dias)
    upcoming_sessions = check_upcoming_sessions(empresa_id, days_ahead=3)
    if upcoming_sessions:
        _send_and_log(
            upcoming_sessions, 'lembrete_sessao',
            "⚠️ {N} Sessões nos Próximos 3 Dias",
            "⚠️ Sessões Próximas - Prepare-se!", 'sessoes_proximas',
        )
        # Notificar fornecedores da equipe de cada sessão próxima (individualmente)
        for sessao in upcoming_sessions:
            sessao_id = sessao.get('id')
            if was_notified_today(empresa_id, 'lembrete_sessao_fornecedor', sessao_id):
                print(f"  ⏭️ Fornecedores da sessão {sessao_id} já notificados hoje")
                continue
            forn_emails = _get_fornecedor_emails_from_equipe(
                sessao.get('equipe', []), empresa_id
            )
            if not forn_emails:
                continue
            data_fmt = _fmt_date(sessao.get('data'))
            assunto_forn = (
                f"\U0001f4c5 Lembrete de Sessão — "
                f"{sessao.get('cliente_nome', 'Cliente')} em "
                f"{data_fmt}"
            )
            html_forn = create_notification_html(
                f"\U0001f4c5 Lembrete: Sessão em {data_fmt}",
                [sessao],
                'sessoes_proximas'
            )
            ok_forn = send_email_notification(forn_emails, assunto_forn, html_forn)
            status_forn = 'enviado' if ok_forn else 'erro'
            erro_forn = None if ok_forn else 'Falha ao enviar via Resend/SMTP'
            log_notification_sent(
                empresa_id, 'lembrete_sessao_fornecedor', sessao_id,
                sessao.get('data'), forn_emails, assunto_forn, status_forn, erro_forn,
            )
            print(f"  {'✅' if ok_forn else '❌'} Fornecedores notificados para sessão "
                  f"{sessao_id}: {forn_emails}")

    # Sessões atrasadas
    overdue_sessions = check_overdue_sessions(empresa_id)
    if overdue_sessions:
        _send_and_log(
            overdue_sessions, 'sessao_atrasada',
            "🚨 {N} Sessões Atrasadas",
            "🚨 Sessões Atrasadas - Ação Necessária!", 'sessoes_atrasadas',
        )

    # Sessões em aberto (> 10)
    open_sessions = check_open_sessions(empresa_id)
    if open_sessions and len(open_sessions) > 10:
        _send_and_log(
            open_sessions[:10], 'sessoes_abertas',
            "📝 {N} Sessões em Aberto",
            "📝 Muitas Sessões em Aberto", 'sessoes_abertas',
        )

    # Contratos próximos do vencimento (30 dias)
    upcoming_contracts = check_upcoming_contracts(empresa_id, days_ahead=30)
    if upcoming_contracts:
        _send_and_log(
            upcoming_contracts, 'contrato_proximo',
            "📄 {N} Contrato(s) Vencendo em 30 Dias",
            "📄 Contratos Próximos do Vencimento", 'contratos_proximos',
        )

    # Contratos vencidos
    expired_contracts = check_expired_contracts(empresa_id)
    if expired_contracts:
        _send_and_log(
            expired_contracts, 'contrato_vencido',
            "🚨 {N} Contrato(s) Vencido(s)",
            "🚨 Contratos Vencidos", 'contratos_vencidos',
        )

    print(f"✅ Verificação concluída para empresa {empresa_id}")

def run_notifications_for_all_companies():
    """
    Executar verificação de notificações para todas as empresas
    """
    print("🔔 Iniciando verificação de notificações para todas as empresas...")
    
    try:
        # Buscar todas as empresas
        # TODO: Implementar função para listar todas as empresas
        # Por enquanto, usar empresa ID 1 como exemplo
        empresas = [1]
        
        for empresa_id in empresas:
            try:
                send_notification_batch(empresa_id)
            except Exception as e:
                print(f"❌ Erro ao processar empresa {empresa_id}: {e}")
        
        print("✅ Verificação conclu��da para todas as empresas")
    
    except Exception as e:
        print(f"❌ Erro ao executar notificações: {e}")

if __name__ == '__main__':
    # Executar verificação manual
    import sys
    
    if len(sys.argv) > 1:
        empresa_id = int(sys.argv[1])
        print(f"Executando verificação para empresa {empresa_id}...")
        send_notification_batch(empresa_id)
    else:
        run_notifications_for_all_companies()

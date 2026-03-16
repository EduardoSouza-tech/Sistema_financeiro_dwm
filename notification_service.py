"""
Sistema de Notificações Automáticas
Envia alertas sobre contratos e sessões via e-mail e Google Calendar
"""

import os
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
import database_postgresql as db
from app.utils import google_calendar_helper

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

    payload = json.dumps({
        'from': f'{from_name} <{from_email}>',
        'to': recipients,
        'subject': subject,
        'html': html_content,
        **(({'text': plain_content}) if plain_content else {}),
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
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
            items_html += f"""
            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid {color}; margin-bottom: 10px; border-radius: 4px;">
                <div style="font-weight: bold; color: #2c3e50; margin-bottom: 5px;">
                    📅 {item['data']} - {item.get('horario', 'Horário não definido')}
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
                    📅 Validade: {item.get('data_fim', 'Não informada')}
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
            if sessao.get('status') not in ['finalizada', 'cancelada']:
                try:
                    sessao_date = datetime.strptime(sessao['data'], '%Y-%m-%d').date()
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
            if sessao.get('status') not in ['finalizada', 'cancelada']:
                try:
                    sessao_date = datetime.strptime(sessao['data'], '%Y-%m-%d').date()
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
    Enviar lote de notificações para uma empresa
    Args:
        empresa_id: ID da empresa
    """
    settings = load_email_settings()
    recipients = settings.get('notification_emails', [])
    
    if not recipients:
        print(f"⚠️ Nenhum e-mail configurado para empresa {empresa_id}")
        return
    
    print(f"🔍 Verificando notificações para empresa {empresa_id}...")
    
    # Verificar sessões próximas (3 dias)
    upcoming_sessions = check_upcoming_sessions(empresa_id, days_ahead=3)
    if upcoming_sessions:
        print(f"  📅 {len(upcoming_sessions)} sessões próximas")
        html = create_notification_html(
            "⚠️ Sessões Próximas - Prepare-se!",
            upcoming_sessions,
            'sessoes_proximas'
        )
        send_email_notification(
            recipients,
            f"⚠️ {len(upcoming_sessions)} Sessão(ões) nos Próximos 3 Dias",
            html
        )
    
    # Verificar sessões atrasadas
    overdue_sessions = check_overdue_sessions(empresa_id)
    if overdue_sessions:
        print(f"  🚨 {len(overdue_sessions)} sessões atrasadas")
        html = create_notification_html(
            "🚨 Sessões Atrasadas - Ação Necessária!",
            overdue_sessions,
            'sessoes_atrasadas'
        )
        send_email_notification(
            recipients,
            f"🚨 {len(overdue_sessions)} Sessão(ões) Atrasada(s)",
            html
        )
    
    # Verificar sessões em aberto
    open_sessions = check_open_sessions(empresa_id)
    if open_sessions and len(open_sessions) > 10:  # Só notificar se houver muitas
        print(f"  📝 {len(open_sessions)} sessões em aberto")
        html = create_notification_html(
            "📝 Muitas Sessões em Aberto",
            open_sessions[:10],  # Enviar apenas as 10 primeiras
            'sessoes_abertas'
        )
        send_email_notification(
            recipients,
            f"📝 {len(open_sessions)} Sessão(ões) em Aberto",
            html
        )
    
    # Verificar contratos próximos do vencimento (30 dias)
    upcoming_contracts = check_upcoming_contracts(empresa_id, days_ahead=30)
    if upcoming_contracts:
        print(f"  📄 {len(upcoming_contracts)} contratos próximos do vencimento")
        html = create_notification_html(
            "📄 Contratos Próximos do Vencimento",
            upcoming_contracts,
            'contratos_proximos'
        )
        send_email_notification(
            recipients,
            f"📄 {len(upcoming_contracts)} Contrato(s) Vencendo em 30 Dias",
            html
        )
    
    # Verificar contratos vencidos
    expired_contracts = check_expired_contracts(empresa_id)
    if expired_contracts:
        print(f"  🚨 {len(expired_contracts)} contratos vencidos")
        html = create_notification_html(
            "🚨 Contratos Vencidos",
            expired_contracts,
            'contratos_vencidos'
        )
        send_email_notification(
            recipients,
            f"🚨 {len(expired_contracts)} Contrato(s) Vencido(s)",
            html
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

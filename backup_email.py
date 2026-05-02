"""
Módulo de backup automático por e-mail
Roda 3x ao dia: 06:00, 12:00, 19:00 (horário de Brasília)
Exporta tabelas críticas em JSON e envia como anexo
"""
import os
import json
import io
import zipfile
import smtplib
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import psycopg2
import psycopg2.extras


# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────
SMTP_HOST     = os.getenv('BACKUP_SMTP_HOST',  'smtp.gmail.com')
SMTP_PORT     = int(os.getenv('BACKUP_SMTP_PORT', '587'))
SMTP_USER     = os.getenv('BACKUP_SMTP_USER',  '')   # e-mail remetente
SMTP_PASSWORD = os.getenv('BACKUP_SMTP_PASSWORD', '') # senha de app Gmail
EMAIL_DESTINO = os.getenv('BACKUP_EMAIL_DESTINO', '') # quem recebe
DATABASE_URL  = os.getenv('DATABASE_URL', '')

# Tabelas que serão incluídas no backup
TABELAS_BACKUP = [
    'sessoes',
    'clientes',
    'contratos',
    'lancamentos',
    'funcionarios',
    'eventos',
]


def _json_default(obj):
    """Serializa tipos não-padrão (datetime, date, Decimal)"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return str(obj)


def gerar_backup_zip() -> tuple[bytes, str]:
    """
    Consulta as tabelas críticas e gera um .zip em memória com um JSON por tabela.
    Retorna (bytes_do_zip, nome_do_arquivo).
    """
    agora = datetime.now()
    nome_arquivo = f"backup_DWM_{agora.strftime('%Y%m%d_%H%M')}.zip"

    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        resumo = {}
        for tabela in TABELAS_BACKUP:
            try:
                cur.execute(f"SELECT * FROM {tabela} ORDER BY id DESC")
                rows = [dict(r) for r in cur.fetchall()]
                conteudo = json.dumps(rows, ensure_ascii=False, indent=2, default=_json_default)
                zf.writestr(f"{tabela}.json", conteudo)
                resumo[tabela] = len(rows)
            except Exception as e:
                zf.writestr(f"{tabela}_ERRO.txt", str(e))
                resumo[tabela] = f'ERRO: {e}'

        # Arquivo de resumo
        info = {
            'gerado_em': agora.isoformat(),
            'tabelas': resumo,
            'total_registros': sum(v for v in resumo.values() if isinstance(v, int)),
        }
        zf.writestr('_resumo.json', json.dumps(info, ensure_ascii=False, indent=2))

    cur.close()
    conn.close()

    zip_buffer.seek(0)
    return zip_buffer.read(), nome_arquivo, info


def enviar_backup_email():
    """Gera o backup e envia por e-mail. Chamado pelo scheduler."""
    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_DESTINO, DATABASE_URL]):
        print("⚠️  [BACKUP] Variáveis de ambiente não configuradas — backup ignorado")
        return

    try:
        print(f"📦 [BACKUP] Iniciando backup — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        zip_bytes, nome_arquivo, info = gerar_backup_zip()

        # Monta e-mail
        msg = MIMEMultipart()
        msg['From']    = SMTP_USER
        msg['To']      = EMAIL_DESTINO
        msg['Subject'] = f"🔒 Backup DWM — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        corpo = f"""
<html><body style="font-family:Arial,sans-serif;color:#333;">
<h2 style="color:#3b82f6;">Backup Automático — Sistema DWM</h2>
<p>Gerado em: <strong>{datetime.now().strftime('%d/%m/%Y às %H:%M')}</strong></p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
  <tr style="background:#f1f5f9;"><th>Tabela</th><th>Registros</th></tr>
  {"".join(f'<tr><td>{t}</td><td style="text-align:center">{q}</td></tr>' for t,q in info["tabelas"].items())}
  <tr style="background:#e0f2fe;font-weight:bold;"><td>TOTAL</td><td style="text-align:center">{info["total_registros"]}</td></tr>
</table>
<p style="color:#64748b;font-size:12px;margin-top:20px;">
O arquivo <strong>{nome_arquivo}</strong> está anexado a este e-mail.<br>
Este backup é gerado automaticamente às 06:00, 12:00 e 19:00 (horário de Brasília).
</p>
</body></html>
"""
        msg.attach(MIMEText(corpo, 'html'))

        # Anexa o zip
        parte = MIMEBase('application', 'zip')
        parte.set_payload(zip_bytes)
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', f'attachment; filename="{nome_arquivo}"')
        msg.attach(parte)

        # Envia via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_DESTINO, msg.as_string())

        print(f"✅ [BACKUP] E-mail enviado para {EMAIL_DESTINO} — {info['total_registros']} registros")

    except Exception as e:
        print(f"❌ [BACKUP] Erro ao enviar backup: {e}")
        traceback.print_exc()


def iniciar_scheduler(app):
    """
    Registra o job de backup no APScheduler.
    Chamado uma vez na inicialização do servidor.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler(timezone='America/Sao_Paulo')
        scheduler.add_job(
            func=enviar_backup_email,
            trigger=CronTrigger(hour='6,12,19', minute=0, timezone='America/Sao_Paulo'),
            id='backup_email',
            name='Backup DB por e-mail (06h / 12h / 19h)',
            replace_existing=True,
            misfire_grace_time=300,  # tolera até 5min de atraso
        )
        scheduler.start()
        print("✅ [BACKUP] Scheduler iniciado — backups às 06:00, 12:00 e 19:00 (Brasília)")
        return scheduler
    except ImportError:
        print("⚠️  [BACKUP] APScheduler não instalado — backups automáticos desativados")
        print("   Execute: pip install apscheduler")
        return None
    except Exception as e:
        print(f"⚠️  [BACKUP] Erro ao iniciar scheduler: {e}")
        return None

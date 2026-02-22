"""
Arquivo de configuração do sistema financeiro
"""
import os

# Escolha qual banco de dados usar
# Opções: 'sqlite', 'mysql', 'postgresql'
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

# Configurações do PostgreSQL (Railway)
POSTGRESQL_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'database': os.getenv('PGDATABASE', 'sistema_financeiro')
}

# Configurações do MySQL
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'sistema_financeiro'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Configurações do SQLite (padrão para desenvolvimento local)
SQLITE_DB_PATH = 'sistema_financeiro.db'

# =========================================
# GOOGLE CALENDAR API CONFIGURATION
# =========================================
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'https://sistemafinanceirodwm-production.up.railway.app/api/google-calendar/callback')

# Scopes necessários para Google Calendar
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]
# =========================================
# EMAIL/SMTP CONFIGURATION
# =========================================
# Configurações de e-mail para notificações
EMAIL_NOTIFICATIONS_ENABLED = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'False').lower() == 'true'

# Configurações SMTP (Gmail, Outlook, etc.)
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')  # Gmail por padrão
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
SMTP_USER = os.getenv('SMTP_USER', '')  # Seu e-mail
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Senha de app (Gmail) ou senha normal
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', SMTP_USER)
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'Sistema Financeiro DWM')

# Exemplos de configuração para diferentes provedores:
# Gmail:
#   SMTP_HOST = 'smtp.gmail.com'
#   SMTP_PORT = 587
#   SMTP_USE_TLS = True
#   SMTP_PASSWORD = 'senha de app gerada em https://myaccount.google.com/apppasswords'
#
# Outlook/Hotmail:
#   SMTP_HOST = 'smtp-mail.outlook.com'
#   SMTP_PORT = 587
#   SMTP_USE_TLS = True
#
# SendGrid:
#   SMTP_HOST = 'smtp.sendgrid.net'
#   SMTP_PORT = 587
#   SMTP_USER = 'apikey'
#   SMTP_PASSWORD = 'sua_api_key'
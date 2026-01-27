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

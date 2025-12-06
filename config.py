"""
Arquivo de configuração do sistema financeiro
"""

# Escolha qual banco de dados usar
USE_MYSQL = False  # True = MySQL, False = SQLite

# Configurações do MySQL (usado apenas se USE_MYSQL = True)
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # ← Configure sua senha aqui
    'database': 'sistema_financeiro',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Configurações do SQLite (usado apenas se USE_MYSQL = False)
SQLITE_DB_PATH = 'sistema_financeiro.db'

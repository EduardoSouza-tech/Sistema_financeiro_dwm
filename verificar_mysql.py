"""
Script de verificação da instalação e configuração do MySQL
"""
import sys

print("=== VERIFICAÇÃO DO MySQL ===\n")

# 1. Verificar se mysql-connector-python está instalado
print("1. Verificando mysql-connector-python...")
try:
    import mysql.connector
    print("   ✓ mysql-connector-python instalado")
    print(f"   Versão: {mysql.connector.__version__}")
except ImportError:
    print("   ✗ mysql-connector-python NÃO instalado")
    print("   Execute: pip install mysql-connector-python")
    sys.exit(1)

# 2. Ler configuração
print("\n2. Verificando configuração...")
try:
    from config import MYSQL_CONFIG
    print("   ✓ Arquivo config.py encontrado")
    print(f"   Host: {MYSQL_CONFIG['host']}")
    print(f"   Port: {MYSQL_CONFIG['port']}")
    print(f"   User: {MYSQL_CONFIG['user']}")
    print(f"   Database: {MYSQL_CONFIG['database']}")
    
    if not MYSQL_CONFIG['password']:
        print("   ⚠ ATENÇÃO: Senha não configurada!")
        print("   Edite config.py e adicione a senha do MySQL")
except Exception as e:
    print(f"   ✗ Erro ao ler config.py: {e}")
    sys.exit(1)

# 3. Testar conexão com MySQL (sem selecionar database)
print("\n3. Testando conexão com MySQL...")
try:
    conn = mysql.connector.connect(
        host=MYSQL_CONFIG['host'],
        port=MYSQL_CONFIG['port'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password']
    )
    print("   ✓ Conexão com MySQL estabelecida")
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"   MySQL versão: {version}")
    
    cursor.close()
    conn.close()
except mysql.connector.Error as e:
    print(f"   ✗ Erro ao conectar ao MySQL: {e}")
    print("\n   SOLUÇÕES:")
    print("   - Verifique se o MySQL está rodando")
    print("   - Verifique usuário e senha em config.py")
    print("   - Verifique se a porta 3306 está aberta")
    sys.exit(1)

# 4. Verificar/criar database
print("\n4. Verificando database...")
try:
    conn = mysql.connector.connect(
        host=MYSQL_CONFIG['host'],
        port=MYSQL_CONFIG['port'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password']
    )
    cursor = conn.cursor()
    
    # Criar database se não existir
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} CHARACTER SET {MYSQL_CONFIG['charset']} COLLATE {MYSQL_CONFIG['collation']}")
    print(f"   ✓ Database '{MYSQL_CONFIG['database']}' criado/verificado")
    
    # Conectar ao database
    cursor.execute(f"USE {MYSQL_CONFIG['database']}")
    
    # Listar tabelas
    cursor.execute("SHOW TABLES")
    tabelas = cursor.fetchall()
    
    if tabelas:
        print(f"   Tabelas existentes ({len(tabelas)}):")
        for tabela in tabelas:
            print(f"     - {tabela[0]}")
    else:
        print("   Nenhuma tabela encontrada (database vazio)")
    
    cursor.close()
    conn.close()
except mysql.connector.Error as e:
    print(f"   ✗ Erro ao verificar database: {e}")
    sys.exit(1)

# 5. Testar criação de tabelas
print("\n5. Testando criação de tabelas...")
try:
    from database_mysql import DatabaseManager
    
    db = DatabaseManager(MYSQL_CONFIG)
    print("   ✓ DatabaseManager inicializado")
    print("   ✓ Tabelas criadas/verificadas")
    
    # Verificar tabelas criadas
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tabelas = cursor.fetchall()
    
    print(f"\n   Tabelas no banco ({len(tabelas)}):")
    for tabela in tabelas:
        nome_tabela = tabela[0]
        cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
        count = cursor.fetchone()[0]
        print(f"     - {nome_tabela}: {count} registros")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ✗ Erro ao criar tabelas: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. Verificar se SQLite ainda existe
print("\n6. Verificando dados existentes...")
import os
if os.path.exists('sistema_financeiro.db'):
    print("   ✓ Banco SQLite encontrado: sistema_financeiro.db")
    print("   Você pode migrar os dados executando: python migrar_sqlite_para_mysql.py")
else:
    print("   ⚠ Banco SQLite não encontrado")
    print("   Começando com banco MySQL vazio")

print("\n=== VERIFICAÇÃO CONCLUÍDA COM SUCESSO ===")
print("\nPróximos passos:")
print("1. Se tem dados no SQLite, execute: python migrar_sqlite_para_mysql.py")
print("2. Configure USE_MYSQL = True em config.py")
print("3. Execute a aplicação: python app_gui.py")

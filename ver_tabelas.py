import sqlite3

conn = sqlite3.connect('financeiro.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = cursor.fetchall()
print("Tabelas no banco de dados:")
for tabela in tabelas:
    print(f"  - {tabela[0]}")
conn.close()

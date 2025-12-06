import sqlite3

conn = sqlite3.connect('sistema_financeiro.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM lancamentos')
rows = cursor.fetchall()

print(f'\nTotal de lançamentos no banco: {len(rows)}')
print('-' * 80)

for row in rows:
    print(row)

conn.close()

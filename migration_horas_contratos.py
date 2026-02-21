"""Migration: adiciona colunas horas_totais, horas_utilizadas, horas_extras, controle_horas_ativo à tabela contratos"""
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

sqls = [
    'ALTER TABLE contratos ADD COLUMN IF NOT EXISTS horas_totais NUMERIC DEFAULT 0',
    'ALTER TABLE contratos ADD COLUMN IF NOT EXISTS horas_utilizadas NUMERIC DEFAULT 0',
    'ALTER TABLE contratos ADD COLUMN IF NOT EXISTS horas_extras NUMERIC DEFAULT 0',
    'ALTER TABLE contratos ADD COLUMN IF NOT EXISTS controle_horas_ativo BOOLEAN DEFAULT FALSE',
]

for sql in sqls:
    cur.execute(sql)
    print(f'✅ OK: {sql}')

conn.commit()
cur.close()
conn.close()
print('\n✅ Migration concluída! Colunas adicionadas à tabela contratos.')

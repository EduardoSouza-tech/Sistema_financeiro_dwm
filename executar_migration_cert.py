#!/usr/bin/env python3
"""Executar migração de certificados NFS-e no Railway"""
import psycopg2

DATABASE_URL = 'postgresql://postgres:JhsyBdqwhkOJORFyZRtVgshWGZWQAIQT@centerbeam.proxy.rlwy.net:12659/railway'

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

with open('migration_nfse_certificado.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

cursor.execute(sql)
conn.commit()

cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'nfse_certificados' ORDER BY ordinal_position")
cols = cursor.fetchall()
print("Colunas da tabela nfse_certificados:")
for col in cols:
    print(f"  {col[0]}: {col[1]}")

cursor.close()
conn.close()
print("\nMigracao executada com sucesso!")

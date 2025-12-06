"""
Script para migrar dados do SQLite local para PostgreSQL do Railway
"""
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# URL do PostgreSQL do Railway - SUBSTITUA PELA SUA URL
DATABASE_URL = input("Cole a DATABASE_URL do Railway aqui: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL não fornecida!")
    exit(1)

print("\n" + "="*60)
print("MIGRAÇÃO SQLITE → POSTGRESQL (RAILWAY)")
print("="*60)

# Conectar ao SQLite local
print("\n📂 Conectando ao SQLite local...")
sqlite_conn = sqlite3.connect('sistema_financeiro.db')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# Conectar ao PostgreSQL do Railway
print("🐘 Conectando ao PostgreSQL do Railway...")
try:
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()
    print("✅ Conectado ao PostgreSQL!")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    exit(1)

# Função para migrar uma tabela
def migrar_tabela(nome_tabela, colunas, converter_booleano=None):
    print(f"\n📊 Migrando tabela: {nome_tabela}")
    
    # Buscar dados do SQLite
    sqlite_cursor.execute(f"SELECT * FROM {nome_tabela}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   ⚠️  Tabela {nome_tabela} está vazia")
        return
    
    print(f"   📦 {len(rows)} registros encontrados")
    
    # Inserir no PostgreSQL
    placeholders = ', '.join(['%s'] * len(colunas))
    cols = ', '.join(colunas)
    
    migrados = 0
    erros = 0
    
    for row in rows:
        try:
            valores = []
            for col in colunas:
                valor = row[col] if col in row.keys() else None
                
                # Converter inteiro para booleano se necessário
                if converter_booleano and col in converter_booleano:
                    valor = bool(valor) if valor is not None else None
                
                valores.append(valor)
            
            pg_cursor.execute(
                f"INSERT INTO {nome_tabela} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                valores
            )
            pg_conn.commit()  # Commit individual para evitar bloqueio
            migrados += 1
        except Exception as e:
            erros += 1
            pg_conn.rollback()  # Rollback apenas deste registro
            # print(f"   ⚠️  Erro ao migrar registro: {e}")
    
    print(f"   ✅ {migrados} registros migrados com sucesso")
    if erros > 0:
        print(f"   ❌ {erros} registros com erro (estrutura pode ser diferente)")

# Migrar Contas Bancárias
try:
    migrar_tabela('contas_bancarias', [
        'id', 'nome', 'banco', 'agencia', 'conta', 
        'saldo_inicial', 'ativa', 'data_criacao'
    ], converter_booleano=['ativa'])
except Exception as e:
    print(f"❌ Erro na migração de contas: {e}")

# Migrar Categorias
try:
    migrar_tabela('categorias', [
        'id', 'nome', 'tipo', 'subcategorias'
    ])
except Exception as e:
    print(f"❌ Erro na migração de categorias: {e}")

# Migrar Clientes
try:
    migrar_tabela('clientes', [
        'id', 'nome', 'cpf_cnpj', 'email', 'telefone', 'endereco', 'ativo'
    ], converter_booleano=['ativo'])
except Exception as e:
    print(f"❌ Erro na migração de clientes: {e}")

# Migrar Fornecedores
try:
    migrar_tabela('fornecedores', [
        'id', 'nome', 'cpf_cnpj', 'email', 'telefone', 'endereco', 'ativo'
    ], converter_booleano=['ativo'])
except Exception as e:
    print(f"❌ Erro na migração de fornecedores: {e}")

# Migrar Lançamentos
try:
    migrar_tabela('lancamentos', [
        'id', 'tipo', 'descricao', 'valor', 'data_vencimento', 
        'data_pagamento', 'categoria', 'subcategoria', 'conta_bancaria',
        'cliente_fornecedor', 'pessoa', 'status', 'observacoes', 
        'anexo', 'recorrente', 'frequencia_recorrencia', 'dia_vencimento'
    ], converter_booleano=['recorrente'])
except Exception as e:
    print(f"❌ Erro na migração de lançamentos: {e}")

# Fechar conexões
sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("\n" + "="*60)
print("✅ MIGRAÇÃO CONCLUÍDA!")
print("="*60)
print("\n🚀 Acesse seu sistema no Railway para verificar os dados!")

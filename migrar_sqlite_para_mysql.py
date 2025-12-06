"""
Script de migração de dados do SQLite para MySQL
"""
import sqlite3
import mysql.connector
from datetime import datetime
import json

# Configurações
SQLITE_DB = "sistema_financeiro.db"
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # Configure sua senha aqui
    'database': 'sistema_financeiro'
}

def migrar_dados():
    """Migra todos os dados do SQLite para MySQL"""
    
    print("=== INICIANDO MIGRAÇÃO SQLite → MySQL ===\n")
    
    # Conectar ao SQLite
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_conn.row_factory = sqlite3.Row
        print(f"✓ Conectado ao SQLite: {SQLITE_DB}")
    except Exception as e:
        print(f"✗ Erro ao conectar ao SQLite: {e}")
        return
    
    # Conectar ao MySQL
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        print(f"✓ Conectado ao MySQL: {MYSQL_CONFIG['database']}\n")
    except Exception as e:
        print(f"✗ Erro ao conectar ao MySQL: {e}")
        print("Verifique se o MySQL está rodando e as credenciais estão corretas")
        sqlite_conn.close()
        return
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    # === MIGRAR CONTAS BANCÁRIAS ===
    print("--- Migrando Contas Bancárias ---")
    try:
        sqlite_cursor.execute("SELECT * FROM contas_bancarias")
        contas = sqlite_cursor.fetchall()
        
        for conta in contas:
            mysql_cursor.execute("""
                INSERT INTO contas_bancarias 
                (nome, banco, agencia, conta, saldo_inicial, ativa, data_criacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                conta['nome'], conta['banco'], conta['agencia'], conta['conta'],
                float(conta['saldo_inicial']), conta['ativa'], conta['data_criacao']
            ))
        
        mysql_conn.commit()
        print(f"✓ {len(contas)} contas bancárias migradas")
    except Exception as e:
        print(f"✗ Erro ao migrar contas: {e}")
        mysql_conn.rollback()
    
    # === MIGRAR CATEGORIAS ===
    print("--- Migrando Categorias ---")
    try:
        sqlite_cursor.execute("SELECT * FROM categorias")
        categorias = sqlite_cursor.fetchall()
        
        for cat in categorias:
            mysql_cursor.execute("""
                INSERT INTO categorias 
                (nome, tipo, subcategorias)
                VALUES (%s, %s, %s)
            """, (cat['nome'], cat['tipo'], cat['subcategorias']))
        
        mysql_conn.commit()
        print(f"✓ {len(categorias)} categorias migradas")
    except Exception as e:
        print(f"✗ Erro ao migrar categorias: {e}")
        mysql_conn.rollback()
    
    # === MIGRAR CLIENTES ===
    print("--- Migrando Clientes ---")
    try:
        sqlite_cursor.execute("SELECT * FROM clientes")
        clientes = sqlite_cursor.fetchall()
        
        for cli in clientes:
            mysql_cursor.execute("""
                INSERT INTO clientes 
                (nome, razao_social, nome_fantasia, cnpj, ie, im, cep, rua, numero,
                 complemento, bairro, cidade, estado, telefone, contato, email, endereco, documento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cli['nome'], cli['razao_social'], cli['nome_fantasia'], cli['cnpj'],
                cli['ie'], cli['im'], cli['cep'], cli['rua'], cli['numero'],
                cli['complemento'], cli['bairro'], cli['cidade'], cli['estado'],
                cli['telefone'], cli['contato'], cli['email'], cli['endereco'], cli['documento']
            ))
        
        mysql_conn.commit()
        print(f"✓ {len(clientes)} clientes migrados")
    except Exception as e:
        print(f"✗ Erro ao migrar clientes: {e}")
        mysql_conn.rollback()
    
    # === MIGRAR FORNECEDORES ===
    print("--- Migrando Fornecedores ---")
    try:
        sqlite_cursor.execute("SELECT * FROM fornecedores")
        fornecedores = sqlite_cursor.fetchall()
        
        for forn in fornecedores:
            mysql_cursor.execute("""
                INSERT INTO fornecedores 
                (nome, razao_social, nome_fantasia, cnpj, ie, im, cep, rua, numero,
                 complemento, bairro, cidade, estado, telefone, contato, email, endereco, documento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                forn['nome'], forn['razao_social'], forn['nome_fantasia'], forn['cnpj'],
                forn['ie'], forn['im'], forn['cep'], forn['rua'], forn['numero'],
                forn['complemento'], forn['bairro'], forn['cidade'], forn['estado'],
                forn['telefone'], forn['contato'], forn['email'], forn['endereco'], forn['documento']
            ))
        
        mysql_conn.commit()
        print(f"✓ {len(fornecedores)} fornecedores migrados")
    except Exception as e:
        print(f"✗ Erro ao migrar fornecedores: {e}")
        mysql_conn.rollback()
    
    # === MIGRAR LANÇAMENTOS ===
    print("--- Migrando Lançamentos ---")
    try:
        sqlite_cursor.execute("SELECT * FROM lancamentos")
        lancamentos = sqlite_cursor.fetchall()
        
        for lanc in lancamentos:
            mysql_cursor.execute("""
                INSERT INTO lancamentos 
                (tipo, descricao, valor, data_vencimento, data_pagamento, status, categoria,
                 subcategoria, conta_bancaria, pessoa, observacoes, num_documento, recorrente,
                 frequencia_recorrencia, data_criacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lanc['tipo'], lanc['descricao'], float(lanc['valor']), lanc['data_vencimento'],
                lanc['data_pagamento'], lanc['status'], lanc['categoria'], lanc['subcategoria'],
                lanc['conta_bancaria'], lanc['pessoa'], lanc['observacoes'], lanc['num_documento'],
                lanc['recorrente'], lanc['frequencia_recorrencia'], lanc['data_criacao']
            ))
        
        mysql_conn.commit()
        print(f"✓ {len(lancamentos)} lançamentos migrados")
    except Exception as e:
        print(f"✗ Erro ao migrar lançamentos: {e}")
        mysql_conn.rollback()
    
    # Fechar conexões
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
    
    print("\n=== MIGRAÇÃO CONCLUÍDA ===")

if __name__ == "__main__":
    migrar_dados()

"""
Script para verificar e corrigir a estrutura do banco de dados
"""
import sqlite3
from datetime import datetime

def verificar_e_corrigir_db(db_path='sistema_financeiro.db'):
    """Verifica e corrige a estrutura do banco de dados"""
    
    print("=" * 70)
    print("VERIFICAÇÃO E CORREÇÃO DO BANCO DE DADOS")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()
    
    # 1. Verificar integridade
    print("\n1. Verificando integridade do banco...")
    cursor.execute("PRAGMA integrity_check")
    resultado = cursor.fetchone()[0]
    if resultado == "ok":
        print("   ✓ Integridade OK")
    else:
        print(f"   ✗ Problema de integridade: {resultado}")
    
    # 2. Listar tabelas existentes
    print("\n2. Tabelas existentes:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas_existentes = [row[0] for row in cursor.fetchall()]
    for tabela in tabelas_existentes:
        print(f"   - {tabela}")
    
    # 3. Verificar estrutura de cada tabela
    print("\n3. Verificando estrutura das tabelas:")
    
    tabelas_esperadas = {
        'contas_bancarias': [
            'id', 'nome', 'banco', 'agencia', 'conta', 
            'saldo_inicial', 'ativa', 'data_criacao'
        ],
        'categorias': [
            'id', 'nome', 'tipo', 'subcategorias'
        ],
        'clientes': [
            'id', 'nome', 'razao_social', 'nome_fantasia', 'cnpj', 'ie', 'im',
            'cep', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
            'telefone', 'contato', 'email', 'endereco', 'documento'
        ],
        'fornecedores': [
            'id', 'nome', 'razao_social', 'nome_fantasia', 'cnpj', 'ie', 'im',
            'cep', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
            'telefone', 'contato', 'email', 'endereco', 'documento'
        ],
        'lancamentos': [
            'id', 'tipo', 'descricao', 'valor', 'data_vencimento', 'data_pagamento',
            'status', 'categoria', 'subcategoria', 'conta_bancaria', 'pessoa',
            'observacoes', 'num_documento', 'recorrente', 'frequencia_recorrencia',
            'data_criacao'
        ]
    }
    
    for tabela, colunas_esperadas in tabelas_esperadas.items():
        if tabela in tabelas_existentes:
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas_existentes = [row[1] for row in cursor.fetchall()]
            
            print(f"\n   Tabela '{tabela}':")
            print(f"      Colunas esperadas: {len(colunas_esperadas)}")
            print(f"      Colunas existentes: {len(colunas_existentes)}")
            
            # Verificar colunas faltando
            faltando = set(colunas_esperadas) - set(colunas_existentes)
            if faltando:
                print(f"      ⚠ Colunas faltando: {', '.join(faltando)}")
                
                # Adicionar colunas faltando
                for coluna in faltando:
                    tipo_coluna = 'TEXT'
                    if coluna in ['id', 'ativa', 'recorrente']:
                        tipo_coluna = 'INTEGER'
                    elif coluna in ['valor', 'saldo_inicial']:
                        tipo_coluna = 'REAL'
                    
                    try:
                        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo_coluna}")
                        print(f"         ✓ Coluna '{coluna}' adicionada")
                    except Exception as e:
                        print(f"         ✗ Erro ao adicionar '{coluna}': {e}")
            else:
                print(f"      ✓ Todas as colunas presentes")
            
            # Verificar colunas extras
            extras = set(colunas_existentes) - set(colunas_esperadas)
            if extras:
                print(f"      ℹ Colunas extras: {', '.join(extras)}")
        else:
            print(f"\n   ⚠ Tabela '{tabela}' não existe! Criando...")
            criar_tabela(cursor, tabela)
    
    # 4. Verificar dados
    print("\n4. Resumo dos dados:")
    for tabela in tabelas_existentes:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"   - {tabela}: {count} registros")
        except Exception as e:
            print(f"   - {tabela}: Erro ao contar registros - {e}")
    
    # 5. Otimizar banco
    print("\n5. Otimizando banco de dados...")
    try:
        cursor.execute("VACUUM")
        print("   ✓ VACUUM executado")
    except Exception as e:
        print(f"   ⚠ Erro no VACUUM: {e}")
    
    try:
        cursor.execute("ANALYZE")
        print("   ✓ ANALYZE executado")
    except Exception as e:
        print(f"   ⚠ Erro no ANALYZE: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 70)

def criar_tabela(cursor, nome_tabela):
    """Cria uma tabela que está faltando"""
    
    sqls = {
        'contas_bancarias': """
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                banco TEXT NOT NULL,
                agencia TEXT NOT NULL,
                conta TEXT NOT NULL,
                saldo_inicial REAL NOT NULL,
                ativa INTEGER DEFAULT 1,
                data_criacao TEXT NOT NULL
            )
        """,
        'categorias': """
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL,
                subcategorias TEXT
            )
        """,
        'clientes': """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                razao_social TEXT,
                nome_fantasia TEXT,
                cnpj TEXT,
                ie TEXT,
                im TEXT,
                cep TEXT,
                rua TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                estado TEXT,
                telefone TEXT,
                contato TEXT,
                email TEXT,
                endereco TEXT,
                documento TEXT
            )
        """,
        'fornecedores': """
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                razao_social TEXT,
                nome_fantasia TEXT,
                cnpj TEXT,
                ie TEXT,
                im TEXT,
                cep TEXT,
                rua TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                estado TEXT,
                telefone TEXT,
                contato TEXT,
                email TEXT,
                endereco TEXT,
                documento TEXT
            )
        """,
        'lancamentos': """
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data_vencimento TEXT NOT NULL,
                data_pagamento TEXT,
                status TEXT NOT NULL,
                categoria TEXT,
                subcategoria TEXT,
                conta_bancaria TEXT,
                pessoa TEXT,
                observacoes TEXT,
                num_documento TEXT,
                recorrente INTEGER DEFAULT 0,
                frequencia_recorrencia TEXT,
                data_criacao TEXT NOT NULL
            )
        """
    }
    
    if nome_tabela in sqls:
        try:
            cursor.execute(sqls[nome_tabela])
            print(f"      ✓ Tabela '{nome_tabela}' criada")
        except Exception as e:
            print(f"      ✗ Erro ao criar tabela: {e}")

if __name__ == '__main__':
    verificar_e_corrigir_db()
    print("\nPressione Enter para sair...")
    input()

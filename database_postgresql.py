"""
Módulo de gerenciamento do banco de dados PostgreSQL
"""
import psycopg2  # type: ignore
from psycopg2 import Error, sql  # type: ignore
from psycopg2.extras import RealDictCursor  # type: ignore
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
import json
import os
from models import (
    ContaBancaria, Lancamento, Categoria,
    TipoLancamento, StatusLancamento
)

__all__ = [
    'criar_tabelas',
    'get_connection',
    'adicionar_conta',
    'listar_contas',
    'excluir_conta',
    'adicionar_categoria',
    'listar_categorias',
    'excluir_categoria',
    'atualizar_categoria',
    'atualizar_nome_categoria',
    'adicionar_cliente',
    'listar_clientes',
    'adicionar_fornecedor',
    'listar_fornecedores',
    'adicionar_lancamento',
    'listar_lancamentos',
    'excluir_lancamento',
    'pagar_lancamento',
    'cancelar_lancamento',
    'migrar_dados_json',
    'obter_lancamento',
    'atualizar_cliente',
    'atualizar_fornecedor',
    # Novas funções do menu Operacional
    'adicionar_contrato',
    'listar_contratos',
    'atualizar_contrato',
    'deletar_contrato',
    'adicionar_agenda',
    'listar_agenda',
    'atualizar_agenda',
    'deletar_agenda',
    'adicionar_produto',
    'listar_produtos',
    'atualizar_produto',
    'deletar_produto',
    'adicionar_kit',
    'listar_kits',
    'atualizar_kit',
    'deletar_kit',
    'adicionar_tag',
    'listar_tags',
    'atualizar_tag',
    'deletar_tag',
    'adicionar_template',
    'listar_templates_equipe',
    'atualizar_template',
    'deletar_template',
    'adicionar_sessao',
    'listar_sessoes',
    'atualizar_sessao',
    'deletar_sessao',
    'adicionar_comissao',
    'listar_comissoes',
    'atualizar_comissao',
    'deletar_comissao',
    'adicionar_sessao_equipe',
    'listar_sessao_equipe',
    'atualizar_sessao_equipe',
    'deletar_sessao_equipe',
    'adicionar_tipo_sessao',
    'listar_tipos_sessao',
    'atualizar_tipo_sessao',
    'deletar_tipo_sessao'
]

# Configurações do PostgreSQL (Railway fornece via variáveis de ambiente)
# Suporta DATABASE_URL ou variáveis individuais
def _get_postgresql_config():
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Usar DATABASE_URL se disponível (Railway fornece automaticamente)
        return {'dsn': database_url}
    else:
        # Fallback para variáveis individuais
        return {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': int(os.getenv('PGPORT', '5432')),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', ''),
            'database': os.getenv('PGDATABASE', 'sistema_financeiro')
        }

POSTGRESQL_CONFIG = _get_postgresql_config()


class DatabaseManager:
    """Gerenciador do banco de dados PostgreSQL"""
    
    def __init__(self, config: Dict = None):
        self.config = config or POSTGRESQL_CONFIG
        self.criar_tabelas()
    
    def get_connection(self):
        """Cria uma conexão com o banco de dados"""
        try:
            if 'dsn' in self.config:
                # Conectar usando DATABASE_URL
                conn = psycopg2.connect(self.config['dsn'], cursor_factory=RealDictCursor)
            else:
                # Conectar usando variáveis individuais
                conn = psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
            
            conn.autocommit = True
            return conn
        except Error as e:
            print(f"Erro ao conectar ao PostgreSQL: {e}")
            print(f"Config: {self.config if 'dsn' not in self.config else 'usando DATABASE_URL'}")
            raise
    
    def criar_tabelas(self):
        """Cria as tabelas no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de contas bancárias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                banco VARCHAR(255) NOT NULL,
                agencia VARCHAR(50) NOT NULL,
                conta VARCHAR(50) NOT NULL,
                saldo_inicial DECIMAL(15,2) NOT NULL,
                ativa BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                subcategorias TEXT,
                cor VARCHAR(7),
                icone VARCHAR(50),
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf_cnpj VARCHAR(18) UNIQUE,
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de fornecedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf_cnpj VARCHAR(18) UNIQUE,
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de lançamentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                descricao TEXT NOT NULL,
                valor DECIMAL(15,2) NOT NULL,
                data_vencimento DATE NOT NULL,
                data_pagamento DATE,
                categoria VARCHAR(255),
                subcategoria VARCHAR(255),
                conta_bancaria VARCHAR(255),
                cliente_fornecedor VARCHAR(255),
                pessoa VARCHAR(255),
                status VARCHAR(50) NOT NULL,
                observacoes TEXT,
                anexo TEXT,
                recorrente BOOLEAN DEFAULT FALSE,
                frequencia_recorrencia VARCHAR(50),
                dia_vencimento INTEGER,
                juros DECIMAL(15,2) DEFAULT 0,
                desconto DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar colunas juros e desconto se não existirem (migration)
        try:
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='lancamentos' AND column_name='juros'
                    ) THEN
                        ALTER TABLE lancamentos ADD COLUMN juros DECIMAL(15,2) DEFAULT 0;
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='lancamentos' AND column_name='desconto'
                    ) THEN
                        ALTER TABLE lancamentos ADD COLUMN desconto DECIMAL(15,2) DEFAULT 0;
                    END IF;
                END $$;
            """)
            print("✅ Migração: Colunas juros e desconto adicionadas/verificadas")
        except Exception as e:
            print(f"⚠️  Aviso na migração de colunas: {e}")
        
        # Sincronizar sequências de auto-incremento com valores máximos atuais
        try:
            cursor.execute("""
                DO $$ 
                DECLARE
                    max_id INTEGER;
                BEGIN
                    -- Sincronizar sequência de categorias
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM categorias;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''categorias_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de contas_bancarias
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM contas_bancarias;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''contas_bancarias_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de clientes
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM clientes;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''clientes_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de fornecedores
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM fornecedores;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''fornecedores_id_seq'', ' || max_id || ')';
                    END IF;
                    
                    -- Sincronizar sequência de lancamentos
                    SELECT COALESCE(MAX(id), 0) INTO max_id FROM lancamentos;
                    IF max_id > 0 THEN
                        EXECUTE 'SELECT setval(''lancamentos_id_seq'', ' || max_id || ')';
                    END IF;
                END $$;
            """)
            print("✅ Migração: Sequências de ID sincronizadas com sucesso")
        except Exception as e:
            print(f"⚠️  Aviso na sincronização de sequências: {e}")
        
        # Tabela de contratos
        # Primeiro, dropar tabela antiga se existir com estrutura incompatível
        try:
            cursor.execute("""
                DO $$ 
                BEGIN
                    -- Verificar se existe coluna numero_nf (estrutura antiga)
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='contratos' AND column_name='numero_nf'
                    ) THEN
                        -- Dropar tabela antiga
                        DROP TABLE IF EXISTS contratos CASCADE;
                    END IF;
                END $$;
            """)
        except Exception as e:
            print(f"⚠️  Aviso ao verificar tabela contratos: {e}")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratos (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(100) UNIQUE NOT NULL,
                cliente_id INTEGER REFERENCES clientes(id),
                descricao TEXT NOT NULL,
                valor DECIMAL(15,2) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE,
                status VARCHAR(50) DEFAULT 'ativo',
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de agenda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                data_evento DATE NOT NULL,
                hora_inicio TIME,
                hora_fim TIME,
                local VARCHAR(255),
                tipo VARCHAR(50),
                status VARCHAR(50) DEFAULT 'agendado',
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(100) UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                categoria VARCHAR(100),
                quantidade DECIMAL(15,3) DEFAULT 0,
                preco_custo DECIMAL(15,2),
                preco_venda DECIMAL(15,2),
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de kits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kits (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(100) UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                preco DECIMAL(15,2) NOT NULL,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de itens dos kits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kit_itens (
                id SERIAL PRIMARY KEY,
                kit_id INTEGER REFERENCES kits(id) ON DELETE CASCADE,
                produto_id INTEGER REFERENCES produtos(id),
                quantidade DECIMAL(15,3) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de tags
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) UNIQUE NOT NULL,
                cor VARCHAR(7) DEFAULT '#007bff',
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de templates de equipe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates_equipe (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                tipo VARCHAR(50),
                conteudo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de sessões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                data_sessao DATE NOT NULL,
                duracao INTEGER,
                contrato_id INTEGER REFERENCES contratos(id),
                cliente_id INTEGER REFERENCES clientes(id),
                valor DECIMAL(15,2),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar coluna contrato_id se não existir
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='contrato_id'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN contrato_id INTEGER REFERENCES contratos(id);
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em sessoes
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar titulo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='titulo'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN titulo VARCHAR(255) NOT NULL DEFAULT 'Sessão';
                END IF;
                
                -- Adicionar data_sessao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='data_sessao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN data_sessao DATE NOT NULL DEFAULT CURRENT_DATE;
                END IF;
                
                -- Adicionar duracao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='duracao'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN duracao INTEGER;
                END IF;
                
                -- Adicionar cliente_id se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='cliente_id'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN cliente_id INTEGER REFERENCES clientes(id);
                END IF;
                
                -- Adicionar valor se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='valor'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN valor DECIMAL(15,2);
                END IF;
                
                -- Adicionar observacoes se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='observacoes'
                ) THEN
                    ALTER TABLE sessoes ADD COLUMN observacoes TEXT;
                END IF;
                
                -- Alterar horario para aceitar NULL se existir
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='sessoes' AND column_name='horario'
                ) THEN
                    ALTER TABLE sessoes ALTER COLUMN horario DROP NOT NULL;
                END IF;
            END $$;
        """)
        
        # Tabela de tipos de sessão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_sessao (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                descricao TEXT,
                duracao_padrao INTEGER,
                valor_padrao DECIMAL(15,2),
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migração: Adicionar colunas que podem faltar em tipos_sessao
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='descricao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar duracao_padrao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='duracao_padrao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN duracao_padrao INTEGER;
                END IF;
                
                -- Adicionar valor_padrao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='valor_padrao'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN valor_padrao DECIMAL(15,2);
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='ativo'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar created_at se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='created_at'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
                
                -- Adicionar updated_at se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tipos_sessao' AND column_name='updated_at'
                ) THEN
                    ALTER TABLE tipos_sessao ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em produtos
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='descricao'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar unidade se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='unidade'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN unidade VARCHAR(20) DEFAULT 'UN';
                END IF;
                
                -- Adicionar quantidade_minima se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='quantidade_minima'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN quantidade_minima DECIMAL(15,3) DEFAULT 0;
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='ativo'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em kits
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='descricao'
                ) THEN
                    ALTER TABLE kits ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='ativo'
                ) THEN
                    ALTER TABLE kits ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='kits' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE kits ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em tags
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar data_criacao se não existir  
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='tags' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE tags ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Migração: Adicionar colunas que podem faltar em templates_equipe
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Adicionar conteudo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='conteudo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN conteudo TEXT;
                END IF;
                
                -- Adicionar tipo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='tipo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN tipo VARCHAR(50);
                END IF;
                
                -- Adicionar descricao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='descricao'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN descricao TEXT;
                END IF;
                
                -- Adicionar ativo se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='ativo'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN ativo BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Adicionar data_criacao se não existir
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='templates_equipe' AND column_name='data_criacao'
                ) THEN
                    ALTER TABLE templates_equipe ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """)
        
        # Tabela de comissões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comissoes (
                id SERIAL PRIMARY KEY,
                contrato_id INTEGER REFERENCES contratos(id) ON DELETE CASCADE,
                cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE,
                tipo VARCHAR(50) DEFAULT 'percentual',
                descricao TEXT,
                valor DECIMAL(15,2) DEFAULT 0,
                percentual DECIMAL(5,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migração: adicionar campos faltantes em comissoes
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='comissoes' AND column_name='contrato_id') THEN
                    ALTER TABLE comissoes ADD COLUMN contrato_id INTEGER REFERENCES contratos(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='comissoes' AND column_name='cliente_id') THEN
                    ALTER TABLE comissoes ADD COLUMN cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='comissoes' AND column_name='tipo') THEN
                    ALTER TABLE comissoes ADD COLUMN tipo VARCHAR(50) DEFAULT 'percentual';
                END IF;
            END $$;
        """)
        
        # Migração: tornar campos nullable em comissoes
        cursor.execute("""
            DO $$
            BEGIN
                ALTER TABLE comissoes ALTER COLUMN descricao DROP NOT NULL;
                ALTER TABLE comissoes ALTER COLUMN valor DROP NOT NULL;
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END $$;
        """)
        
        # Tabela de equipe de sessão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessao_equipe (
                id SERIAL PRIMARY KEY,
                sessao_id INTEGER NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
                membro_nome VARCHAR(255) NOT NULL,
                funcao VARCHAR(100),
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.close()
        conn.close()
    
    def adicionar_conta(self, conta: ContaBancaria) -> int:
        """Adiciona uma nova conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contas_bancarias 
            (nome, banco, agencia, conta, saldo_inicial, ativa, data_criacao)
            VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
            RETURNING id
        """, (
            conta.nome,
            conta.banco,
            conta.agencia,
            conta.conta,
            float(conta.saldo_inicial),
            conta.ativa,
            conta.data_criacao
        ))
        
        conta_id = cursor.fetchone()['id']
        cursor.close()
        conn.close()
        return conta_id
    
    def listar_contas(self) -> List[ContaBancaria]:
        """Lista todas as contas bancárias"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM contas_bancarias ORDER BY nome")
        rows = cursor.fetchall()
        
        contas = []
        for row in rows:
            conta = ContaBancaria(
                id=row['id'],
                nome=row['nome'],
                banco=row['banco'],
                agencia=row['agencia'],
                conta=row['conta'],
                saldo_inicial=Decimal(str(row['saldo_inicial'])),
                ativa=row['ativa'],
                data_criacao=row['data_criacao']
            )
            contas.append(conta)
        
        cursor.close()
        conn.close()
        return contas
    
    def atualizar_conta(self, nome_antigo: str, conta: ContaBancaria) -> bool:
        """Atualiza uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se o nome mudou, verificar se o novo nome já existe
        if nome_antigo != conta.nome:
            cursor.execute("SELECT COUNT(*) FROM contas_bancarias WHERE nome = %s AND nome != %s", 
                         (conta.nome, nome_antigo))
            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                raise ValueError("Já existe uma conta com este nome")
        
        cursor.execute("""
            UPDATE contas_bancarias
            SET nome = %s, banco = %s, agencia = %s, conta = %s, saldo_inicial = %s
            WHERE nome = %s
        """, (conta.nome, conta.banco, conta.agencia, conta.conta,
              float(conta.saldo_inicial), nome_antigo))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    def excluir_conta(self, nome: str) -> bool:
        """Exclui uma conta bancária pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM contas_bancarias WHERE nome = %s", (nome,))
        sucesso = cursor.rowcount > 0
        
        conn.commit()
        cursor.close()
        conn.close()
        return sucesso
    
    def adicionar_categoria(self, categoria: Categoria) -> int:
        """Adiciona uma nova categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
        
        cursor.execute("""
            INSERT INTO categorias 
            (nome, tipo, subcategorias, cor, icone, descricao)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            categoria.nome,
            categoria.tipo.value,
            subcategorias_json,
            categoria.cor,
            categoria.icone,
            categoria.descricao
        ))
        
        categoria_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return categoria_id
    
    def listar_categorias(self, tipo: Optional[TipoLancamento] = None) -> List[Categoria]:
        """Lista todas as categorias, opcionalmente filtradas por tipo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if tipo:
            cursor.execute(
                "SELECT * FROM categorias WHERE tipo = %s ORDER BY nome",
                (tipo.value,)
            )
        else:
            cursor.execute("SELECT * FROM categorias ORDER BY nome")
        
        rows = cursor.fetchall()
        
        categorias = []
        for row in rows:
            subcategorias = json.loads(row['subcategorias']) if row['subcategorias'] else []  # type: ignore
            
            categoria = Categoria(
                id=row['id'],
                nome=row['nome'],
                tipo=TipoLancamento(row['tipo']),
                subcategorias=subcategorias,
                cor=row['cor'],
                icone=row['icone'],
                descricao=row['descricao']
            )
            categorias.append(categoria)
        
        cursor.close()
        conn.close()
        return categorias
    
    def excluir_categoria(self, nome: str) -> bool:
        """Exclui uma categoria pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Normalizar nome
        nome_normalizado = nome.upper().strip()
        cursor.execute("DELETE FROM categorias WHERE UPPER(TRIM(nome)) = %s", (nome_normalizado,))
        sucesso = cursor.rowcount > 0
        conn.commit()
        
        cursor.close()
        conn.close()
        return sucesso
    
    def atualizar_categoria(self, categoria: Categoria) -> bool:
        """Atualiza uma categoria pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
        
        # Normalizar nome
        nome_normalizado = categoria.nome.strip().upper()
        
        cursor.execute("""
            UPDATE categorias 
            SET tipo = %s, subcategorias = %s
            WHERE UPPER(TRIM(nome)) = %s
        """, (
            categoria.tipo.value,
            subcategorias_json,
            nome_normalizado
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return sucesso
    
    def atualizar_nome_categoria(self, nome_antigo: str, nome_novo: str) -> bool:
        """Atualiza o nome de uma categoria e suas referências"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Atualizar nome da categoria
            cursor.execute(
                "UPDATE categorias SET nome = %s WHERE nome = %s",
                (nome_novo, nome_antigo)
            )
            
            # Atualizar referências nos lançamentos
            cursor.execute(
                "UPDATE lancamentos SET categoria = %s WHERE categoria = %s",
                (nome_novo, nome_antigo)
            )
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar categoria: {e}")
            cursor.close()
            conn.close()
            return False
    
    def adicionar_cliente(self, cliente_data, cpf_cnpj: str = None, 
                         email: str = None, telefone: str = None,
                         endereco: str = None) -> int:
        """Adiciona um novo cliente (aceita dict ou parâmetros individuais)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Aceitar dict ou parâmetros individuais
        if isinstance(cliente_data, dict):
            nome = cliente_data.get('nome')
            cpf_cnpj = cliente_data.get('cpf', cliente_data.get('cpf_cnpj'))
            email = cliente_data.get('email')
            telefone = cliente_data.get('telefone')
            endereco = cliente_data.get('endereco')
        else:
            nome = cliente_data
        
        cursor.execute("""
            INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (nome, cpf_cnpj, email, telefone, endereco))
        
        cliente_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return cliente_id
    
    def listar_clientes(self, ativos: bool = True) -> List[Dict]:
        """Lista todos os clientes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if ativos:
            cursor.execute("SELECT * FROM clientes WHERE ativo = TRUE ORDER BY nome")
        else:
            cursor.execute("SELECT * FROM clientes ORDER BY nome")
        rows = cursor.fetchall()
        
        clientes = [dict(row) for row in rows]
        cursor.close()
        conn.close()
        return clientes
    
    def atualizar_cliente(self, nome_antigo: str, dados: Dict) -> bool:
        """Atualiza os dados de um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome_antigo.upper().strip()
        cursor.execute("""
            UPDATE clientes 
            SET nome = %s, cpf_cnpj = %s, email = %s, 
                telefone = %s, endereco = %s, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (
            dados.get('nome'),
            dados.get('cpf', dados.get('cpf_cnpj')),
            dados.get('email'),
            dados.get('telefone'),
            dados.get('endereco'),
            nome_normalizado
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return sucesso
    
    def inativar_cliente(self, nome: str, motivo: str = "") -> tuple[bool, str]:
        """Inativa um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE clientes 
            SET ativo = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return (sucesso, "Cliente inativado com sucesso" if sucesso else "Cliente não encontrado")
    
    def reativar_cliente(self, nome: str) -> bool:
        """Reativa um cliente pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE clientes 
            SET ativo = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return sucesso
    
    def adicionar_fornecedor(self, fornecedor_data, cpf_cnpj: str = None,
                           email: str = None, telefone: str = None,
                           endereco: str = None) -> int:
        """Adiciona um novo fornecedor (aceita dict ou parâmetros individuais)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Aceitar dict ou parâmetros individuais
        if isinstance(fornecedor_data, dict):
            nome = fornecedor_data.get('nome')
            cpf_cnpj = fornecedor_data.get('cnpj', fornecedor_data.get('cpf_cnpj'))
            email = fornecedor_data.get('email')
            telefone = fornecedor_data.get('telefone')
            endereco = fornecedor_data.get('endereco')
        else:
            nome = fornecedor_data
        
        cursor.execute("""
            INSERT INTO fornecedores (nome, cpf_cnpj, email, telefone, endereco)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (nome, cpf_cnpj, email, telefone, endereco))
        
        fornecedor_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        return fornecedor_id
    
    def listar_fornecedores(self, ativos: bool = True) -> List[Dict]:
        """Lista todos os fornecedores"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if ativos:
            cursor.execute("SELECT * FROM fornecedores WHERE ativo = TRUE ORDER BY nome")
        else:
            cursor.execute("SELECT * FROM fornecedores ORDER BY nome")
        rows = cursor.fetchall()
        
        fornecedores = [dict(row) for row in rows]
        cursor.close()
        conn.close()
        return fornecedores
    
    def atualizar_fornecedor(self, nome_antigo: str, dados: Dict) -> bool:
        """Atualiza os dados de um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome_antigo.upper().strip()
        cursor.execute("""
            UPDATE fornecedores 
            SET nome = %s, cpf_cnpj = %s, email = %s, 
                telefone = %s, endereco = %s, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (
            dados.get('nome'),
            dados.get('cnpj', dados.get('cpf_cnpj')),
            dados.get('email'),
            dados.get('telefone'),
            dados.get('endereco'),
            nome_normalizado
        ))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return sucesso
    
    def inativar_fornecedor(self, nome: str, motivo: str = "") -> tuple[bool, str]:
        """Inativa um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE fornecedores 
            SET ativo = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return (sucesso, "Fornecedor inativado com sucesso" if sucesso else "Fornecedor não encontrado")
    
    def reativar_fornecedor(self, nome: str) -> bool:
        """Reativa um fornecedor pelo nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        nome_normalizado = nome.upper().strip()
        cursor.execute("""
            UPDATE fornecedores 
            SET ativo = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE UPPER(TRIM(nome)) = %s
        """, (nome_normalizado,))
        
        sucesso = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return sucesso
    
    def adicionar_lancamento(self, lancamento: Lancamento) -> int:
        """Adiciona um novo lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO lancamentos 
            (tipo, descricao, valor, data_vencimento, data_pagamento,
             categoria, subcategoria, conta_bancaria, cliente_fornecedor, pessoa,
             status, observacoes, anexo, recorrente, frequencia_recorrencia, dia_vencimento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            lancamento.tipo.value,
            lancamento.descricao,
            float(lancamento.valor),
            lancamento.data_vencimento,
            lancamento.data_pagamento,
            lancamento.categoria,
            lancamento.subcategoria,
            lancamento.conta_bancaria,
            lancamento.cliente_fornecedor,
            lancamento.pessoa,
            lancamento.status.value,
            lancamento.observacoes,
            lancamento.anexo,
            lancamento.recorrente,
            lancamento.frequencia_recorrencia,
            lancamento.dia_vencimento
        ))
        
        lancamento_id = cursor.fetchone()['id']
        cursor.close()
        conn.close()
        return lancamento_id
    
    def listar_lancamentos(self, filtros: Dict[str, Any] = None) -> List[Lancamento]:
        """Lista lançamentos com filtros opcionais"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM lancamentos WHERE 1=1"
        params = []
        
        if filtros:
            if 'tipo' in filtros:
                query += " AND tipo = %s"
                params.append(filtros['tipo'])
            if 'status' in filtros:
                query += " AND status = %s"
                params.append(filtros['status'])
            if 'data_inicio' in filtros:
                query += " AND data_vencimento >= %s"
                params.append(filtros['data_inicio'])
            if 'data_fim' in filtros:
                query += " AND data_vencimento <= %s"
                params.append(filtros['data_fim'])
            if 'categoria' in filtros:
                query += " AND categoria = %s"
                params.append(filtros['categoria'])
            if 'conta_bancaria' in filtros:
                query += " AND conta_bancaria = %s"
                params.append(filtros['conta_bancaria'])
        
        query += " ORDER BY data_vencimento DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        lancamentos = []
        for row in rows:
            try:
                # Tratar valores que podem ser None
                tipo_value = row['tipo'].lower() if row['tipo'] else 'receita'
                status_value = row['status'].lower() if row['status'] else 'pendente'
                
                lancamento = Lancamento(
                    id=row['id'],
                    tipo=TipoLancamento(tipo_value),
                    descricao=row['descricao'],
                    valor=Decimal(str(row['valor'])),
                    data_vencimento=row['data_vencimento'],
                    data_pagamento=row['data_pagamento'],
                    categoria=row['categoria'] or '',
                    subcategoria=row['subcategoria'] or '',
                    conta_bancaria=row['conta_bancaria'] or '',
                    cliente_fornecedor=row['cliente_fornecedor'] or '',
                    pessoa=row['pessoa'] or '',
                    status=StatusLancamento(status_value),
                    observacoes=row['observacoes'] or '',
                    anexo=row['anexo'] or '',
                    recorrente=row['recorrente'] or False,
                    frequencia_recorrencia=row['frequencia_recorrencia'] or '',
                    dia_vencimento=row['dia_vencimento'] or 0
                )
                lancamentos.append(lancamento)
            except Exception as e:
                print(f"❌ Erro ao processar lançamento ID {row.get('id', 'unknown')}: {e}")
                continue
        
        cursor.close()
        conn.close()
        return lancamentos
    
    def obter_lancamento(self, lancamento_id: int) -> Optional[Lancamento]:
        """Obtém um lançamento específico por ID"""
        print(f"\n🔍 obter_lancamento() chamado com ID: {lancamento_id}")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM lancamentos WHERE id = %s"
        print(f"📝 Query: {query}")
        print(f"📝 Params: ({lancamento_id},)")
        
        try:
            cursor.execute(query, (lancamento_id,))
            row = cursor.fetchone()
            print(f"✅ Row encontrada: {row is not None}")
        except Exception as e:
            print(f"❌ ERRO ao executar query: {e}")
            cursor.close()
            conn.close()
            raise
        
        if not row:
            cursor.close()
            conn.close()
            return None
        
        # Tratar valores que podem ser None
        tipo_value = row['tipo'].lower() if row['tipo'] else 'receita'
        status_value = row['status'].lower() if row['status'] else 'pendente'
        
        print(f"📊 Construindo Lancamento com:")
        print(f"   - juros: {row.get('juros', 0)}")
        print(f"   - desconto: {row.get('desconto', 0)}")
        
        lancamento = Lancamento(
            id=row['id'],
            tipo=TipoLancamento(tipo_value),
            descricao=row['descricao'],
            valor=Decimal(str(row['valor'])),
            data_vencimento=row['data_vencimento'],
            data_pagamento=row['data_pagamento'],
            categoria=row['categoria'] or '',
            subcategoria=row['subcategoria'] or '',
            conta_bancaria=row['conta_bancaria'] or '',
            cliente_fornecedor=row['cliente_fornecedor'] or '',
            pessoa=row['pessoa'] or '',
            status=StatusLancamento(status_value),
            observacoes=row['observacoes'] or '',
            anexo=row['anexo'] or '',
            recorrente=row['recorrente'] or False,
            frequencia_recorrencia=row['frequencia_recorrencia'] or '',
            dia_vencimento=row['dia_vencimento'] or 0,
            juros=float(row.get('juros', 0)) if row.get('juros') is not None else 0,
            desconto=float(row.get('desconto', 0)) if row.get('desconto') is not None else 0
        )
        
        print(f"✅ Lancamento criado com sucesso\n")
        cursor.close()
        conn.close()
        return lancamento
    
    def excluir_lancamento(self, lancamento_id: int) -> bool:
        """Exclui um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento_id,))
        sucesso = cursor.rowcount > 0
        
        cursor.close()
        conn.close()
        return sucesso
    
    def atualizar_lancamento(self, lancamento: Lancamento) -> bool:
        """Atualiza um lançamento existente"""
        print(f"\n🔍 DatabaseManager.atualizar_lancamento() chamada:")
        print(f"   ID: {lancamento.id}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE lancamentos 
            SET tipo = %s, descricao = %s, valor = %s, data_vencimento = %s,
                data_pagamento = %s, categoria = %s, subcategoria = %s,
                conta_bancaria = %s, cliente_fornecedor = %s, pessoa = %s,
                status = %s, observacoes = %s, anexo = %s,
                recorrente = %s, frequencia_recorrencia = %s, dia_vencimento = %s,
                juros = %s, desconto = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        params = (
            lancamento.tipo.value if hasattr(lancamento.tipo, 'value') else str(lancamento.tipo),
            lancamento.descricao,
            float(lancamento.valor),
            lancamento.data_vencimento,
            lancamento.data_pagamento,
            lancamento.categoria,
            lancamento.subcategoria,
            lancamento.conta_bancaria or '',
            lancamento.cliente_fornecedor or '',
            lancamento.pessoa or '',
            lancamento.status.value if hasattr(lancamento.status, 'value') else str(lancamento.status),
            lancamento.observacoes or '',
            lancamento.anexo or '',
            lancamento.recorrente,
            lancamento.frequencia_recorrencia or '',
            lancamento.dia_vencimento or 0,
            getattr(lancamento, 'juros', 0),
            getattr(lancamento, 'desconto', 0),
            lancamento.id
        )
        
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        
        cursor.execute(query, params)
        sucesso = cursor.rowcount > 0
        
        print(f"✅ Linhas afetadas: {cursor.rowcount}, Sucesso: {sucesso}\n")
        
        cursor.close()
        conn.close()
        return sucesso
    
    def pagar_lancamento(self, lancamento_id: int, conta: str = '', data_pagamento: date = None,
                        juros: float = 0, desconto: float = 0, observacoes: str = '',
                        valor_pago: Optional[Decimal] = None) -> bool:
        """Marca um lançamento como pago"""
        print(f"\n🔍 DatabaseManager.pagar_lancamento() chamada:")
        print(f"   - lancamento_id: {lancamento_id} (tipo: {type(lancamento_id)})")
        print(f"   - conta: {conta} (tipo: {type(conta)})")
        print(f"   - data_pagamento: {data_pagamento} (tipo: {type(data_pagamento)})")
        print(f"   - juros: {juros} (tipo: {type(juros)})")
        print(f"   - desconto: {desconto} (tipo: {type(desconto)})")
        print(f"   - observacoes: {observacoes} (tipo: {type(observacoes)})")
        print(f"   - valor_pago: {valor_pago} (tipo: {type(valor_pago)})")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se não passar data_pagamento, usar a data atual
        if not data_pagamento:
            data_pagamento = date.today()
            print(f"⚠️  Data não fornecida, usando hoje: {data_pagamento}")
        
        if valor_pago:
            query = """
                UPDATE lancamentos 
                SET status = %s, data_pagamento = %s, valor = %s, 
                    conta_bancaria = %s, juros = %s, desconto = %s, observacoes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (StatusLancamento.PAGO.value, data_pagamento, float(valor_pago), 
                  conta, juros, desconto, observacoes, lancamento_id)
            print(f"📝 Query COM valor_pago:")
            print(f"   SQL: {query}")
            print(f"   Params: {params}")
            cursor.execute(query, params)
        else:
            query = """
                UPDATE lancamentos 
                SET status = %s, data_pagamento = %s,
                    conta_bancaria = %s, juros = %s, desconto = %s, observacoes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (StatusLancamento.PAGO.value, data_pagamento, 
                  conta, juros, desconto, observacoes, lancamento_id)
            print(f"📝 Query SEM valor_pago:")
            print(f"   SQL: {query}")
            print(f"   Params: {params}")
            cursor.execute(query, params)
        
        sucesso = cursor.rowcount > 0
        print(f"✅ Linhas afetadas: {cursor.rowcount}, Sucesso: {sucesso}")
        cursor.close()
        conn.close()
        return sucesso
    
    def cancelar_lancamento(self, lancamento_id: int) -> bool:
        """Cancela um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lancamentos 
            SET status = %s, data_pagamento = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (StatusLancamento.PENDENTE.value, lancamento_id))
        
        sucesso = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return sucesso
    
    def migrar_dados_json(self, json_path: str):
        """Migra dados de um arquivo JSON para o banco"""
        if not os.path.exists(json_path):
            print(f"Arquivo {json_path} não encontrado")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Migrar contas
        for conta_data in dados.get('contas', []):
            conta = ContaBancaria(**conta_data)
            try:
                self.adicionar_conta(conta)
            except Exception as e:
                print(f"Erro ao migrar conta {conta.nome}: {e}")
        
        # Migrar categorias
        for cat_data in dados.get('categorias', []):
            categoria = Categoria(**cat_data)
            try:
                self.adicionar_categoria(categoria)
            except Exception as e:
                print(f"Erro ao migrar categoria {categoria.nome}: {e}")
        
        # Migrar lançamentos
        for lanc_data in dados.get('lancamentos', []):
            lancamento = Lancamento(**lanc_data)
            try:
                self.adicionar_lancamento(lancamento)
            except Exception as e:
                print(f"Erro ao migrar lançamento: {e}")
        
        print("Migração concluída!")
    
    # === MÉTODOS DO MENU OPERACIONAL ===
    
    def gerar_proximo_numero_contrato(self) -> str:
        """Gera o próximo número de contrato"""
        return gerar_proximo_numero_contrato()
    
    def adicionar_contrato(self, dados: Dict) -> int:
        """Adiciona um novo contrato"""
        return adicionar_contrato(dados)
    
    def listar_contratos(self) -> List[Dict]:
        """Lista todos os contratos"""
        return listar_contratos()
    
    def atualizar_contrato(self, contrato_id: int, dados: Dict) -> bool:
        """Atualiza um contrato"""
        return atualizar_contrato(contrato_id, dados)
    
    def deletar_contrato(self, contrato_id: int) -> bool:
        """Deleta um contrato"""
        return deletar_contrato(contrato_id)
    
    def adicionar_sessao(self, dados: Dict) -> int:
        """Adiciona uma nova sessão"""
        return adicionar_sessao(dados)
    
    def listar_sessoes(self) -> List[Dict]:
        """Lista todas as sessões"""
        return listar_sessoes()
    
    def atualizar_sessao(self, sessao_id: int, dados: Dict) -> bool:
        """Atualiza uma sessão"""
        return atualizar_sessao(sessao_id, dados)
    
    def deletar_sessao(self, sessao_id: int) -> bool:
        """Deleta uma sessão"""
        return deletar_sessao(sessao_id)
    
    def adicionar_comissao(self, dados: Dict) -> int:
        """Adiciona uma nova comissão"""
        return adicionar_comissao(dados)
    
    def listar_comissoes(self) -> List[Dict]:
        """Lista todas as comissões"""
        return listar_comissoes()
    
    def atualizar_comissao(self, comissao_id: int, dados: Dict) -> bool:
        """Atualiza uma comissão"""
        return atualizar_comissao(comissao_id, dados)
    
    def deletar_comissao(self, comissao_id: int) -> bool:
        """Deleta uma comissão"""
        return deletar_comissao(comissao_id)
    
    def adicionar_sessao_equipe(self, dados: Dict) -> int:
        """Adiciona um membro à equipe de sessão"""
        return adicionar_sessao_equipe(dados)
    
    def listar_sessao_equipe(self, sessao_id: int = None) -> List[Dict]:
        """Lista membros da equipe de sessão"""
        return listar_sessao_equipe(sessao_id)
    
    def atualizar_sessao_equipe(self, membro_id: int, dados: Dict) -> bool:
        """Atualiza um membro da equipe"""
        return atualizar_sessao_equipe(membro_id, dados)
    
    def deletar_sessao_equipe(self, membro_id: int) -> bool:
        """Deleta um membro da equipe"""
        return deletar_sessao_equipe(membro_id)
    
    def adicionar_tipo_sessao(self, dados: Dict) -> int:
        """Adiciona um novo tipo de sessão"""
        return adicionar_tipo_sessao(dados)
    
    def listar_tipos_sessao(self) -> List[Dict]:
        """Lista todos os tipos de sessão"""
        return listar_tipos_sessao()
    
    def atualizar_tipo_sessao(self, tipo_id: int, dados: Dict) -> bool:
        """Atualiza um tipo de sessão"""
        return atualizar_tipo_sessao(tipo_id, dados)
    
    def deletar_tipo_sessao(self, tipo_id: int) -> bool:
        """Deleta um tipo de sessão"""
        return deletar_tipo_sessao(tipo_id)
    
    def adicionar_agenda(self, dados: Dict) -> int:
        """Adiciona um novo agendamento"""
        return adicionar_agenda(dados)
    
    def listar_agenda(self) -> List[Dict]:
        """Lista todos os agendamentos"""
        return listar_agenda()
    
    def atualizar_agenda(self, agenda_id: int, dados: Dict) -> bool:
        """Atualiza um agendamento"""
        return atualizar_agenda(agenda_id, dados)
    
    def deletar_agenda(self, agenda_id: int) -> bool:
        """Deleta um agendamento"""
        return deletar_agenda(agenda_id)


# Funções standalone para compatibilidade
def criar_tabelas():
    db = DatabaseManager()
    db.criar_tabelas()

def get_connection():
    db = DatabaseManager()
    return db.get_connection()

def adicionar_conta(conta: ContaBancaria) -> int:
    db = DatabaseManager()
    return db.adicionar_conta(conta)

def listar_contas() -> List[ContaBancaria]:
    db = DatabaseManager()
    return db.listar_contas()

def atualizar_conta(nome_antigo: str, conta: ContaBancaria) -> bool:
    db = DatabaseManager()
    return db.atualizar_conta(nome_antigo, conta)

def excluir_conta(nome: str) -> bool:
    db = DatabaseManager()
    return db.excluir_conta(nome)

def adicionar_categoria(categoria: Categoria) -> int:
    db = DatabaseManager()
    return db.adicionar_categoria(categoria)

def listar_categorias(tipo: Optional[TipoLancamento] = None) -> List[Categoria]:
    db = DatabaseManager()
    return db.listar_categorias(tipo)

def excluir_categoria(nome: str) -> bool:
    db = DatabaseManager()
    return db.excluir_categoria(nome)

def atualizar_categoria(categoria: Categoria) -> bool:
    db = DatabaseManager()
    return db.atualizar_categoria(categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    db = DatabaseManager()
    return db.atualizar_nome_categoria(nome_antigo, nome_novo)

def adicionar_cliente(cliente_data, cpf_cnpj: str = None, email: str = None,
                     telefone: str = None, endereco: str = None) -> int:
    db = DatabaseManager()
    return db.adicionar_cliente(cliente_data, cpf_cnpj, email, telefone, endereco)

def listar_clientes(ativos: bool = True) -> List[Dict]:
    db = DatabaseManager()
    return db.listar_clientes(ativos)

def atualizar_cliente(nome_antigo: str, dados: Dict) -> bool:
    db = DatabaseManager()
    return db.atualizar_cliente(nome_antigo, dados)

def inativar_cliente(nome: str, motivo: str = "") -> tuple[bool, str]:
    db = DatabaseManager()
    return db.inativar_cliente(nome, motivo)

def reativar_cliente(nome: str) -> bool:
    db = DatabaseManager()
    return db.reativar_cliente(nome)

def adicionar_fornecedor(fornecedor_data, cpf_cnpj: str = None, email: str = None,
                        telefone: str = None, endereco: str = None) -> int:
    db = DatabaseManager()
    return db.adicionar_fornecedor(fornecedor_data, cpf_cnpj, email, telefone, endereco)

def listar_fornecedores(ativos: bool = True) -> List[Dict]:
    db = DatabaseManager()
    return db.listar_fornecedores(ativos)

def atualizar_fornecedor(nome_antigo: str, dados: Dict) -> bool:
    db = DatabaseManager()
    return db.atualizar_fornecedor(nome_antigo, dados)

def inativar_fornecedor(nome: str, motivo: str = "") -> tuple[bool, str]:
    db = DatabaseManager()
    return db.inativar_fornecedor(nome, motivo)

def reativar_fornecedor(nome: str) -> bool:
    db = DatabaseManager()
    return db.reativar_fornecedor(nome)

def adicionar_lancamento(lancamento: Lancamento) -> int:
    db = DatabaseManager()
    return db.adicionar_lancamento(lancamento)

def listar_lancamentos(filtros: Dict[str, Any] = None) -> List[Lancamento]:
    db = DatabaseManager()
    return db.listar_lancamentos(filtros)

def obter_lancamento(lancamento_id: int) -> Optional[Lancamento]:
    db = DatabaseManager()
    return db.obter_lancamento(lancamento_id)

def excluir_lancamento(lancamento_id: int) -> bool:
    db = DatabaseManager()
    return db.excluir_lancamento(lancamento_id)

def pagar_lancamento(lancamento_id: int, conta: str = '', data_pagamento: date = None,
                    juros: float = 0, desconto: float = 0, observacoes: str = '',
                    valor_pago: Optional[Decimal] = None) -> bool:
    print(f"\n🔍 pagar_lancamento() wrapper chamada:")
    print(f"   Args: ({lancamento_id}, {conta}, {data_pagamento}, {juros}, {desconto}, {observacoes}, {valor_pago})")
    db = DatabaseManager()
    print(f"   DatabaseManager criado: {type(db)}")
    resultado = db.pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes, valor_pago)
    print(f"   Resultado: {resultado}\n")
    return resultado

def cancelar_lancamento(lancamento_id: int) -> bool:
    db = DatabaseManager()
    return db.cancelar_lancamento(lancamento_id)

def migrar_dados_json(json_path: str):
    db = DatabaseManager()
    return db.migrar_dados_json(json_path)


# ==================== FUNÇÕES CRUD - CONTRATOS ====================
def gerar_proximo_numero_contrato() -> str:
    """Gera o próximo número de contrato no formato CONT-YYYY-NNNN"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        ano_atual = datetime.now().year
        
        # Buscar o último número de contrato do ano atual
        cursor.execute("""
            SELECT numero FROM contratos 
            WHERE numero LIKE %s
            ORDER BY numero DESC 
            LIMIT 1
        """, (f'CONT-{ano_atual}-%',))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Extrair o número sequencial do último contrato
            ultimo_numero = resultado['numero']
            try:
                sequencial = int(ultimo_numero.split('-')[-1])
                proximo_numero = sequencial + 1
            except (ValueError, IndexError):
                proximo_numero = 1
        else:
            proximo_numero = 1
        
        cursor.close()
        conn.close()
        
        # Formatar: CONT-2025-0001
        return f'CONT-{ano_atual}-{proximo_numero:04d}'
    except Exception as e:
        print(f"❌ Erro ao gerar número do contrato: {e}")
        # Em caso de erro, retornar um número padrão
        ano_atual = datetime.now().year
        return f'CONT-{ano_atual}-0001'

def adicionar_contrato(dados: Dict) -> int:
    """Adiciona um novo contrato"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO contratos (numero, cliente_id, descricao, valor, data_inicio, data_fim, status, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('numero'),
        dados.get('cliente_id'),
        dados.get('descricao'),
        dados.get('valor'),
        dados.get('data_inicio'),
        dados.get('data_fim'),
        dados.get('status', 'ativo'),
        dados.get('observacoes')
    ))
    
    contrato_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return contrato_id

def listar_contratos() -> List[Dict]:
    """Lista todos os contratos"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, cl.nome as cliente_nome
        FROM contratos c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        ORDER BY c.created_at DESC
    """)
    
    contratos = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return contratos

def atualizar_contrato(contrato_id: int, dados: Dict) -> bool:
    """Atualiza um contrato existente"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE contratos
        SET numero = %s, cliente_id = %s, descricao = %s, valor = %s,
            data_inicio = %s, data_fim = %s, status = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('numero'),
        dados.get('cliente_id'),
        dados.get('descricao'),
        dados.get('valor'),
        dados.get('data_inicio'),
        dados.get('data_fim'),
        dados.get('status'),
        dados.get('observacoes'),
        contrato_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_contrato(contrato_id: int) -> bool:
    """Deleta um contrato"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM contratos WHERE id = %s", (contrato_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - AGENDA ====================
def adicionar_agenda(dados: Dict) -> int:
    """Adiciona um novo evento na agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO agenda (titulo, data_evento, hora_inicio, hora_fim, local, tipo, status, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('titulo'),
        dados.get('data_evento'),
        dados.get('hora_inicio'),
        dados.get('hora_fim'),
        dados.get('local'),
        dados.get('tipo'),
        dados.get('status', 'agendado'),
        dados.get('observacoes')
    ))
    
    agenda_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return agenda_id

def listar_agenda() -> List[Dict]:
    """Lista todos os eventos da agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agenda ORDER BY data_evento DESC, hora_inicio DESC")
    
    eventos = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return eventos

def atualizar_agenda(agenda_id: int, dados: Dict) -> bool:
    """Atualiza um evento da agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agenda
        SET titulo = %s, data_evento = %s, hora_inicio = %s, hora_fim = %s,
            local = %s, tipo = %s, status = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('titulo'),
        dados.get('data_evento'),
        dados.get('hora_inicio'),
        dados.get('hora_fim'),
        dados.get('local'),
        dados.get('tipo'),
        dados.get('status'),
        dados.get('observacoes'),
        agenda_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_agenda(agenda_id: int) -> bool:
    """Deleta um evento da agenda"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM agenda WHERE id = %s", (agenda_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - PRODUTOS ====================
def adicionar_produto(dados: Dict) -> int:
    """Adiciona um novo produto"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO produtos (codigo, nome, categoria, quantidade, preco_custo, preco_venda, fornecedor_id, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('categoria'),
        dados.get('quantidade', 0),
        dados.get('preco_custo'),
        dados.get('preco_venda'),
        dados.get('fornecedor_id'),
        dados.get('observacoes')
    ))
    
    produto_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return produto_id

def listar_produtos() -> List[Dict]:
    """Lista todos os produtos"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.codigo, p.nome, p.categoria, p.quantidade, 
               p.preco_custo, p.preco_venda, p.fornecedor_id, p.observacoes,
               p.created_at, p.updated_at, f.nome as fornecedor_nome
        FROM produtos p
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        ORDER BY p.nome
    """)
    
    produtos = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return produtos

def atualizar_produto(produto_id: int, dados: Dict) -> bool:
    """Atualiza um produto"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE produtos
        SET codigo = %s, nome = %s, categoria = %s, quantidade = %s,
            preco_custo = %s, preco_venda = %s, fornecedor_id = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('categoria'),
        dados.get('quantidade'),
        dados.get('preco_custo'),
        dados.get('preco_venda'),
        dados.get('fornecedor_id'),
        dados.get('observacoes'),
        produto_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_produto(produto_id: int) -> bool:
    """Deleta um produto"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM produtos WHERE id = %s", (produto_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - KITS ====================
def adicionar_kit(dados: Dict) -> int:
    """Adiciona um novo kit"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO kits (codigo, nome, preco, observacoes)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('preco'),
        dados.get('observacoes')
    ))
    
    kit_id = cursor.fetchone()['id']
    
    # Adicionar itens do kit se fornecidos
    if 'itens' in dados and dados['itens']:
        for item in dados['itens']:
            cursor.execute("""
                INSERT INTO kit_itens (kit_id, produto_id, quantidade)
                VALUES (%s, %s, %s)
            """, (kit_id, item['produto_id'], item['quantidade']))
    
    cursor.close()
    conn.close()
    return kit_id

def listar_kits() -> List[Dict]:
    """Lista todos os kits"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, codigo, nome, preco, observacoes, created_at, updated_at FROM kits ORDER BY nome")
    kits = [dict(row) for row in cursor.fetchall()]
    
    # Buscar itens de cada kit
    for kit in kits:
        cursor.execute("""
            SELECT ki.*, p.nome as produto_nome, p.codigo as produto_codigo
            FROM kit_itens ki
            JOIN produtos p ON ki.produto_id = p.id
            WHERE ki.kit_id = %s
        """, (kit['id'],))
        kit['itens'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return kits

def atualizar_kit(kit_id: int, dados: Dict) -> bool:
    """Atualiza um kit"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE kits
        SET codigo = %s, nome = %s, preco = %s, observacoes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('codigo'),
        dados.get('nome'),
        dados.get('preco'),
        dados.get('observacoes'),
        kit_id
    ))
    
    # Atualizar itens se fornecidos
    if 'itens' in dados:
        cursor.execute("DELETE FROM kit_itens WHERE kit_id = %s", (kit_id,))
        for item in dados['itens']:
            cursor.execute("""
                INSERT INTO kit_itens (kit_id, produto_id, quantidade)
                VALUES (%s, %s, %s)
            """, (kit_id, item['produto_id'], item['quantidade']))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_kit(kit_id: int) -> bool:
    """Deleta um kit"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM kits WHERE id = %s", (kit_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - TAGS ====================
def adicionar_tag(dados: Dict) -> int:
    """Adiciona uma nova tag"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tags (nome, cor, descricao)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        dados.get('nome'),
        dados.get('cor', '#007bff'),
        dados.get('descricao')
    ))
    
    tag_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return tag_id

def listar_tags() -> List[Dict]:
    """Lista todas as tags"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, cor, descricao, created_at, updated_at FROM tags ORDER BY nome")
    
    tags = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tags

def atualizar_tag(tag_id: int, dados: Dict) -> bool:
    """Atualiza uma tag"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tags
        SET nome = %s, cor = %s, descricao = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('nome'),
        dados.get('cor'),
        dados.get('descricao'),
        tag_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_tag(tag_id: int) -> bool:
    """Deleta uma tag"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tags WHERE id = %s", (tag_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - TEMPLATES DE EQUIPE ====================
def adicionar_template(dados: Dict) -> int:
    """Adiciona um novo template de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO templates_equipe (nome, tipo, conteudo)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        dados.get('nome'),
        dados.get('tipo'),
        dados.get('conteudo')
    ))
    
    template_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return template_id

def listar_templates_equipe() -> List[Dict]:
    """Lista todos os templates de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, tipo, conteudo, created_at, updated_at FROM templates_equipe ORDER BY nome")
    
    templates = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return templates

def atualizar_template(template_id: int, dados: Dict) -> bool:
    """Atualiza um template de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE templates_equipe
        SET nome = %s, tipo = %s, conteudo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('nome'),
        dados.get('tipo'),
        dados.get('conteudo'),
        template_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_template(template_id: int) -> bool:
    """Deleta um template de equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM templates_equipe WHERE id = %s", (template_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - SESSÕES ====================
def adicionar_sessao(dados: Dict) -> int:
    """Adiciona uma nova sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessoes (titulo, data_sessao, duracao, contrato_id, cliente_id, valor, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('titulo'),
        dados.get('data_sessao'),
        dados.get('duracao'),
        dados.get('contrato_id'),
        dados.get('cliente_id'),
        dados.get('valor'),
        dados.get('observacoes')
    ))
    
    sessao_id = cursor.fetchone()['id']
    
    # Adicionar membros da equipe se fornecidos
    if 'equipe' in dados and dados['equipe']:
        for membro in dados['equipe']:
            cursor.execute("""
                INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao)
                VALUES (%s, %s, %s)
            """, (sessao_id, membro['nome'], membro.get('funcao')))
    
    cursor.close()
    conn.close()
    return sessao_id

def listar_sessoes() -> List[Dict]:
    """Lista todas as sessões"""
    import datetime
    import decimal
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.*, c.nome as cliente_nome, ct.numero as contrato_numero
        FROM sessoes s
        LEFT JOIN clientes c ON s.cliente_id = c.id
        LEFT JOIN contratos ct ON s.contrato_id = ct.id
        ORDER BY s.data_sessao DESC
    """)
    sessoes = []
    for row in cursor.fetchall():
        sessao = {}
        for key, value in dict(row).items():
            # Converter tipos não-serializáveis para JSON
            if isinstance(value, (datetime.time, datetime.datetime, datetime.date)):
                sessao[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                sessao[key] = float(value)
            else:
                sessao[key] = value
        sessoes.append(sessao)
    
    # Buscar equipe de cada sessão
    for sessao in sessoes:
        cursor.execute("""
            SELECT * FROM sessao_equipe WHERE sessao_id = %s
        """, (sessao['id'],))
        sessao['equipe'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return sessoes

def atualizar_sessao(sessao_id: int, dados: Dict) -> bool:
    """Atualiza uma sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessoes
        SET titulo = %s, data_sessao = %s, duracao = %s, contrato_id = %s, cliente_id = %s,
            valor = %s, observacoes = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados.get('titulo'),
        dados.get('data_sessao'),
        dados.get('duracao'),
        dados.get('contrato_id'),
        dados.get('cliente_id'),
        dados.get('valor'),
        dados.get('observacoes'),
        sessao_id
    ))
    
    # Atualizar equipe se fornecida
    if 'equipe' in dados:
        cursor.execute("DELETE FROM sessao_equipe WHERE sessao_id = %s", (sessao_id,))
        for membro in dados['equipe']:
            cursor.execute("""
                INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao)
                VALUES (%s, %s, %s)
            """, (sessao_id, membro['nome'], membro.get('funcao')))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_sessao(sessao_id: int) -> bool:
    """Deleta uma sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessoes WHERE id = %s", (sessao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - COMISSÕES ====================
def adicionar_comissao(dados: Dict) -> int:
    """Adiciona uma nova comissão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Buscar cliente_id do contrato se não fornecido
    cliente_id = dados.get('cliente_id')
    contrato_id = dados.get('contrato_id')
    
    if not cliente_id and contrato_id:
        cursor.execute("SELECT cliente_id FROM contratos WHERE id = %s", (contrato_id,))
        result = cursor.fetchone()
        if result:
            cliente_id = result['cliente_id']
    
    cursor.execute("""
        INSERT INTO comissoes (contrato_id, cliente_id, tipo, descricao, valor, percentual)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        contrato_id,
        cliente_id,
        dados.get('tipo', 'percentual'),
        dados.get('descricao'),
        dados.get('valor', 0),
        dados.get('percentual', 0)
    ))
    
    comissao_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return comissao_id

def listar_comissoes() -> List[Dict]:
    """Lista todas as comissões com informações de contrato e cliente"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            com.*,
            ct.numero as contrato_numero,
            ct.valor as contrato_valor,
            cl.nome as cliente_nome
        FROM comissoes com
        LEFT JOIN contratos ct ON com.contrato_id = ct.id
        LEFT JOIN clientes cl ON com.cliente_id = cl.id
        ORDER BY com.created_at DESC
    """)
    
    comissoes = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return comissoes

def atualizar_comissao(comissao_id: int, dados: Dict) -> bool:
    """Atualiza uma comissão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Buscar cliente_id do contrato se não fornecido
    cliente_id = dados.get('cliente_id')
    contrato_id = dados.get('contrato_id')
    
    if not cliente_id and contrato_id:
        cursor.execute("SELECT cliente_id FROM contratos WHERE id = %s", (contrato_id,))
        result = cursor.fetchone()
        if result:
            cliente_id = result['cliente_id']
    
    cursor.execute("""
        UPDATE comissoes
        SET contrato_id = %s, cliente_id = %s, tipo = %s, 
            descricao = %s, valor = %s, percentual = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        contrato_id,
        cliente_id,
        dados.get('tipo', 'percentual'),
        dados.get('descricao'),
        dados.get('valor', 0),
        dados.get('percentual', 0),
        comissao_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_comissao(comissao_id: int) -> bool:
    """Deleta uma comissão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM comissoes WHERE id = %s", (comissao_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso


# ==================== FUNÇÕES CRUD - SESSÃO EQUIPE ====================
def adicionar_sessao_equipe(dados: Dict) -> int:
    """Adiciona um membro à equipe de uma sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print(f"[DB] Inserindo membro: {dados}")
    
    cursor.execute("""
        INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao, observacoes)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        dados.get('sessao_id'),
        dados.get('membro_nome'),
        dados.get('funcao'),
        dados.get('observacoes', '')
    ))
    
    se_id = cursor.fetchone()['id']
    print(f"[DB] Membro inserido com ID: {se_id}")
    
    conn.commit()  # COMMIT ESQUECIDO!
    print(f"[DB] COMMIT executado")
    
    cursor.close()
    conn.close()
    return se_id

def listar_sessao_equipe(sessao_id: int = None) -> List[Dict]:
    """Lista membros da equipe de sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if sessao_id:
        cursor.execute("""
            SELECT se.*, 
                   s.titulo as sessao_titulo,
                   s.data_sessao,
                   c.nome as cliente_nome
            FROM sessao_equipe se
            LEFT JOIN sessoes s ON se.sessao_id = s.id
            LEFT JOIN contratos ct ON s.contrato_id = ct.id
            LEFT JOIN clientes c ON ct.cliente_id = c.id
            WHERE se.sessao_id = %s
            ORDER BY se.created_at
        """, (sessao_id,))
    else:
        cursor.execute("""
            SELECT se.*, 
                   s.titulo as sessao_titulo,
                   s.data_sessao,
                   c.nome as cliente_nome
            FROM sessao_equipe se
            LEFT JOIN sessoes s ON se.sessao_id = s.id
            LEFT JOIN contratos ct ON s.contrato_id = ct.id
            LEFT JOIN clientes c ON ct.cliente_id = c.id
            ORDER BY se.created_at DESC
        """)
    
    membros = []
    for row in cursor.fetchall():
        membro = dict(row)
        # Criar sessao_info formatada
        if membro.get('sessao_titulo'):
            info_parts = [membro['sessao_titulo']]
            if membro.get('data_sessao'):
                info_parts.append(str(membro['data_sessao']))
            if membro.get('cliente_nome'):
                info_parts.append(membro['cliente_nome'])
            membro['sessao_info'] = ' - '.join(info_parts)
        else:
            membro['sessao_info'] = f"Sessão #{membro.get('sessao_id', '?')}"
        membros.append(membro)
    
    cursor.close()
    conn.close()
    return membros

def atualizar_sessao_equipe(membro_id: int, dados: Dict) -> bool:
    """Atualiza um membro da equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessao_equipe
        SET sessao_id = %s, membro_nome = %s, funcao = %s, observacoes = %s
        WHERE id = %s
    """, (
        dados.get('sessao_id'),
        dados.get('membro_nome'),
        dados.get('funcao'),
        dados.get('observacoes', ''),
        membro_id
    ))
    
    sucesso = cursor.rowcount > 0
    conn.commit()  # COMMIT ESQUECIDO!
    cursor.close()
    conn.close()
    return sucesso

def deletar_sessao_equipe(membro_id: int) -> bool:
    """Deleta um membro da equipe"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessao_equipe WHERE id = %s", (membro_id,))
    
    sucesso = cursor.rowcount > 0
    conn.commit()  # COMMIT ESQUECIDO!
    cursor.close()
    conn.close()
    return sucesso

# ==================== TIPOS DE SESSÃO ====================

def adicionar_tipo_sessao(dados: Dict) -> int:
    """Adiciona um novo tipo de sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tipos_sessao (nome, descricao, duracao_padrao, valor_padrao, ativo)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        dados['nome'],
        dados.get('descricao'),
        dados.get('duracao_padrao'),
        dados.get('valor_padrao'),
        dados.get('ativo', True)
    ))
    
    tipo_id = cursor.fetchone()['id']
    cursor.close()
    conn.close()
    return tipo_id

def listar_tipos_sessao() -> List[Dict]:
    """Lista todos os tipos de sessão"""
    import datetime
    import decimal
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nome, descricao, duracao_padrao, valor_padrao, ativo, created_at, updated_at
        FROM tipos_sessao
        ORDER BY nome
    """)
    
    tipos = []
    for row in cursor.fetchall():
        tipo = {}
        for key, value in dict(row).items():
            if isinstance(value, (datetime.time, datetime.datetime, datetime.date)):
                tipo[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                tipo[key] = float(value)
            else:
                tipo[key] = value
        tipos.append(tipo)
    
    cursor.close()
    conn.close()
    return tipos

def atualizar_tipo_sessao(tipo_id: int, dados: Dict) -> bool:
    """Atualiza um tipo de sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tipos_sessao 
        SET nome = %s, descricao = %s, duracao_padrao = %s, valor_padrao = %s, ativo = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (
        dados['nome'],
        dados.get('descricao'),
        dados.get('duracao_padrao'),
        dados.get('valor_padrao'),
        dados.get('ativo', True),
        tipo_id
    ))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

def deletar_tipo_sessao(tipo_id: int) -> bool:
    """Deleta um tipo de sessão"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tipos_sessao WHERE id = %s", (tipo_id,))
    
    sucesso = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return sucesso

"""
Módulo de gerenciamento do banco de dados PostgreSQL
"""
import psycopg2
from psycopg2 import Error, sql
from psycopg2.extras import RealDictCursor
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
    'atualizar_fornecedor'
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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
    
    def excluir_conta(self, conta_id: int) -> bool:
        """Exclui uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM contas_bancarias WHERE id = %s", (conta_id,))
        sucesso = cursor.rowcount > 0
        
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
            subcategorias = json.loads(row['subcategorias']) if row['subcategorias'] else []
            
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
    
    def excluir_categoria(self, categoria_id: int) -> bool:
        """Exclui uma categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM categorias WHERE id = %s", (categoria_id,))
        sucesso = cursor.rowcount > 0
        
        cursor.close()
        conn.close()
        return sucesso
    
    def atualizar_categoria(self, categoria_id: int, categoria: Categoria) -> bool:
        """Atualiza uma categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias) if categoria.subcategorias else None
        
        cursor.execute("""
            UPDATE categorias 
            SET nome = %s, tipo = %s, subcategorias = %s, 
                cor = %s, icone = %s, descricao = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            categoria.nome,
            categoria.tipo.value,
            subcategorias_json,
            categoria.cor,
            categoria.icone,
            categoria.descricao,
            categoria_id
        ))
        
        sucesso = cursor.rowcount > 0
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
    
    def adicionar_cliente(self, nome: str, cpf_cnpj: str = None, 
                         email: str = None, telefone: str = None,
                         endereco: str = None) -> int:
        """Adiciona um novo cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (nome, cpf_cnpj, email, telefone, endereco))
        
        cliente_id = cursor.fetchone()['id']
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
    
    def atualizar_cliente(self, cliente_id: int, dados: Dict) -> bool:
        """Atualiza os dados de um cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE clientes 
            SET nome = %s, cpf_cnpj = %s, email = %s, 
                telefone = %s, endereco = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            dados.get('nome'),
            dados.get('cpf_cnpj'),
            dados.get('email'),
            dados.get('telefone'),
            dados.get('endereco'),
            cliente_id
        ))
        
        sucesso = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return sucesso
    
    def adicionar_fornecedor(self, nome: str, cpf_cnpj: str = None,
                           email: str = None, telefone: str = None,
                           endereco: str = None) -> int:
        """Adiciona um novo fornecedor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO fornecedores (nome, cpf_cnpj, email, telefone, endereco)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (nome, cpf_cnpj, email, telefone, endereco))
        
        fornecedor_id = cursor.fetchone()['id']
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
    
    def atualizar_fornecedor(self, fornecedor_id: int, dados: Dict) -> bool:
        """Atualiza os dados de um fornecedor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fornecedores 
            SET nome = %s, cpf_cnpj = %s, email = %s, 
                telefone = %s, endereco = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            dados.get('nome'),
            dados.get('cpf_cnpj'),
            dados.get('email'),
            dados.get('telefone'),
            dados.get('endereco'),
            fornecedor_id
        ))
        
        sucesso = cursor.rowcount > 0
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM lancamentos WHERE id = %s", (lancamento_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return None
        
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
    
    def pagar_lancamento(self, lancamento_id: int, conta: str = '', data_pagamento: date = None,
                        juros: float = 0, desconto: float = 0, observacoes: str = '',
                        valor_pago: Optional[Decimal] = None) -> bool:
        """Marca um lançamento como pago"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se não passar data_pagamento, usar a data atual
        if not data_pagamento:
            data_pagamento = date.today()
        
        if valor_pago:
            cursor.execute("""
                UPDATE lancamentos 
                SET status = %s, data_pagamento = %s, valor = %s, 
                    conta_bancaria = %s, juros = %s, desconto = %s, observacoes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (StatusLancamento.PAGO.value, data_pagamento, float(valor_pago), 
                  conta, juros, desconto, observacoes, lancamento_id))
        else:
            cursor.execute("""
                UPDATE lancamentos 
                SET status = %s, data_pagamento = %s,
                    conta_bancaria = %s, juros = %s, desconto = %s, observacoes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (StatusLancamento.PAGO.value, data_pagamento, 
                  conta, juros, desconto, observacoes, lancamento_id))
        
        sucesso = cursor.rowcount > 0
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

def excluir_conta(conta_id: int) -> bool:
    db = DatabaseManager()
    return db.excluir_conta(conta_id)

def adicionar_categoria(categoria: Categoria) -> int:
    db = DatabaseManager()
    return db.adicionar_categoria(categoria)

def listar_categorias(tipo: Optional[TipoLancamento] = None) -> List[Categoria]:
    db = DatabaseManager()
    return db.listar_categorias(tipo)

def excluir_categoria(categoria_id: int) -> bool:
    db = DatabaseManager()
    return db.excluir_categoria(categoria_id)

def atualizar_categoria(categoria_id: int, categoria: Categoria) -> bool:
    db = DatabaseManager()
    return db.atualizar_categoria(categoria_id, categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    db = DatabaseManager()
    return db.atualizar_nome_categoria(nome_antigo, nome_novo)

def adicionar_cliente(nome: str, cpf_cnpj: str = None, email: str = None,
                     telefone: str = None, endereco: str = None) -> int:
    db = DatabaseManager()
    return db.adicionar_cliente(nome, cpf_cnpj, email, telefone, endereco)

def listar_clientes(ativos: bool = True) -> List[Dict]:
    db = DatabaseManager()
    return db.listar_clientes(ativos)

def atualizar_cliente(cliente_id: int, dados: Dict) -> bool:
    db = DatabaseManager()
    return db.atualizar_cliente(cliente_id, dados)

def adicionar_fornecedor(nome: str, cpf_cnpj: str = None, email: str = None,
                        telefone: str = None, endereco: str = None) -> int:
    db = DatabaseManager()
    return db.adicionar_fornecedor(nome, cpf_cnpj, email, telefone, endereco)

def listar_fornecedores(ativos: bool = True) -> List[Dict]:
    db = DatabaseManager()
    return db.listar_fornecedores(ativos)

def atualizar_fornecedor(fornecedor_id: int, dados: Dict) -> bool:
    db = DatabaseManager()
    return db.atualizar_fornecedor(fornecedor_id, dados)

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
    db = DatabaseManager()
    return db.pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes, valor_pago)

def cancelar_lancamento(lancamento_id: int) -> bool:
    db = DatabaseManager()
    return db.cancelar_lancamento(lancamento_id)

def migrar_dados_json(json_path: str):
    db = DatabaseManager()
    return db.migrar_dados_json(json_path)

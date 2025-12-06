"""
Módulo de gerenciamento do banco de dados MySQL
"""
import mysql.connector
from mysql.connector import Error
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
    'migrar_dados_json'
]

# Configurações do MySQL
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'sistema_financeiro'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}


class DatabaseManager:
    """Gerenciador do banco de dados MySQL"""
    
    def __init__(self, config: Dict = None):  # type: ignore
        self.config = config or MYSQL_CONFIG
        self.criar_database()
        self.criar_tabelas()
    
    def criar_database(self):
        """Cria o database se não existir"""
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']} CHARACTER SET {self.config['charset']} COLLATE {self.config['collation']}")
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Erro ao criar database: {e}")
    
    def get_connection(self):
        """Cria uma conexão com o banco de dados"""
        try:
            conn = mysql.connector.connect(**self.config)
            return conn
        except Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            raise
    
    def criar_tabelas(self):
        """Cria as tabelas no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de contas bancárias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                banco VARCHAR(255) NOT NULL,
                agencia VARCHAR(50) NOT NULL,
                conta VARCHAR(50) NOT NULL,
                saldo_inicial DECIMAL(15,2) NOT NULL,
                ativa TINYINT DEFAULT 1,
                data_criacao DATETIME NOT NULL,
                INDEX idx_nome (nome),
                INDEX idx_ativa (ativa)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabela de categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                subcategorias JSON,
                INDEX idx_nome (nome),
                INDEX idx_tipo (tipo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabela de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                razao_social VARCHAR(255),
                nome_fantasia VARCHAR(255),
                cnpj VARCHAR(20),
                ie VARCHAR(50),
                im VARCHAR(50),
                cep VARCHAR(10),
                rua VARCHAR(255),
                numero VARCHAR(20),
                complemento VARCHAR(100),
                bairro VARCHAR(100),
                cidade VARCHAR(100),
                estado VARCHAR(2),
                telefone VARCHAR(20),
                contato VARCHAR(20),
                email VARCHAR(255),
                endereco TEXT,
                documento VARCHAR(20),
                INDEX idx_nome (nome),
                INDEX idx_cnpj (cnpj)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabela de fornecedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                razao_social VARCHAR(255),
                nome_fantasia VARCHAR(255),
                cnpj VARCHAR(20),
                ie VARCHAR(50),
                im VARCHAR(50),
                cep VARCHAR(10),
                rua VARCHAR(255),
                numero VARCHAR(20),
                complemento VARCHAR(100),
                bairro VARCHAR(100),
                cidade VARCHAR(100),
                estado VARCHAR(2),
                telefone VARCHAR(20),
                contato VARCHAR(20),
                email VARCHAR(255),
                endereco TEXT,
                documento VARCHAR(20),
                INDEX idx_nome (nome),
                INDEX idx_cnpj (cnpj)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabela de lançamentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                descricao TEXT NOT NULL,
                valor DECIMAL(15,2) NOT NULL,
                data_vencimento DATE NOT NULL,
                data_pagamento DATE,
                status VARCHAR(50) NOT NULL,
                categoria VARCHAR(255),
                subcategoria VARCHAR(255),
                conta_bancaria VARCHAR(255),
                pessoa VARCHAR(255),
                observacoes TEXT,
                num_documento VARCHAR(100),
                recorrente TINYINT DEFAULT 0,
                frequencia_recorrencia VARCHAR(50),
                data_criacao DATETIME NOT NULL,
                INDEX idx_tipo (tipo),
                INDEX idx_status (status),
                INDEX idx_data_vencimento (data_vencimento),
                INDEX idx_data_pagamento (data_pagamento),
                INDEX idx_categoria (categoria),
                INDEX idx_conta_bancaria (conta_bancaria)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    # === CONTAS BANCÁRIAS ===
    
    def adicionar_conta(self, conta: ContaBancaria) -> int:
        """Adiciona uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contas_bancarias (nome, banco, agencia, conta, saldo_inicial, data_criacao)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (conta.nome, conta.banco, conta.agencia, conta.conta, 
              float(conta.saldo_inicial), datetime.now()))
        
        conta_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return conta_id
    
    def listar_contas(self) -> List[ContaBancaria]:
        """Lista todas as contas bancárias ativas"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT nome, banco, agencia, conta, saldo_inicial
            FROM contas_bancarias
            WHERE ativa = 1
        """)
        
        contas = []
        for row in cursor.fetchall():
            conta = ContaBancaria(
                nome=row['nome'],
                banco=row['banco'],
                agencia=row['agencia'],
                conta=row['conta'],
                saldo_inicial=float(row['saldo_inicial'])
            )
            contas.append(conta)
        
        cursor.close()
        conn.close()
        return contas
    
    def atualizar_conta(self, nome_antigo: str, conta: ContaBancaria) -> bool:
        """Atualiza uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        """Remove uma conta bancária (marca como inativa)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE contas_bancarias SET ativa = 0 WHERE nome = %s", (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    # === CATEGORIAS ===
    
    def adicionar_categoria(self, categoria: Categoria) -> int:
        """Adiciona uma categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias)
        
        cursor.execute("""
            INSERT INTO categorias (nome, tipo, subcategorias)
            VALUES (%s, %s, %s)
        """, (categoria.nome, categoria.tipo.value, subcategorias_json))
        
        categoria_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return categoria_id
    
    def listar_categorias(self) -> List[Categoria]:
        """Lista todas as categorias"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT nome, tipo, subcategorias FROM categorias ORDER BY nome")
        
        categorias = []
        for row in cursor.fetchall():
            subcategorias = json.loads(row['subcategorias']) if row['subcategorias'] else []
            cat = Categoria(
                nome=row['nome'],
                tipo=TipoLancamento(row['tipo']),
                subcategorias=subcategorias
            )
            categorias.append(cat)
        
        cursor.close()
        conn.close()
        return categorias
    
    def excluir_categoria(self, nome: str) -> bool:
        """Remove uma categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM categorias WHERE nome = %s", (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    def atualizar_categoria(self, categoria: Categoria) -> bool:
        """Atualiza uma categoria existente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        subcategorias_json = json.dumps(categoria.subcategorias)
        
        cursor.execute("""
            UPDATE categorias 
            SET tipo = %s, subcategorias = %s 
            WHERE nome = %s
        """, (categoria.tipo.value, subcategorias_json, categoria.nome))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    def atualizar_nome_categoria(self, nome_antigo: str, nome_novo: str) -> bool:
        """Atualiza o nome de uma categoria e todos os lançamentos relacionados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE categorias SET nome = %s WHERE nome = %s", (nome_novo, nome_antigo))
            cursor.execute("UPDATE lancamentos SET categoria = %s WHERE categoria = %s", (nome_novo, nome_antigo))
            
            conn.commit()
            success = True
        except:
            conn.rollback()
            success = False
        finally:
            cursor.close()
            conn.close()
        
        return success
    
    # === CLIENTES ===
    
    def adicionar_cliente(self, dados: Dict[str, str]) -> int:
        """Adiciona um cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO clientes (
                nome, razao_social, nome_fantasia, cnpj, ie, im, cep, rua, numero,
                complemento, bairro, cidade, estado, telefone, contato, email, endereco, documento
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dados['nome'],
            dados.get('razao_social'),
            dados.get('nome_fantasia'),
            dados.get('cnpj'),
            dados.get('ie'),
            dados.get('im'),
            dados.get('cep'),
            dados.get('rua'),
            dados.get('numero'),
            dados.get('complemento'),
            dados.get('bairro'),
            dados.get('cidade'),
            dados.get('estado'),
            dados.get('telefone'),
            dados.get('contato'),
            dados.get('email'),
            dados.get('endereco'),
            dados.get('documento')
        ))
        
        cliente_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return cliente_id
    
    def listar_clientes(self) -> List[Dict]:
        """Lista todos os clientes"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM clientes ORDER BY nome")
        
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        return clientes
    
    def excluir_cliente(self, nome: str) -> bool:
        """Remove um cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM clientes WHERE nome = %s", (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    # === FORNECEDORES ===
    
    def adicionar_fornecedor(self, dados: Dict[str, str]) -> int:
        """Adiciona um fornecedor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO fornecedores (
                nome, razao_social, nome_fantasia, cnpj, ie, im, cep, rua, numero,
                complemento, bairro, cidade, estado, telefone, contato, email, endereco, documento
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dados['nome'],
            dados.get('razao_social'),
            dados.get('nome_fantasia'),
            dados.get('cnpj'),
            dados.get('ie'),
            dados.get('im'),
            dados.get('cep'),
            dados.get('rua'),
            dados.get('numero'),
            dados.get('complemento'),
            dados.get('bairro'),
            dados.get('cidade'),
            dados.get('estado'),
            dados.get('telefone'),
            dados.get('contato'),
            dados.get('email'),
            dados.get('endereco'),
            dados.get('documento')
        ))
        
        fornecedor_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return fornecedor_id
    
    def listar_fornecedores(self) -> List[Dict]:
        """Lista todos os fornecedores"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM fornecedores ORDER BY nome")
        
        fornecedores = cursor.fetchall()
        cursor.close()
        conn.close()
        return fornecedores
    
    def excluir_fornecedor(self, nome: str) -> bool:
        """Remove um fornecedor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM fornecedores WHERE nome = %s", (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    # === LANÇAMENTOS ===
    
    def adicionar_lancamento(self, lancamento: Lancamento) -> int:
        """Adiciona um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_vencimento = lancamento.data_vencimento.date() if isinstance(lancamento.data_vencimento, datetime) else lancamento.data_vencimento
        
        cursor.execute("""
            INSERT INTO lancamentos (
                tipo, descricao, valor, data_vencimento, status, categoria, subcategoria,
                conta_bancaria, pessoa, observacoes, num_documento, recorrente,
                frequencia_recorrencia, data_criacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            lancamento.tipo.value,
            lancamento.descricao,
            float(lancamento.valor),
            data_vencimento,
            lancamento.status.value,
            lancamento.categoria,
            lancamento.subcategoria,
            lancamento.conta_bancaria,
            lancamento.pessoa,
            lancamento.observacoes,
            lancamento.num_documento,
            1 if lancamento.recorrente else 0,  # type: ignore
            lancamento.frequencia_recorrencia,  # type: ignore
            datetime.now()
        ))
        
        lancamento_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return lancamento_id
    
    def listar_lancamentos(self) -> List[Lancamento]:
        """Lista todos os lançamentos"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM lancamentos ORDER BY data_vencimento DESC")
        
        lancamentos = []
        for row in cursor.fetchall():
            lanc = Lancamento(
                descricao=row['descricao'],
                valor=float(row['valor']),
                tipo=TipoLancamento(row['tipo']),
                data_vencimento=row['data_vencimento'],
                categoria=row['categoria'],
                subcategoria=row['subcategoria'],
                status=StatusLancamento(row['status']),  # type: ignore
                conta_bancaria=row['conta_bancaria'],
                pessoa=row['pessoa'],
                observacoes=row['observacoes'],
                num_documento=row['num_documento'],
                recorrente=bool(row['recorrente']),  # type: ignore
                frequencia_recorrencia=row['frequencia_recorrencia']  # type: ignore
            )
            lanc.id = row['id']
            lanc.data_pagamento = row['data_pagamento']
            lancamentos.append(lanc)
        
        cursor.close()
        conn.close()
        return lancamentos
    
    def excluir_lancamento(self, lancamento_id: int) -> bool:
        """Remove um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (lancamento_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    def pagar_lancamento(self, lancamento_id: int, conta: str, data_pagamento: datetime, juros: float = 0) -> bool:
        """Marca um lançamento como pago"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_pag = data_pagamento.date() if isinstance(data_pagamento, datetime) else data_pagamento
        
        cursor.execute("""
            UPDATE lancamentos 
            SET status = %s, data_pagamento = %s, conta_bancaria = %s
            WHERE id = %s
        """, (StatusLancamento.PAGO.value, data_pag, conta, lancamento_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    def cancelar_lancamento(self, lancamento_id: int) -> bool:
        """Cancela um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lancamentos 
            SET status = %s 
            WHERE id = %s
        """, (StatusLancamento.CANCELADO.value, lancamento_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        conn.close()
        return success
    
    def migrar_dados_json(self):
        """Migra dados de arquivos JSON para o banco"""
        pass


# Instância global do gerenciador
_db_manager = None

def _get_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# Funções de conveniência que usam a instância global
def criar_tabelas():
    _get_manager().criar_tabelas()

def get_connection():
    return _get_manager().get_connection()

def adicionar_conta(conta: ContaBancaria) -> int:
    return _get_manager().adicionar_conta(conta)

def listar_contas() -> List[ContaBancaria]:
    return _get_manager().listar_contas()

def excluir_conta(nome: str) -> bool:
    return _get_manager().excluir_conta(nome)

def adicionar_categoria(categoria: Categoria) -> int:
    return _get_manager().adicionar_categoria(categoria)

def listar_categorias() -> List[Categoria]:
    return _get_manager().listar_categorias()

def excluir_categoria(nome: str) -> bool:
    return _get_manager().excluir_categoria(nome)

def atualizar_categoria(categoria: Categoria) -> bool:
    return _get_manager().atualizar_categoria(categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    return _get_manager().atualizar_nome_categoria(nome_antigo, nome_novo)

def adicionar_cliente(cliente: Dict) -> int:
    return _get_manager().adicionar_cliente(cliente)

def listar_clientes() -> List[Dict]:
    return _get_manager().listar_clientes()

def adicionar_fornecedor(fornecedor: Dict) -> int:
    return _get_manager().adicionar_fornecedor(fornecedor)

def listar_fornecedores() -> List[Dict]:
    return _get_manager().listar_fornecedores()

def adicionar_lancamento(lancamento: Lancamento) -> int:
    return _get_manager().adicionar_lancamento(lancamento)

def listar_lancamentos() -> List[Lancamento]:
    return _get_manager().listar_lancamentos()

def excluir_lancamento(lancamento_id: int) -> bool:
    return _get_manager().excluir_lancamento(lancamento_id)

def pagar_lancamento(lancamento_id: int, conta: str, data_pagamento: datetime, juros: float = 0) -> bool:
    return _get_manager().pagar_lancamento(lancamento_id, conta, data_pagamento, juros)

def cancelar_lancamento(lancamento_id: int) -> bool:
    return _get_manager().cancelar_lancamento(lancamento_id)

def migrar_dados_json():
    return _get_manager().migrar_dados_json()

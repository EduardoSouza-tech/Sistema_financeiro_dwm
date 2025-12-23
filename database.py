"""
Módulo de gerenciamento do banco de dados
Suporta SQLite, MySQL e PostgreSQL
"""
import os
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from models import (
    ContaBancaria, Lancamento, Categoria,
    TipoLancamento, StatusLancamento
)
from config import DATABASE_TYPE

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
    'DatabaseManager'
]


# Importar o DatabaseManager correto baseado na configuração
def _get_database_manager():
    """Retorna o DatabaseManager correto baseado na configuração"""
    if DATABASE_TYPE == 'postgresql':
        from database_postgresql import DatabaseManager as PostgreSQLManager
        return PostgreSQLManager
    elif DATABASE_TYPE == 'mysql':
        from database_mysql import DatabaseManager as MySQLManager
        return MySQLManager
    else:  # sqlite (padrão)
        return _SQLiteDatabaseManager

# Manter a classe SQLite com novo nome interno
class _SQLiteDatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "sistema_financeiro.db"):
        self.db_path = db_path
        self.criar_tabelas()
    
    def get_connection(self):
        """Cria uma conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn
    
    def criar_tabelas(self):
        """Cria as tabelas no banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de contas bancárias
        cursor.execute("""
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
        """)
        
        # Tabela de categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL,
                subcategorias TEXT
            )
        """)
        
        # Tabela de clientes
        cursor.execute("""
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
        """)
        
        # Tabela de fornecedores
        cursor.execute("""
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
        """)
        
        # Tabela de lançamentos
        cursor.execute("""
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
        """)
        
        # Adicionar coluna num_documento se não existir (para migração de bancos antigos)
        try:
            cursor.execute("ALTER TABLE lancamentos ADD COLUMN num_documento TEXT")
            conn.commit()
        except:
            pass  # Coluna já existe
        
        # Adicionar colunas de inativação em clientes
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN ativo INTEGER DEFAULT 1")
            conn.commit()
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN data_inativacao TEXT")
            conn.commit()
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN motivo_inativacao TEXT")
            conn.commit()
        except:
            pass
        
        # Adicionar colunas de inativação em fornecedores
        try:
            cursor.execute("ALTER TABLE fornecedores ADD COLUMN ativo INTEGER DEFAULT 1")
            conn.commit()
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE fornecedores ADD COLUMN data_inativacao TEXT")
            conn.commit()
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE fornecedores ADD COLUMN motivo_inativacao TEXT")
            conn.commit()
        except:
            pass
        
        # Tabela de contratos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                cliente_id INTEGER,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data_inicio TEXT NOT NULL,
                data_fim TEXT,
                status TEXT DEFAULT 'ativo',
                observacoes TEXT,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        
        # Tabela de agenda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                data_evento TEXT NOT NULL,
                hora_inicio TEXT,
                hora_fim TEXT,
                local TEXT,
                tipo TEXT DEFAULT 'evento',
                status TEXT DEFAULT 'agendado',
                cliente_id INTEGER,
                observacoes TEXT,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        
        # Tabela de produtos (estoque)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                descricao TEXT,
                categoria TEXT,
                unidade TEXT DEFAULT 'un',
                quantidade REAL DEFAULT 0,
                quantidade_minima REAL DEFAULT 0,
                preco_custo REAL DEFAULT 0,
                preco_venda REAL DEFAULT 0,
                fornecedor_id INTEGER,
                ativo INTEGER DEFAULT 1,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
            )
        """)
        
        # Tabela de kits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco REAL DEFAULT 0,
                ativo INTEGER DEFAULT 1,
                data_criacao TEXT NOT NULL
            )
        """)
        
        # Tabela de itens de kits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kit_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kit_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade REAL NOT NULL,
                FOREIGN KEY (kit_id) REFERENCES kits(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        """)
        
        # Tabela de tags
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                cor TEXT DEFAULT '#3498db',
                descricao TEXT,
                data_criacao TEXT NOT NULL
            )
        """)
        
        # Tabela de templates de equipe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates_equipe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                descricao TEXT,
                conteudo TEXT NOT NULL,
                tipo TEXT DEFAULT 'geral',
                ativo INTEGER DEFAULT 1,
                data_criacao TEXT NOT NULL
            )
        """)
        
        # Tabela de sessões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                data_sessao TEXT NOT NULL,
                duracao INTEGER DEFAULT 60,
                cliente_id INTEGER,
                valor REAL DEFAULT 0,
                status TEXT DEFAULT 'agendada',
                observacoes TEXT,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        
        # Tabela de comissões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comissoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                percentual REAL DEFAULT 0,
                data_referencia TEXT NOT NULL,
                data_pagamento TEXT,
                status TEXT DEFAULT 'pendente',
                beneficiario TEXT,
                lancamento_id INTEGER,
                observacoes TEXT,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (lancamento_id) REFERENCES lancamentos(id)
            )
        """)
        
        # Tabela de relação sessão-equipe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessao_equipe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessao_id INTEGER NOT NULL,
                membro_nome TEXT NOT NULL,
                funcao TEXT,
                observacoes TEXT,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (sessao_id) REFERENCES sessoes(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    # === CONTAS BANCÁRIAS ===
    
    def adicionar_conta(self, conta: ContaBancaria) -> int:
        """Adiciona uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contas_bancarias (nome, banco, agencia, conta, saldo_inicial, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (conta.nome, conta.banco, conta.agencia, conta.conta, 
              float(conta.saldo_inicial), datetime.now().isoformat()))
        
        conta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conta_id  # type: ignore
    
    def listar_contas(self) -> List[ContaBancaria]:
        """Lista todas as contas bancárias ativas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        
        conn.close()
        return contas
    
    def buscar_conta(self, nome: str) -> Optional[ContaBancaria]:
        """Busca uma conta bancária por nome"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nome, banco, agencia, conta, saldo_inicial
            FROM contas_bancarias
            WHERE nome = ? AND ativa = 1
        """, (nome,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ContaBancaria(
                nome=row['nome'],
                banco=row['banco'],
                agencia=row['agencia'],
                conta=row['conta'],
                saldo_inicial=float(row['saldo_inicial'])
            )
        return None
    
    def atualizar_conta(self, nome_antigo: str, conta: ContaBancaria) -> bool:
        """Atualiza uma conta bancária"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se o nome mudou, verificar se o novo nome já existe
        if nome_antigo != conta.nome:
            cursor.execute("SELECT COUNT(*) FROM contas_bancarias WHERE nome = ? AND nome != ?", 
                         (conta.nome, nome_antigo))
            if cursor.fetchone()[0] > 0:
                conn.close()
                raise ValueError("Já existe uma conta com este nome")
        
        cursor.execute("""
            UPDATE contas_bancarias
            SET nome = ?, banco = ?, agencia = ?, conta = ?, saldo_inicial = ?
            WHERE nome = ?
        """, (conta.nome, conta.banco, conta.agencia, conta.conta,
              float(conta.saldo_inicial), nome_antigo))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def excluir_conta(self, nome: str) -> bool:
        """Desativa uma conta bancária (soft delete)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE contas_bancarias
            SET ativa = 0
            WHERE nome = ?
        """, (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # === CATEGORIAS ===
    
    def adicionar_categoria(self, categoria: Categoria) -> int:
        """Adiciona uma categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        import json
        # Normalizar nome: uppercase e remover espaços extras
        nome_normalizado = categoria.nome.strip().upper()
        
        # Verificar se já existe (case-insensitive)
        cursor.execute("""
            SELECT nome FROM categorias WHERE UPPER(TRIM(nome)) = ?
        """, (nome_normalizado,))
        existente = cursor.fetchone()
        if existente:
            conn.close()
            raise ValueError(f"Já existe uma categoria com o nome '{existente[0]}'")
        
        subcategorias_json = json.dumps(categoria.subcategorias)
        
        cursor.execute("""
            INSERT INTO categorias (nome, tipo, subcategorias)
            VALUES (?, ?, ?)
        """, (nome_normalizado, categoria.tipo.value, subcategorias_json))
        
        categoria_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return categoria_id  # type: ignore
    
    def listar_categorias(self) -> List[Categoria]:
        """Lista todas as categorias"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nome, tipo, subcategorias FROM categorias")
        
        import json
        categorias = []
        for row in cursor.fetchall():
            tipo = TipoLancamento(row['tipo'].lower())
            subcategorias = json.loads(row['subcategorias']) if row['subcategorias'] else []
            
            categoria = Categoria(
                nome=row['nome'],
                tipo=tipo,
                subcategorias=subcategorias
            )
            categorias.append(categoria)
        
        conn.close()
        return categorias
    
    def excluir_categoria(self, nome: str) -> bool:
        """Remove uma categoria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Normalizar nome
        nome_normalizado = nome.strip().upper()
        
        cursor.execute("DELETE FROM categorias WHERE UPPER(TRIM(nome)) = ?", (nome_normalizado,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def atualizar_categoria(self, categoria: Categoria) -> bool:
        """Atualiza uma categoria existente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        import json
        subcategorias_json = json.dumps(categoria.subcategorias)
        
        # Normalizar nome
        nome_normalizado = categoria.nome.strip().upper()
        
        cursor.execute("""
            UPDATE categorias 
            SET tipo = ?, subcategorias = ?
            WHERE UPPER(TRIM(nome)) = ?
        """, (categoria.tipo.value, subcategorias_json, nome_normalizado))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def atualizar_nome_categoria(self, nome_antigo: str, nome_novo: str) -> bool:
        """Atualiza o nome de uma categoria e seus relacionamentos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Normalizar nomes
        nome_antigo_normalizado = nome_antigo.strip().upper()
        nome_novo_normalizado = nome_novo.strip().upper()
        
        try:
            # Atualizar o nome da categoria
            cursor.execute("""
                UPDATE categorias 
                SET nome = ?
                WHERE UPPER(TRIM(nome)) = ?
            """, (nome_novo_normalizado, nome_antigo_normalizado))
            
            # Atualizar os lançamentos que usam esta categoria
            cursor.execute("""
                UPDATE lancamentos 
                SET categoria = ?
                WHERE UPPER(TRIM(categoria)) = ?
            """, (nome_novo_normalizado, nome_antigo_normalizado))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.close()
        return cliente_id  # type: ignore
    
    def listar_clientes(self, ativos: bool = True) -> List[Dict]:
        """Lista clientes ativos ou inativos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        status = 1 if ativos else 0
        cursor.execute("SELECT * FROM clientes WHERE ativo = ? ORDER BY nome", (status,))
        
        clientes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return clientes
    
    def inativar_cliente(self, nome: str, motivo: str) -> tuple[bool, str]:
        """Inativa um cliente com motivo - Pode inativar sempre"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE clientes 
            SET ativo = 0, data_inativacao = ?, motivo_inativacao = ?
            WHERE nome = ?
        """, (datetime.now().isoformat(), motivo, nome))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return (success, "Cliente inativado com sucesso" if success else "Cliente não encontrado")
    
    def reativar_cliente(self, nome: str) -> bool:
        """Reativa um cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE clientes 
            SET ativo = 1, data_inativacao = NULL, motivo_inativacao = NULL
            WHERE nome = ?
        """, (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def excluir_cliente(self, nome: str) -> tuple[bool, str]:
        """Exclui um cliente permanentemente - Só permite se não houver lançamentos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar se existem lançamentos vinculados
        cursor.execute("""
            SELECT COUNT(*) as total FROM lancamentos 
            WHERE pessoa = ?
        """, (nome,))
        count = cursor.fetchone()['total']
        
        if count > 0:
            conn.close()
            return (False, f"Não é possível excluir. Existem {count} lançamento(s) vinculado(s) a este cliente. Inative ao invés de excluir.")
        
        cursor.execute("DELETE FROM clientes WHERE nome = ?", (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return (success, "Cliente excluído com sucesso" if success else "Cliente não encontrado")
    
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.close()
        return fornecedor_id  # type: ignore
    
    def listar_fornecedores(self, ativos: bool = True) -> List[Dict]:
        """Lista fornecedores ativos ou inativos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        status = 1 if ativos else 0
        cursor.execute("SELECT * FROM fornecedores WHERE ativo = ? ORDER BY nome", (status,))
        
        fornecedores = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return fornecedores
    
    def inativar_fornecedor(self, nome: str, motivo: str) -> tuple[bool, str]:
        """Inativa um fornecedor com motivo - Pode inativar sempre"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fornecedores 
            SET ativo = 0, data_inativacao = ?, motivo_inativacao = ?
            WHERE nome = ?
        """, (datetime.now().isoformat(), motivo, nome))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return (success, "Fornecedor inativado com sucesso" if success else "Fornecedor não encontrado")
    
    def reativar_fornecedor(self, nome: str) -> bool:
        """Reativa um fornecedor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fornecedores 
            SET ativo = 1, data_inativacao = NULL, motivo_inativacao = NULL
            WHERE nome = ?
        """, (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def excluir_fornecedor(self, nome: str) -> tuple[bool, str]:
        """Exclui um fornecedor permanentemente - Só permite se não houver lançamentos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar se existem lançamentos vinculados
        cursor.execute("""
            SELECT COUNT(*) as total FROM lancamentos 
            WHERE pessoa = ?
        """, (nome,))
        count = cursor.fetchone()['total']
        
        if count > 0:
            conn.close()
            return (False, f"Não é possível excluir. Existem {count} lançamento(s) vinculado(s) a este fornecedor. Inative ao invés de excluir.")
        
        cursor.execute("DELETE FROM fornecedores WHERE nome = ?", (nome,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return (success, "Fornecedor excluído com sucesso" if success else "Fornecedor não encontrado")
    
    # === LANÇAMENTOS ===
    
    def adicionar_lancamento(self, lancamento: Lancamento) -> int:
        """Adiciona um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_vencimento = lancamento.data_vencimento.isoformat() if isinstance(lancamento.data_vencimento, (datetime, date)) else lancamento.data_vencimento
        data_pagamento = lancamento.data_pagamento.isoformat() if lancamento.data_pagamento and isinstance(lancamento.data_pagamento, (datetime, date)) else None
        
        cursor.execute("""
            INSERT INTO lancamentos (
                tipo, descricao, valor, data_vencimento, data_pagamento,
                status, categoria, subcategoria, conta_bancaria, pessoa,
                observacoes, num_documento, recorrente, frequencia_recorrencia, data_criacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lancamento.tipo.value,
            lancamento.descricao,
            float(lancamento.valor),
            data_vencimento,
            data_pagamento,
            lancamento.status.value,
            lancamento.categoria,
            lancamento.subcategoria,
            lancamento.conta_bancaria,
            lancamento.pessoa,
            lancamento.observacoes,
            getattr(lancamento, 'num_documento', ''),
            0,  # recorrente (não implementado)
            None,  # frequencia_recorrencia (não implementado)
            datetime.now().isoformat()
        ))
        
        lancamento_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return lancamento_id  # type: ignore
    
    def listar_lancamentos(self) -> List[Lancamento]:
        """Lista todos os lançamentos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM lancamentos ORDER BY data_vencimento DESC")
        
        lancamentos = []
        for row in cursor.fetchall():
            # Converter datas para date (não datetime) para compatibilidade
            data_vencimento = datetime.fromisoformat(row['data_vencimento']).date() if row['data_vencimento'] else date.today()
            data_pagamento = datetime.fromisoformat(row['data_pagamento']).date() if row['data_pagamento'] else None
            
            # Converter Row para dict para facilitar acesso
            row_dict = dict(row)
            
            lancamento = Lancamento(
                descricao=row_dict['descricao'],
                valor=float(row_dict['valor']),
                tipo=TipoLancamento(row_dict['tipo'].lower()),
                categoria=row_dict['categoria'],
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                conta_bancaria=row_dict['conta_bancaria'],
                pessoa=row_dict['pessoa'],
                observacoes=row_dict['observacoes'],
                num_documento=row_dict.get('num_documento', ''),
                subcategoria=row_dict['subcategoria']
            )
            # Define o ID do banco de dados
            lancamento.id = row_dict['id']
            # Define status manualmente - converter para lowercase para compatibilidade
            status_value = row_dict['status'].lower() if row_dict['status'] else 'pendente'
            lancamento.status = StatusLancamento(status_value)
            lancamentos.append(lancamento)
        
        conn.close()
        return lancamentos
    
    def atualizar_lancamento(self, lancamento_id: int, lancamento: Lancamento) -> bool:
        """Atualiza um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_vencimento = lancamento.data_vencimento.isoformat() if isinstance(lancamento.data_vencimento, (datetime, date)) else lancamento.data_vencimento
        data_pagamento = lancamento.data_pagamento.isoformat() if lancamento.data_pagamento and isinstance(lancamento.data_pagamento, (datetime, date)) else None
        
        cursor.execute("""
            UPDATE lancamentos SET
                tipo = ?, descricao = ?, valor = ?, data_vencimento = ?,
                data_pagamento = ?, status = ?, categoria = ?, subcategoria = ?,
                conta_bancaria = ?, pessoa = ?, observacoes = ?, num_documento = ?,
                recorrente = ?, frequencia_recorrencia = ?
            WHERE id = ?
        """, (
            lancamento.tipo.value,
            lancamento.descricao,
            float(lancamento.valor),
            data_vencimento,
            data_pagamento,
            lancamento.status.value,
            lancamento.categoria,
            lancamento.subcategoria,
            lancamento.conta_bancaria,
            lancamento.pessoa,
            lancamento.observacoes,
            getattr(lancamento, 'num_documento', ''),
            0,  # recorrente (não implementado)
            None,  # frequencia_recorrencia (não implementado)
            lancamento_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def excluir_lancamento(self, lancamento_id: int) -> bool:
        """Remove um lançamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print(f"[DATABASE] Executando DELETE para lançamento ID: {lancamento_id}")
        cursor.execute("DELETE FROM lancamentos WHERE id = ?", (lancamento_id,))
        
        rows_affected = cursor.rowcount
        print(f"[DATABASE] Linhas afetadas: {rows_affected}")
        
        conn.commit()
        conn.close()
        
        success = rows_affected > 0
        print(f"[DATABASE] Sucesso: {success}")
        return success
    
    # === MIGRAÇÃO ===
    
    def migrar_dados_json(self, arquivo_json: str):
        """Migra dados do arquivo JSON para o banco de dados"""
        import json
        
        if not os.path.exists(arquivo_json):
            print(f"Arquivo {arquivo_json} não encontrado")
            return
        
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Usar uma única conexão durante toda a migração
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Migrar contas
            for conta_data in dados.get('contas', []):
                try:
                    cursor.execute("""
                        INSERT INTO contas_bancarias (nome, banco, agencia, conta, saldo_inicial)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        conta_data['nome'],
                        conta_data['banco'],
                        conta_data['agencia'],
                        conta_data['conta'],
                        float(conta_data['saldo_inicial'])
                    ))
                except:
                    pass
            
            # Migrar categorias
            for cat_data in dados.get('categorias', []):
                try:
                    import json as json_module
                    cursor.execute("""
                        INSERT INTO categorias (nome, tipo, subcategorias)
                        VALUES (?, ?, ?)
                    """, (
                        cat_data['nome'],
                        cat_data['tipo'],
                        json_module.dumps(cat_data.get('subcategorias', []))
                    ))
                except:
                    pass
            
            # Migrar clientes
            for cliente in dados.get('clientes', []):
                try:
                    cursor.execute("""
                        INSERT INTO clientes (nome, cpf, email, telefone, endereco)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        cliente.get('nome', ''),
                        cliente.get('cpf', ''),
                        cliente.get('email', ''),
                        cliente.get('telefone', ''),
                        cliente.get('endereco', '')
                    ))
                except:
                    pass
            
            # Migrar fornecedores
            for fornecedor in dados.get('fornecedores', []):
                try:
                    cursor.execute("""
                        INSERT INTO fornecedores (nome, cnpj, email, telefone, endereco)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        fornecedor.get('nome', ''),
                        fornecedor.get('cnpj', ''),
                        fornecedor.get('email', ''),
                        fornecedor.get('telefone', ''),
                        fornecedor.get('endereco', '')
                    ))
                except:
                    pass
            
            # Migrar lançamentos
            for lanc_data in dados.get('lancamentos', []):
                try:
                    data_venc = datetime.fromisoformat(lanc_data['data_vencimento']) if lanc_data.get('data_vencimento') else datetime.now()
                    data_pag = datetime.fromisoformat(lanc_data['data_pagamento']) if lanc_data.get('data_pagamento') else None
                    
                    # Determinar status
                    status = lanc_data.get('status', 'PENDENTE')
                    if status.upper() == 'PAGO':
                        status = 'PAGO'
                    else:
                        status = 'PENDENTE'
                    
                    cursor.execute("""
                        INSERT INTO lancamentos (
                            tipo, descricao, valor, data_vencimento, data_pagamento,
                            status, categoria, subcategoria, conta_bancaria, pessoa,
                            observacoes, num_documento, recorrente, frequencia_recorrencia, data_criacao
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        lanc_data['tipo'],
                        lanc_data['descricao'],
                        float(lanc_data['valor']),
                        data_venc.isoformat(),
                        data_pag.isoformat() if data_pag else None,
                        status,
                        lanc_data.get('categoria', ''),
                        lanc_data.get('subcategoria', ''),
                        lanc_data.get('conta_bancaria'),
                        lanc_data.get('pessoa', ''),
                        lanc_data.get('observacoes', ''),
                        lanc_data.get('num_documento', ''),
                        0,
                        None,
                        datetime.now().isoformat()
                    ))
                except Exception as e:
                    print(f"Erro ao migrar lançamento: {e}")
            
            conn.commit()
            print("Migração concluída com sucesso!")
        
        except Exception as e:
            conn.rollback()
            print(f"Erro durante migração: {e}")
        finally:
            conn.close()


import os

# As funções de nível de módulo (wrappers) usarão a instância global definida no final do arquivo
def criar_tabelas():
    """Cria as tabelas do banco de dados"""
    _db.criar_tabelas()

def get_connection():
    """Obtém uma conexão com o banco de dados"""
    return _db.get_connection()

def adicionar_conta(conta: ContaBancaria) -> int:
    """Adiciona uma conta bancária"""
    return _db.adicionar_conta(conta)

def listar_contas() -> List[ContaBancaria]:
    """Lista todas as contas bancárias"""
    return _db.listar_contas()

def excluir_conta(nome: str) -> bool:
    """Exclui uma conta bancária"""
    return _db.excluir_conta(nome)

def adicionar_categoria(categoria: Categoria) -> int:
    """Adiciona uma categoria"""
    return _db.adicionar_categoria(categoria)

def listar_categorias() -> List[Categoria]:
    """Lista todas as categorias"""
    return _db.listar_categorias()

def adicionar_cliente(cliente: Dict) -> int:
    """Adiciona um cliente"""
    return _db.adicionar_cliente(cliente)

def listar_clientes() -> List[Dict]:
    """Lista todos os clientes"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def adicionar_fornecedor(fornecedor: Dict) -> int:
    """Adiciona um fornecedor"""
    return _db.adicionar_fornecedor(fornecedor)

def listar_fornecedores() -> List[Dict]:
    """Lista todos os fornecedores"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fornecedores')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def adicionar_lancamento(lancamento: Lancamento) -> int:
    """Adiciona um lançamento"""
    return _db.adicionar_lancamento(lancamento)

def listar_lancamentos() -> List[Lancamento]:
    """Lista todos os lançamentos"""
    return _db.listar_lancamentos()

def obter_lancamento(lancamento_id: int):
    """Obtém um lançamento específico por ID"""
    print(f"\n🔍 database.py obter_lancamento() wrapper chamada")
    print(f"   lancamento_id: {lancamento_id}")
    print(f"   DATABASE_TYPE: {DATABASE_TYPE}")
    
    # Usar o DatabaseManager correto baseado na configuração
    db = DatabaseManager()
    print(f"   DatabaseManager type: {type(db)}")
    
    # Chamar o método do DatabaseManager
    resultado = db.obter_lancamento(lancamento_id)
    print(f"   Resultado: {resultado}")
    print(f"   Tipo resultado: {type(resultado)}\n")
    
    return resultado

def excluir_lancamento(lancamento_id: int) -> bool:
    """Exclui um lançamento"""
    return _db.excluir_lancamento(lancamento_id)

def pagar_lancamento(lancamento_id: int, conta: str, data_pagamento: datetime, juros: float = 0, desconto: float = 0, observacoes: str = '') -> bool:
    """Marca um lançamento como pago e registra a conta bancária"""
    print(f"\n🔍 database.py pagar_lancamento() wrapper chamada")
    print(f"   DATABASE_TYPE: {DATABASE_TYPE}")
    
    # Usar o DatabaseManager correto baseado na configuração
    db = DatabaseManager()
    print(f"   DatabaseManager type: {type(db)}")
    
    # Converter datetime para date se necessário
    if isinstance(data_pagamento, datetime):
        data_pagamento = data_pagamento.date()
    
    # Chamar o método do DatabaseManager
    return db.pagar_lancamento(lancamento_id, conta, data_pagamento, juros, desconto, observacoes)

def cancelar_lancamento(lancamento_id: int) -> bool:
    """Cancela um lançamento (remove data de pagamento)"""
    print(f"\n🔍 database.py cancelar_lancamento() wrapper chamada")
    print(f"   DATABASE_TYPE: {DATABASE_TYPE}")
    
    # Usar o DatabaseManager correto baseado na configuração
    db = DatabaseManager()
    print(f"   DatabaseManager type: {type(db)}")
    
    return db.cancelar_lancamento(lancamento_id)

def excluir_categoria(nome: str) -> bool:
    """Exclui uma categoria"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE nome = ?", (nome,))
    success = cursor.rowcount > 0
    conn.commit()
# ==================== FUNÇÕES CRUD - MENU OPERACIONAL ====================
# Todas as funções delegam para o database específico (PostgreSQL, MySQL ou SQLite)

def _delegate_to_specific_db(func_name, *args, **kwargs):
    """Função auxiliar para delegar para o database correto"""
    if DATABASE_TYPE == 'postgresql':
        import database_postgresql
        return getattr(database_postgresql, func_name)(*args, **kwargs)
    elif DATABASE_TYPE == 'mysql':
        import database_mysql
        return getattr(database_mysql, func_name)(*args, **kwargs)
    else:  # sqlite - precisa implementar aqui
        raise NotImplementedError(f"Função {func_name} não implementada para SQLite. Use PostgreSQL ou MySQL em produção.")

# ===== CONTRATOS =====
def adicionar_contrato(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_contrato', dados)

def listar_contratos() -> List[Dict]:
    return _delegate_to_specific_db('listar_contratos')

def atualizar_contrato(contrato_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_contrato', contrato_id, dados)

def deletar_contrato(contrato_id: int) -> bool:
    return _delegate_to_specific_db('deletar_contrato', contrato_id)

# ===== AGENDA =====
def adicionar_agenda(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_agenda', dados)

def listar_agenda() -> List[Dict]:
    return _delegate_to_specific_db('listar_agenda')

def atualizar_agenda(agenda_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_agenda', agenda_id, dados)

def deletar_agenda(agenda_id: int) -> bool:
    return _delegate_to_specific_db('deletar_agenda', agenda_id)

# ===== PRODUTOS =====
def adicionar_produto(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_produto', dados)

def listar_produtos() -> List[Dict]:
    return _delegate_to_specific_db('listar_produtos')

def atualizar_produto(produto_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_produto', produto_id, dados)

def deletar_produto(produto_id: int) -> bool:
    return _delegate_to_specific_db('deletar_produto', produto_id)

# ===== KITS =====
def adicionar_kit(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_kit', dados)

def listar_kits() -> List[Dict]:
    return _delegate_to_specific_db('listar_kits')

def atualizar_kit(kit_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_kit', kit_id, dados)

def deletar_kit(kit_id: int) -> bool:
    return _delegate_to_specific_db('deletar_kit', kit_id)

# ===== TAGS =====
def adicionar_tag(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_tag', dados)

def listar_tags() -> List[Dict]:
    return _delegate_to_specific_db('listar_tags')

def atualizar_tag(tag_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_tag', tag_id, dados)

def deletar_tag(tag_id: int) -> bool:
    return _delegate_to_specific_db('deletar_tag', tag_id)

# ===== TEMPLATES DE EQUIPE =====
def adicionar_template(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_template', dados)

def listar_templates() -> List[Dict]:
    return _delegate_to_specific_db('listar_templates')

def atualizar_template(template_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_template', template_id, dados)

def deletar_template(template_id: int) -> bool:
    return _delegate_to_specific_db('deletar_template', template_id)

# ===== SESSÕES =====
def adicionar_sessao(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_sessao', dados)

def listar_sessoes() -> List[Dict]:
    return _delegate_to_specific_db('listar_sessoes')

def atualizar_sessao(sessao_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_sessao', sessao_id, dados)

def deletar_sessao(sessao_id: int) -> bool:
    return _delegate_to_specific_db('deletar_sessao', sessao_id)

# ===== COMISSÕES =====
def adicionar_comissao(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_comissao', dados)

def listar_comissoes() -> List[Dict]:
    return _delegate_to_specific_db('listar_comissoes')

def atualizar_comissao(comissao_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_comissao', comissao_id, dados)

def deletar_comissao(comissao_id: int) -> bool:
    return _delegate_to_specific_db('deletar_comissao', comissao_id)

# ===== SESSÃO EQUIPE =====
def adicionar_sessao_equipe(dados: Dict) -> int:
    return _delegate_to_specific_db('adicionar_sessao_equipe', dados)

def listar_sessao_equipe(sessao_id: int = None) -> List[Dict]:
    return _delegate_to_specific_db('listar_sessao_equipe', sessao_id)

def atualizar_sessao_equipe(membro_id: int, dados: Dict) -> bool:
    return _delegate_to_specific_db('atualizar_sessao_equipe', membro_id, dados)

def deletar_sessao_equipe(membro_id: int) -> bool:
    return _delegate_to_specific_db('deletar_sessao_equipe', membro_id)


# ==================== FUNÇÕES ANTIGAS (mantidas para compatibilidade) ====================

def atualizar_categoria(categoria: Categoria) -> bool:
    """Atualiza uma categoria existente"""
    return _db.atualizar_categoria(categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    """Atualiza o nome de uma categoria e seus relacionamentos"""
    return _db.atualizar_nome_categoria(nome_antigo, nome_novo)


# ==================== FUNÇÕES DE CLIENTES E FORNECEDORES (implementação SQLite antiga) ====================

def atualizar_cliente(nome_antigo: str, cliente: Dict) -> bool:
    """Atualiza um cliente existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    novo_nome = cliente.get('nome', cliente.get('razao_social', ''))
    
    print(f"\n=== atualizar_cliente (database.py) ===")
    """Lista todos os eventos da agenda"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.id, a.titulo, a.descricao, a.data_evento, a.hora_inicio, a.hora_fim, a.local, 
               a.tipo, a.status, a.cliente_id, cl.nome as cliente_nome, a.observacoes, a.data_criacao
        FROM agenda a
        LEFT JOIN clientes cl ON a.cliente_id = cl.id
        ORDER BY a.data_evento DESC, a.hora_inicio DESC
    """)
    
    eventos = []
    for row in cursor.fetchall():
        eventos.append({
            'id': row[0],
            'titulo': row[1],
            'descricao': row[2],
            'data_evento': row[3],
            'hora_inicio': row[4],
            'hora_fim': row[5],
            'local': row[6],
            'tipo': row[7],
            'status': row[8],
            'cliente_id': row[9],
            'cliente_nome': row[10],
            'observacoes': row[11],
            'data_criacao': row[12]
        })
    
    conn.close()
    return eventos

def atualizar_agenda(id: int, agenda: Dict) -> bool:
    """Atualiza um evento da agenda"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE agenda
        SET titulo = ?, descricao = ?, data_evento = ?, hora_inicio = ?, hora_fim = ?, local = ?, tipo = ?, status = ?, cliente_id = ?, observacoes = ?
        WHERE id = ?
    """, (
        agenda['titulo'],
        agenda.get('descricao'),
        agenda['data_evento'],
        agenda.get('hora_inicio'),
        agenda.get('hora_fim'),
        agenda.get('local'),
        agenda.get('tipo', 'evento'),
        agenda.get('status', 'agendado'),
        agenda.get('cliente_id'),
        agenda.get('observacoes'),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_agenda(id: int) -> bool:
    """Deleta um evento da agenda"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM agenda WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== PRODUTOS =====

def adicionar_produto(produto: Dict) -> int:
    """Adiciona um novo produto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO produtos (codigo, nome, descricao, categoria, unidade, quantidade, quantidade_minima, preco_custo, preco_venda, fornecedor_id, ativo, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        produto['codigo'],
        produto['nome'],
        produto.get('descricao'),
        produto.get('categoria'),
        produto.get('unidade', 'un'),
        produto.get('quantidade', 0),
        produto.get('quantidade_minima', 0),
        produto.get('preco_custo', 0),
        produto.get('preco_venda', 0),
        produto.get('fornecedor_id'),
        produto.get('ativo', 1),
        datetime.now().isoformat()
    ))
    
    produto_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return produto_id

def listar_produtos() -> List[Dict]:
    """Lista todos os produtos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.codigo, p.nome, p.descricao, p.categoria, p.unidade, p.quantidade, p.quantidade_minima, 
               p.preco_custo, p.preco_venda, p.fornecedor_id, f.nome as fornecedor_nome, p.ativo, p.data_criacao
        FROM produtos p
        LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
        ORDER BY p.nome
    """)
    
    produtos = []
    for row in cursor.fetchall():
        produtos.append({
            'id': row[0],
            'codigo': row[1],
            'nome': row[2],
            'descricao': row[3],
            'categoria': row[4],
            'unidade': row[5],
            'quantidade': row[6],
            'quantidade_minima': row[7],
            'preco_custo': row[8],
            'preco_venda': row[9],
            'fornecedor_id': row[10],
            'fornecedor_nome': row[11],
            'ativo': row[12],
            'data_criacao': row[13]
        })
    
    conn.close()
    return produtos

def atualizar_produto(id: int, produto: Dict) -> bool:
    """Atualiza um produto existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE produtos
        SET codigo = ?, nome = ?, descricao = ?, categoria = ?, unidade = ?, quantidade = ?, quantidade_minima = ?, preco_custo = ?, preco_venda = ?, fornecedor_id = ?, ativo = ?
        WHERE id = ?
    """, (
        produto['codigo'],
        produto['nome'],
        produto.get('descricao'),
        produto.get('categoria'),
        produto.get('unidade', 'un'),
        produto.get('quantidade', 0),
        produto.get('quantidade_minima', 0),
        produto.get('preco_custo', 0),
        produto.get('preco_venda', 0),
        produto.get('fornecedor_id'),
        produto.get('ativo', 1),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_produto(id: int) -> bool:
    """Deleta um produto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== KITS =====

def adicionar_kit(kit: Dict) -> int:
    """Adiciona um novo kit"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO kits (codigo, nome, descricao, preco, ativo, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        kit['codigo'],
        kit['nome'],
        kit.get('descricao'),
        kit.get('preco', 0),
        kit.get('ativo', 1),
        datetime.now().isoformat()
    ))
    
    kit_id = cursor.lastrowid
    
    # Adicionar itens do kit
    if 'itens' in kit and kit['itens']:
        for item in kit['itens']:
            cursor.execute("""
                INSERT INTO kit_itens (kit_id, produto_id, quantidade)
                VALUES (?, ?, ?)
            """, (kit_id, item['produto_id'], item['quantidade']))
    
    conn.commit()
    conn.close()
    return kit_id

def listar_kits() -> List[Dict]:
    """Lista todos os kits"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, codigo, nome, descricao, preco, ativo, data_criacao
        FROM kits
        ORDER BY nome
    """)
    
    kits = []
    for row in cursor.fetchall():
        kit_id = row[0]
        
        # Buscar itens do kit
        cursor.execute("""
            SELECT ki.id, ki.produto_id, p.nome, ki.quantidade
            FROM kit_itens ki
            JOIN produtos p ON ki.produto_id = p.id
            WHERE ki.kit_id = ?
        """, (kit_id,))
        
        itens = []
        for item_row in cursor.fetchall():
            itens.append({
                'id': item_row[0],
                'produto_id': item_row[1],
                'produto_nome': item_row[2],
                'quantidade': item_row[3]
            })
        
        kits.append({
            'id': kit_id,
            'codigo': row[1],
            'nome': row[2],
            'descricao': row[3],
            'preco': row[4],
            'ativo': row[5],
            'data_criacao': row[6],
            'itens': itens
        })
    
    conn.close()
    return kits

def atualizar_kit(id: int, kit: Dict) -> bool:
    """Atualiza um kit existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE kits
        SET codigo = ?, nome = ?, descricao = ?, preco = ?, ativo = ?
        WHERE id = ?
    """, (
        kit['codigo'],
        kit['nome'],
        kit.get('descricao'),
        kit.get('preco', 0),
        kit.get('ativo', 1),
        id
    ))
    
    # Remover itens antigos e adicionar novos
    cursor.execute("DELETE FROM kit_itens WHERE kit_id = ?", (id,))
    
    if 'itens' in kit and kit['itens']:
        for item in kit['itens']:
            cursor.execute("""
                INSERT INTO kit_itens (kit_id, produto_id, quantidade)
                VALUES (?, ?, ?)
            """, (id, item['produto_id'], item['quantidade']))
    
    success = cursor.rowcount >= 0
    conn.commit()
    conn.close()
    return success

def deletar_kit(id: int) -> bool:
    """Deleta um kit"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Os itens serão deletados automaticamente pelo CASCADE
    cursor.execute("DELETE FROM kits WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== TAGS =====

def adicionar_tag(tag: Dict) -> int:
    """Adiciona uma nova tag"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tags (nome, cor, descricao, data_criacao)
        VALUES (?, ?, ?, ?)
    """, (
        tag['nome'],
        tag.get('cor', '#3498db'),
        tag.get('descricao'),
        datetime.now().isoformat()
    ))
    
    tag_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tag_id

def listar_tags() -> List[Dict]:
    """Lista todas as tags"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nome, cor, descricao, data_criacao
        FROM tags
        ORDER BY nome
    """)
    
    tags = []
    for row in cursor.fetchall():
        tags.append({
            'id': row[0],
            'nome': row[1],
            'cor': row[2],
            'descricao': row[3],
            'data_criacao': row[4]
        })
    
    conn.close()
    return tags

def atualizar_tag(id: int, tag: Dict) -> bool:
    """Atualiza uma tag existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tags
        SET nome = ?, cor = ?, descricao = ?
        WHERE id = ?
    """, (
        tag['nome'],
        tag.get('cor', '#3498db'),
        tag.get('descricao'),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_tag(id: int) -> bool:
    """Deleta uma tag"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tags WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== TEMPLATES DE EQUIPE =====

def adicionar_template_equipe(template: Dict) -> int:
    """Adiciona um novo template de equipe"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO templates_equipe (nome, descricao, conteudo, tipo, ativo, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        template['nome'],
        template.get('descricao'),
        template['conteudo'],
        template.get('tipo', 'geral'),
        template.get('ativo', 1),
        datetime.now().isoformat()
    ))
    
    template_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return template_id

def listar_templates_equipe() -> List[Dict]:
    """Lista todos os templates de equipe"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, nome, descricao, conteudo, tipo, ativo, data_criacao
        FROM templates_equipe
        ORDER BY nome
    """)
    
    templates = []
    for row in cursor.fetchall():
        templates.append({
            'id': row[0],
            'nome': row[1],
            'descricao': row[2],
            'conteudo': row[3],
            'tipo': row[4],
            'ativo': row[5],
            'data_criacao': row[6]
        })
    
    conn.close()
    return templates

def atualizar_template_equipe(id: int, template: Dict) -> bool:
    """Atualiza um template de equipe existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE templates_equipe
        SET nome = ?, descricao = ?, conteudo = ?, tipo = ?, ativo = ?
        WHERE id = ?
    """, (
        template['nome'],
        template.get('descricao'),
        template['conteudo'],
        template.get('tipo', 'geral'),
        template.get('ativo', 1),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_template_equipe(id: int) -> bool:
    """Deleta um template de equipe"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM templates_equipe WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== SESSÕES =====

def adicionar_sessao(sessao: Dict) -> int:
    """Adiciona uma nova sessão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessoes (titulo, descricao, data_sessao, duracao, cliente_id, valor, status, observacoes, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sessao['titulo'],
        sessao.get('descricao'),
        sessao['data_sessao'],
        sessao.get('duracao', 60),
        sessao.get('cliente_id'),
        sessao.get('valor', 0),
        sessao.get('status', 'agendada'),
        sessao.get('observacoes'),
        datetime.now().isoformat()
    ))
    
    sessao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sessao_id

def listar_sessoes() -> List[Dict]:
    """Lista todas as sessões"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, s.titulo, s.descricao, s.data_sessao, s.duracao, s.cliente_id, cl.nome as cliente_nome, s.valor, s.status, s.observacoes, s.data_criacao
        FROM sessoes s
        LEFT JOIN clientes cl ON s.cliente_id = cl.id
        ORDER BY s.data_sessao DESC
    """)
    
    sessoes = []
    for row in cursor.fetchall():
        sessoes.append({
            'id': row[0],
            'titulo': row[1],
            'descricao': row[2],
            'data_sessao': row[3],
            'duracao': row[4],
            'cliente_id': row[5],
            'cliente_nome': row[6],
            'valor': row[7],
            'status': row[8],
            'observacoes': row[9],
            'data_criacao': row[10]
        })
    
    conn.close()
    return sessoes

def atualizar_sessao(id: int, sessao: Dict) -> bool:
    """Atualiza uma sessão existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessoes
        SET titulo = ?, descricao = ?, data_sessao = ?, duracao = ?, cliente_id = ?, valor = ?, status = ?, observacoes = ?
        WHERE id = ?
    """, (
        sessao['titulo'],
        sessao.get('descricao'),
        sessao['data_sessao'],
        sessao.get('duracao', 60),
        sessao.get('cliente_id'),
        sessao.get('valor', 0),
        sessao.get('status', 'agendada'),
        sessao.get('observacoes'),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_sessao(id: int) -> bool:
    """Deleta uma sessão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessoes WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== COMISSÕES =====

def adicionar_comissao(comissao: Dict) -> int:
    """Adiciona uma nova comissão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO comissoes (descricao, valor, percentual, data_referencia, data_pagamento, status, beneficiario, lancamento_id, observacoes, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        comissao['descricao'],
        comissao['valor'],
        comissao.get('percentual', 0),
        comissao['data_referencia'],
        comissao.get('data_pagamento'),
        comissao.get('status', 'pendente'),
        comissao.get('beneficiario'),
        comissao.get('lancamento_id'),
        comissao.get('observacoes'),
        datetime.now().isoformat()
    ))
    
    comissao_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return comissao_id

def listar_comissoes() -> List[Dict]:
    """Lista todas as comissões"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, descricao, valor, percentual, data_referencia, data_pagamento, status, beneficiario, lancamento_id, observacoes, data_criacao
        FROM comissoes
        ORDER BY data_referencia DESC
    """)
    
    comissoes = []
    for row in cursor.fetchall():
        comissoes.append({
            'id': row[0],
            'descricao': row[1],
            'valor': row[2],
            'percentual': row[3],
            'data_referencia': row[4],
            'data_pagamento': row[5],
            'status': row[6],
            'beneficiario': row[7],
            'lancamento_id': row[8],
            'observacoes': row[9],
            'data_criacao': row[10]
        })
    
    conn.close()
    return comissoes

def atualizar_comissao(id: int, comissao: Dict) -> bool:
    """Atualiza uma comissão existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE comissoes
        SET descricao = ?, valor = ?, percentual = ?, data_referencia = ?, data_pagamento = ?, status = ?, beneficiario = ?, lancamento_id = ?, observacoes = ?
        WHERE id = ?
    """, (
        comissao['descricao'],
        comissao['valor'],
        comissao.get('percentual', 0),
        comissao['data_referencia'],
        comissao.get('data_pagamento'),
        comissao.get('status', 'pendente'),
        comissao.get('beneficiario'),
        comissao.get('lancamento_id'),
        comissao.get('observacoes'),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_comissao(id: int) -> bool:
    """Deleta uma comissão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM comissoes WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ===== SESSÃO-EQUIPE =====

def adicionar_sessao_equipe(sessao_equipe: Dict) -> int:
    """Adiciona um novo membro de equipe a uma sessão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessao_equipe (sessao_id, membro_nome, funcao, observacoes, data_criacao)
        VALUES (?, ?, ?, ?, ?)
    """, (
        sessao_equipe['sessao_id'],
        sessao_equipe['membro_nome'],
        sessao_equipe.get('funcao'),
        sessao_equipe.get('observacoes'),
        datetime.now().isoformat()
    ))
    
    se_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return se_id

def listar_sessao_equipe() -> List[Dict]:
    """Lista todos os membros de equipe por sessão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT se.id, se.sessao_id, s.titulo as sessao_titulo, se.membro_nome, se.funcao, se.observacoes, se.data_criacao
        FROM sessao_equipe se
        JOIN sessoes s ON se.sessao_id = s.id
        ORDER BY se.sessao_id DESC, se.membro_nome
    """)
    
    lista = []
    for row in cursor.fetchall():
        lista.append({
            'id': row[0],
            'sessao_id': row[1],
            'sessao_titulo': row[2],
            'membro_nome': row[3],
            'funcao': row[4],
            'observacoes': row[5],
            'data_criacao': row[6]
        })
    
    conn.close()
    return lista

def atualizar_sessao_equipe(id: int, sessao_equipe: Dict) -> bool:
    """Atualiza um membro de equipe de uma sessão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessao_equipe
        SET sessao_id = ?, membro_nome = ?, funcao = ?, observacoes = ?
        WHERE id = ?
    """, (
        sessao_equipe['sessao_id'],
        sessao_equipe['membro_nome'],
        sessao_equipe.get('funcao'),
        sessao_equipe.get('observacoes'),
        id
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def deletar_sessao_equipe(id: int) -> bool:
    """Deleta um membro de equipe de uma sessão"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessao_equipe WHERE id = ?", (id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def atualizar_categoria(categoria: Categoria) -> bool:
    """Atualiza uma categoria existente"""
    return _db.atualizar_categoria(categoria)

def atualizar_nome_categoria(nome_antigo: str, nome_novo: str) -> bool:
    """Atualiza o nome de uma categoria e seus relacionamentos"""
    return _db.atualizar_nome_categoria(nome_antigo, nome_novo)

def atualizar_cliente(nome_antigo: str, cliente: Dict) -> bool:
    """Atualiza um cliente existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    novo_nome = cliente.get('nome', cliente.get('razao_social', ''))
    
    print(f"\n=== atualizar_cliente (database.py) ===")
    print(f"Nome antigo (parâmetro): '{nome_antigo}' (len={len(nome_antigo)})")
    print(f"Novo nome: '{novo_nome}' (len={len(novo_nome)})")
    
    # Verificar se cliente existe
    cursor.execute("SELECT nome, razao_social FROM clientes WHERE nome = ? OR razao_social = ?", 
                 (nome_antigo, nome_antigo))
    cliente_existente = cursor.fetchone()
    if cliente_existente:
        print(f"Cliente encontrado: nome='{cliente_existente[0]}', razao_social='{cliente_existente[1]}'")
    else:
        print(f"ERRO: Cliente não encontrado com nome ou razao_social = '{nome_antigo}'")
        # Listar todos os clientes para comparação
        cursor.execute("SELECT nome FROM clientes")
        todos = cursor.fetchall()
        print(f"Clientes disponíveis: {[c[0] for c in todos]}")
        conn.close()
        raise ValueError(f"Cliente não encontrado para alterar: '{nome_antigo}'")
    
    # Se o nome mudou, verificar se o novo nome já existe
    if nome_antigo != novo_nome:
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE nome = ? AND nome != ?", 
                     (novo_nome, nome_antigo))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Já existe um cliente com este nome")
    
    cursor.execute("""
        UPDATE clientes 
        SET nome = ?, razao_social = ?, nome_fantasia = ?, cnpj = ?, ie = ?, im = ?,
            cep = ?, rua = ?, numero = ?, complemento = ?, bairro = ?, cidade = ?, 
            estado = ?, telefone = ?, contato = ?, email = ?, endereco = ?, documento = ?
        WHERE nome = ? OR razao_social = ?
    """, (
        cliente.get('nome', ''),
        cliente.get('razao_social', ''),
        cliente.get('nome_fantasia', ''),
        cliente.get('cnpj', ''),
        cliente.get('ie', ''),
        cliente.get('im', ''),
        cliente.get('cep', ''),
        cliente.get('rua', ''),
        cliente.get('numero', ''),
        cliente.get('complemento', ''),
        cliente.get('bairro', ''),
        cliente.get('cidade', ''),
        cliente.get('estado', ''),
        cliente.get('telefone', ''),
        cliente.get('contato', ''),
        cliente.get('email', ''),
        cliente.get('endereco', ''),
        cliente.get('documento', ''),
        nome_antigo,
        nome_antigo
    ))
    success = cursor.rowcount > 0
    print(f"Linhas afetadas na tabela clientes: {cursor.rowcount}")
    
    # Atualizar lançamentos em cascata se o nome mudou
    if nome_antigo != novo_nome:
        print(f"Atualizando lançamentos: '{nome_antigo}' -> '{novo_nome}'")
        cursor.execute("""
            UPDATE lancamentos 
            SET pessoa = ?
            WHERE pessoa = ? AND tipo = 'RECEITA'
        """, (novo_nome, nome_antigo))
        print(f"Linhas afetadas na tabela lancamentos: {cursor.rowcount}")
    
    conn.commit()
    conn.close()
    return success

def excluir_cliente(nome: str) -> bool:
    """Exclui um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE nome = ?", (nome,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def atualizar_fornecedor(nome_antigo: str, fornecedor: Dict) -> bool:
    """Atualiza um fornecedor existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    novo_nome = fornecedor.get('nome', fornecedor.get('razao_social', ''))
    
    print(f"\n=== atualizar_fornecedor (database.py) ===")
    print(f"Nome antigo (parâmetro): '{nome_antigo}' (len={len(nome_antigo)})")
    print(f"Novo nome: '{novo_nome}' (len={len(novo_nome)})")
    
    # Verificar se fornecedor existe
    cursor.execute("SELECT nome, razao_social FROM fornecedores WHERE nome = ? OR razao_social = ?", 
                 (nome_antigo, nome_antigo))
    fornecedor_existente = cursor.fetchone()
    if fornecedor_existente:
        print(f"Fornecedor encontrado: nome='{fornecedor_existente[0]}', razao_social='{fornecedor_existente[1]}'")
    else:
        print(f"ERRO: Fornecedor não encontrado com nome ou razao_social = '{nome_antigo}'")
        cursor.execute("SELECT nome FROM fornecedores")
        todos = cursor.fetchall()
        print(f"Fornecedores disponíveis: {[f[0] for f in todos]}")
        conn.close()
        raise ValueError(f"Fornecedor não encontrado para alterar: '{nome_antigo}'")
    
    # Se o nome mudou, verificar se o novo nome já existe
    if nome_antigo != novo_nome:
        cursor.execute("SELECT COUNT(*) FROM fornecedores WHERE nome = ? AND nome != ?", 
                     (novo_nome, nome_antigo))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Já existe um fornecedor com este nome")
    
    cursor.execute("""
        UPDATE fornecedores 
        SET nome = ?, razao_social = ?, nome_fantasia = ?, cnpj = ?, ie = ?, im = ?,
            cep = ?, rua = ?, numero = ?, complemento = ?, bairro = ?, cidade = ?, 
            estado = ?, telefone = ?, contato = ?, email = ?, endereco = ?, documento = ?
        WHERE nome = ? OR razao_social = ?
    """, (
        fornecedor.get('nome', ''),
        fornecedor.get('razao_social', ''),
        fornecedor.get('nome_fantasia', ''),
        fornecedor.get('cnpj', ''),
        fornecedor.get('ie', ''),
        fornecedor.get('im', ''),
        fornecedor.get('cep', ''),
        fornecedor.get('rua', ''),
        fornecedor.get('numero', ''),
        fornecedor.get('complemento', ''),
        fornecedor.get('bairro', ''),
        fornecedor.get('cidade', ''),
        fornecedor.get('estado', ''),
        fornecedor.get('telefone', ''),
        fornecedor.get('contato', ''),
        fornecedor.get('email', ''),
        fornecedor.get('endereco', ''),
        fornecedor.get('documento', ''),
        nome_antigo,
        nome_antigo
    ))
    success = cursor.rowcount > 0
    print(f"Linhas afetadas na tabela fornecedores: {cursor.rowcount}")
    
    # Atualizar lançamentos em cascata se o nome mudou
    if nome_antigo != novo_nome:
        print(f"Atualizando lançamentos: '{nome_antigo}' -> '{novo_nome}'")
        cursor.execute("""
            UPDATE lancamentos 
            SET pessoa = ?
            WHERE pessoa = ? AND tipo = 'DESPESA'
        """, (novo_nome, nome_antigo))
        print(f"Linhas afetadas na tabela lancamentos: {cursor.rowcount}")
    
    conn.commit()
    conn.close()
    return success

def excluir_fornecedor(nome: str) -> bool:
    """Exclui um fornecedor"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fornecedores WHERE nome = ?", (nome,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def migrar_dados_json(arquivo_json: str = "dados_financeiros.json"):
    """Migra dados do arquivo JSON para o banco de dados"""
    _db.migrar_dados_json(arquivo_json)


# Instância global do DatabaseManager (escolhe automaticamente o tipo correto)
DatabaseManager = _get_database_manager()
_db = DatabaseManager()

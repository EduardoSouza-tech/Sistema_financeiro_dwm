"""
Testes para Migration de Senhas SHA-256 → Bcrypt
"""
import pytest
import hashlib
from unittest.mock import Mock, patch, MagicMock
from migration_upgrade_passwords import (
    is_sha256_hash,
    is_bcrypt_hash,
    verificar_e_upgrade_senha,
    relatorio_hashes_pendentes,
    forcar_upgrade_usuario
)


class TestDeteccaoHashes:
    """Testes para detecção de tipos de hash"""
    
    def test_detectar_sha256_valido(self):
        """Deve detectar hash SHA-256 válido"""
        sha256 = hashlib.sha256(b"senha123").hexdigest()
        assert is_sha256_hash(sha256) is True
    
    def test_detectar_sha256_invalido_tamanho(self):
        """Deve rejeitar hash com tamanho errado"""
        assert is_sha256_hash("abc123") is False
    
    def test_detectar_sha256_invalido_caracteres(self):
        """Deve rejeitar hash com caracteres não-hexadecimais"""
        hash_invalido = "g" * 64  # 'g' não é hexadecimal
        assert is_sha256_hash(hash_invalido) is False
    
    def test_detectar_bcrypt_valido(self):
        """Deve detectar hash bcrypt válido"""
        bcrypt_hash = "$2b$12$abcdefghijklmnopqrstuv"  # Formato bcrypt
        assert is_bcrypt_hash(bcrypt_hash) is True
    
    def test_detectar_bcrypt_variantes(self):
        """Deve detectar todas as variantes de bcrypt"""
        assert is_bcrypt_hash("$2a$12$test") is True
        assert is_bcrypt_hash("$2b$12$test") is True
        assert is_bcrypt_hash("$2x$12$test") is True
        assert is_bcrypt_hash("$2y$12$test") is True
    
    def test_detectar_bcrypt_invalido(self):
        """Deve rejeitar hash não-bcrypt"""
        assert is_bcrypt_hash("plaintext") is False
        assert is_bcrypt_hash("") is False
        assert is_bcrypt_hash(None) is False


class TestVerificarEUpgradeSenha:
    """Testes para verificação e upgrade automático de senhas"""
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    @patch('migration_upgrade_passwords.bcrypt')
    def test_verificar_senha_bcrypt_correta(self, mock_bcrypt):
        """Deve verificar senha bcrypt correta sem fazer upgrade"""
        mock_bcrypt.checkpw.return_value = True
        
        db_mock = Mock()
        username = "usuario_teste"
        password = "senha123"
        hash_bcrypt = "$2b$12$abcdefghij"
        
        senha_correta, novo_hash = verificar_e_upgrade_senha(
            username, password, hash_bcrypt, db_mock
        )
        
        assert senha_correta is True
        assert novo_hash is None  # Não deve fazer upgrade
        mock_bcrypt.checkpw.assert_called_once()
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    @patch('migration_upgrade_passwords.bcrypt')
    def test_verificar_senha_bcrypt_incorreta(self, mock_bcrypt):
        """Deve rejeitar senha bcrypt incorreta"""
        mock_bcrypt.checkpw.return_value = False
        
        db_mock = Mock()
        username = "usuario_teste"
        password = "senha_errada"
        hash_bcrypt = "$2b$12$abcdefghij"
        
        senha_correta, novo_hash = verificar_e_upgrade_senha(
            username, password, hash_bcrypt, db_mock
        )
        
        assert senha_correta is False
        assert novo_hash is None
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    @patch('migration_upgrade_passwords.bcrypt')
    def test_upgrade_sha256_para_bcrypt(self, mock_bcrypt):
        """Deve fazer upgrade de SHA-256 para bcrypt"""
        # Setup
        password = "senha123"
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        novo_bcrypt_hash = "$2b$12$novohash"
        
        mock_bcrypt.hashpw.return_value = novo_bcrypt_hash.encode()
        mock_bcrypt.gensalt.return_value = b"$2b$12$salt"
        
        # Mock do banco
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        # Executar
        senha_correta, novo_hash = verificar_e_upgrade_senha(
            "usuario_teste", password, sha256_hash, db_mock
        )
        
        # Verificar
        assert senha_correta is True
        assert novo_hash == novo_bcrypt_hash
        
        # Verificar que UPDATE foi executado
        mock_cursor.execute.assert_called_once()
        sql_executado = mock_cursor.execute.call_args[0][0]
        assert "UPDATE usuarios" in sql_executado
        assert "password_hash" in sql_executado
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    def test_upgrade_sha256_senha_incorreta(self):
        """Não deve fazer upgrade se senha estiver incorreta"""
        password_correta = "senha123"
        password_errada = "senha_errada"
        sha256_hash = hashlib.sha256(password_correta.encode()).hexdigest()
        
        db_mock = Mock()
        
        senha_correta, novo_hash = verificar_e_upgrade_senha(
            "usuario_teste", password_errada, sha256_hash, db_mock
        )
        
        assert senha_correta is False
        assert novo_hash is None
        # Não deve tentar acessar o banco
        db_mock.get_connection.assert_not_called()
    
    def test_hash_desconhecido(self):
        """Deve rejeitar hash em formato desconhecido"""
        db_mock = Mock()
        hash_invalido = "formato_desconhecido"
        
        senha_correta, novo_hash = verificar_e_upgrade_senha(
            "usuario_teste", "senha123", hash_invalido, db_mock
        )
        
        assert senha_correta is False
        assert novo_hash is None


class TestRelatorioHashesPendentes:
    """Testes para relatório de status de migração"""
    
    def test_relatorio_com_usuarios_mistos(self):
        """Deve gerar relatório com usuários bcrypt e SHA-256"""
        # Mock de usuários
        mock_usuarios = [
            {
                'username': 'user1',
                'password_hash': '$2b$12$abcdefghij'  # bcrypt
            },
            {
                'username': 'user2',
                'password_hash': hashlib.sha256(b"senha").hexdigest()  # SHA-256
            },
            {
                'username': 'user3',
                'password_hash': '$2b$12$xyzxyzxyz'  # bcrypt
            },
            {
                'username': 'user4',
                'password_hash': 'hash_invalido'  # desconhecido
            }
        ]
        
        # Mock do banco
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_usuarios
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        # Executar
        stats = relatorio_hashes_pendentes(db_mock)
        
        # Verificar
        assert stats['total_usuarios'] == 4
        assert stats['usuarios_bcrypt'] == 2
        assert stats['usuarios_sha256'] == 1
        assert stats['usuarios_desconhecido'] == 1
        assert len(stats['pendentes']) == 2  # SHA-256 + desconhecido
    
    def test_relatorio_todos_migrados(self):
        """Deve indicar quando todos estão em bcrypt"""
        mock_usuarios = [
            {'username': 'user1', 'password_hash': '$2b$12$abc'},
            {'username': 'user2', 'password_hash': '$2a$12$xyz'}
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_usuarios
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        stats = relatorio_hashes_pendentes(db_mock)
        
        assert stats['total_usuarios'] == 2
        assert stats['usuarios_bcrypt'] == 2
        assert stats['usuarios_sha256'] == 0
        assert len(stats['pendentes']) == 0
    
    def test_relatorio_sem_usuarios(self):
        """Deve lidar com banco sem usuários"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        stats = relatorio_hashes_pendentes(db_mock)
        
        assert stats['total_usuarios'] == 0
        assert stats['usuarios_bcrypt'] == 0
        assert stats['usuarios_sha256'] == 0
        assert len(stats['pendentes']) == 0


class TestForcarUpgradeUsuario:
    """Testes para upgrade forçado de senha"""
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    @patch('migration_upgrade_passwords.bcrypt')
    def test_forcar_upgrade_sucesso(self, mock_bcrypt):
        """Deve forçar upgrade de senha com sucesso"""
        novo_hash = "$2b$12$novohash"
        mock_bcrypt.hashpw.return_value = novo_hash.encode()
        mock_bcrypt.gensalt.return_value = b"salt"
        
        mock_cursor = Mock()
        mock_cursor.rowcount = 1  # 1 linha afetada
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        sucesso = forcar_upgrade_usuario("usuario_teste", "nova_senha", db_mock)
        
        assert sucesso is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    @patch('migration_upgrade_passwords.bcrypt')
    def test_forcar_upgrade_usuario_nao_existe(self, mock_bcrypt):
        """Deve retornar False se usuário não existe"""
        mock_bcrypt.hashpw.return_value = b"hash"
        mock_bcrypt.gensalt.return_value = b"salt"
        
        mock_cursor = Mock()
        mock_cursor.rowcount = 0  # Nenhuma linha afetada
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        sucesso = forcar_upgrade_usuario("usuario_inexistente", "senha", db_mock)
        
        assert sucesso is False
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', False)
    def test_forcar_upgrade_sem_bcrypt(self):
        """Deve falhar se bcrypt não estiver disponível"""
        db_mock = Mock()
        
        sucesso = forcar_upgrade_usuario("usuario", "senha", db_mock)
        
        assert sucesso is False
        db_mock.get_connection.assert_not_called()


class TestIntegracaoLogin:
    """Testes de integração com sistema de login"""
    
    @patch('migration_upgrade_passwords.BCRYPT_AVAILABLE', True)
    @patch('migration_upgrade_passwords.bcrypt')
    def test_login_primeiro_upgrade_automatico(self, mock_bcrypt):
        """Deve fazer upgrade no primeiro login após deploy"""
        # Simular usuário com senha SHA-256 antiga
        password = "senha123"
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        novo_bcrypt = "$2b$12$novo"
        
        mock_bcrypt.hashpw.return_value = novo_bcrypt.encode()
        mock_bcrypt.gensalt.return_value = b"salt"
        
        # Mock banco
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        db_mock = Mock()
        db_mock.get_connection.return_value = mock_conn
        
        # Primeiro login (com SHA-256)
        senha_correta_1, novo_hash_1 = verificar_e_upgrade_senha(
            "usuario", password, sha256_hash, db_mock
        )
        
        assert senha_correta_1 is True
        assert novo_hash_1 == novo_bcrypt
        assert mock_cursor.execute.call_count == 1  # UPDATE executado
        
        # Segundo login (já com bcrypt)
        mock_bcrypt.checkpw.return_value = True
        mock_cursor.reset_mock()
        
        senha_correta_2, novo_hash_2 = verificar_e_upgrade_senha(
            "usuario", password, novo_bcrypt, db_mock
        )
        
        assert senha_correta_2 is True
        assert novo_hash_2 is None  # Não faz upgrade novamente
        assert mock_cursor.execute.call_count == 0  # Sem UPDATE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

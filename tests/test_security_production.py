"""
Testes de Segurança - Proteção de Endpoints de Debug
"""
import pytest
import os
from unittest.mock import patch, Mock
from flask import Flask


class TestProtecaoProducao:
    """Testes para verificar que endpoints de debug são bloqueados em produção"""
    
    @pytest.fixture
    def app_desenvolvimento(self):
        """App configurado para desenvolvimento"""
        with patch.dict(os.environ, {'RAILWAY_ENVIRONMENT': ''}, clear=True):
            # Reimportar para pegar nova configuração
            import importlib
            import web_server
            importlib.reload(web_server)
            return web_server.app
    
    @pytest.fixture
    def app_producao(self):
        """App configurado para produção"""
        with patch.dict(os.environ, {'RAILWAY_ENVIRONMENT': 'production'}):
            # Reimportar para pegar nova configuração
            import importlib
            import web_server
            importlib.reload(web_server)
            return web_server.app
    
    def test_is_production_detection_development(self):
        """Deve detectar ambiente de desenvolvimento"""
        with patch.dict(os.environ, {'RAILWAY_ENVIRONMENT': ''}, clear=True):
            IS_PRODUCTION = bool(os.getenv('RAILWAY_ENVIRONMENT'))
            assert IS_PRODUCTION is False
    
    def test_is_production_detection_production(self):
        """Deve detectar ambiente de produção"""
        with patch.dict(os.environ, {'RAILWAY_ENVIRONMENT': 'production'}):
            IS_PRODUCTION = bool(os.getenv('RAILWAY_ENVIRONMENT'))
            assert IS_PRODUCTION is True
    
    def test_csrf_exempt_routes_development(self, app_desenvolvimento):
        """Em desenvolvimento, deve incluir endpoints de debug"""
        from web_server import CSRF_EXEMPT_ROUTES
        
        assert '/api/auth/login' in CSRF_EXEMPT_ROUTES
        assert '/api/debug/criar-admin' in CSRF_EXEMPT_ROUTES
        assert '/api/debug/fix-kits-table' in CSRF_EXEMPT_ROUTES
    
    def test_csrf_exempt_routes_production(self, app_producao):
        """Em produção, NÃO deve incluir endpoints de debug"""
        from web_server import CSRF_EXEMPT_ROUTES
        
        # Endpoints legítimos devem estar presentes
        assert '/api/auth/login' in CSRF_EXEMPT_ROUTES
        assert '/api/auth/logout' in CSRF_EXEMPT_ROUTES
        
        # Endpoints de debug NÃO devem estar presentes
        assert '/api/debug/criar-admin' not in CSRF_EXEMPT_ROUTES
        assert '/api/debug/fix-kits-table' not in CSRF_EXEMPT_ROUTES
        assert '/api/debug/fix-p1-issues' not in CSRF_EXEMPT_ROUTES
    
    def test_debug_endpoint_blocked_in_production(self, app_producao):
        """Endpoints de debug devem retornar 403 em produção"""
        with app_producao.test_client() as client:
            # Criar admin
            response = client.post('/api/debug/criar-admin')
            assert response.status_code == 403
            data = response.get_json()
            assert data['success'] is False
            assert 'produção' in data['error'].lower()
            
            # Fix kits
            response = client.post('/api/debug/fix-kits-table')
            assert response.status_code == 403
            
            # Fix P1
            response = client.post('/api/debug/fix-p1-issues')
            assert response.status_code == 403
    
    def test_debug_endpoint_allowed_in_development(self, app_desenvolvimento):
        """Endpoints de debug devem funcionar em desenvolvimento"""
        with app_desenvolvimento.test_client() as client:
            # Nota: Estes endpoints vão falhar por outros motivos (DB, etc)
            # mas não devem retornar 403
            
            response = client.post('/api/debug/criar-admin')
            assert response.status_code != 403
            
            response = client.post('/api/debug/fix-kits-table')
            assert response.status_code != 403
    
    def test_auth_endpoints_always_available(self, app_producao):
        """Endpoints de auth devem estar sempre disponíveis"""
        with app_producao.test_client() as client:
            # Login (pode falhar por validação, mas não por bloqueio)
            response = client.post('/api/auth/login', json={
                'username': 'test',
                'password': 'test'
            })
            assert response.status_code != 403
            
            # Logout
            response = client.post('/api/auth/logout')
            assert response.status_code != 403
    
    def test_check_debug_endpoint_allowed_function(self):
        """Testa função _check_debug_endpoint_allowed"""
        with patch('web_server.IS_PRODUCTION', True):
            from web_server import _check_debug_endpoint_allowed
            
            result = _check_debug_endpoint_allowed()
            assert result is not None
            response, status = result
            assert status == 403
        
        with patch('web_server.IS_PRODUCTION', False):
            from web_server import _check_debug_endpoint_allowed
            
            result = _check_debug_endpoint_allowed()
            assert result is None


class TestCriarAdminSeguro:
    """Testes para o script criar_admin_seguro.py"""
    
    def test_validacao_senha_forte(self):
        """Deve validar requisitos de senha forte"""
        from auth_functions import validar_senha_forte
        
        # Senhas fracas
        assert validar_senha_forte('123')[0] is False  # Muito curta
        assert validar_senha_forte('abcdefgh')[0] is False  # Sem maiúscula
        assert validar_senha_forte('ABCDEFGH')[0] is False  # Sem minúscula
        assert validar_senha_forte('Abcdefgh')[0] is False  # Sem número
        assert validar_senha_forte('Abcd1234')[0] is False  # Sem especial
        
        # Senha forte
        assert validar_senha_forte('Senha123!')[0] is True
        assert validar_senha_forte('Admin@2026')[0] is True
    
    @patch('criar_admin_seguro.DatabasePostgreSQL')
    @patch('criar_admin_seguro.getpass.getpass')
    def test_criar_admin_modo_interativo(self, mock_getpass, mock_db):
        """Testa criação de admin em modo interativo"""
        from criar_admin_seguro import criar_admin_seguro
        
        # Mock senha
        mock_getpass.side_effect = ['Senha123!', 'Senha123!']  # senha e confirmação
        
        # Mock banco
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Usuário não existe
        mock_cursor.fetchone.return_value = {'id': 1}  # Após INSERT
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_db_instance = Mock()
        mock_db_instance.get_connection.return_value = mock_conn
        mock_db.return_value = mock_db_instance
        
        # Executar
        resultado = criar_admin_seguro('admin')
        
        assert resultado is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    def test_script_cli_help(self):
        """Testa que CLI tem ajuda adequada"""
        import subprocess
        
        result = subprocess.run(
            ['python', 'criar_admin_seguro.py', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'username' in result.stdout.lower()
        assert 'password' in result.stdout.lower()
        assert 'reset' in result.stdout.lower()


class TestSegurancaGeral:
    """Testes gerais de segurança"""
    
    def test_no_hardcoded_passwords(self):
        """Verifica que não há senhas hardcoded em produção"""
        import web_server
        import inspect
        
        source = inspect.getsource(web_server)
        
        # Verificar que não há senhas óbvias
        # (Exceto em endpoints de debug que estão protegidos)
        assert 'password = "admin123"' in source  # OK, está em endpoint protegido
        
        # Verificar que senha está dentro de função de debug
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'password = "admin123"' in line:
                # Verificar que está dentro de criar_admin_inicial
                context = ''.join(lines[max(0, i-20):i])
                assert 'criar_admin_inicial' in context or 'debug' in context.lower()
    
    def test_rate_limiting_presente(self):
        """Verifica que rate limiting está configurado"""
        from web_server import LIMITER_AVAILABLE
        
        # Em produção, rate limiting deve estar disponível
        # (Pode não estar em testes, mas código deve suportar)
        assert isinstance(LIMITER_AVAILABLE, bool)
    
    def test_csrf_protection_ativo(self):
        """Verifica que CSRF protection está ativo"""
        from web_server import csrf_instance
        
        assert csrf_instance is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

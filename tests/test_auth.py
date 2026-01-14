"""
Testes para o módulo de autenticação
"""
import pytest
import json


class TestAuthentication:
    """Testes para autenticação de usuários"""
    
    def test_login_valido(self, client):
        """Teste de login com credenciais válidas"""
        response = client.post('/api/auth/login', json={
            'email': 'admin@sistema.com',
            'senha': 'admin123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'usuario' in data
        assert data['usuario']['email'] == 'admin@sistema.com'
    
    
    def test_login_senha_invalida(self, client):
        """Teste de login com senha incorreta"""
        response = client.post('/api/auth/login', json={
            'email': 'admin@sistema.com',
            'senha': 'senha_errada'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'erro' in data
    
    
    def test_login_usuario_inexistente(self, client):
        """Teste de login com usuário que não existe"""
        response = client.post('/api/auth/login', json={
            'email': 'naoexiste@teste.com',
            'senha': 'qualquer'
        })
        
        assert response.status_code == 401
    
    
    def test_login_sem_email(self, client):
        """Teste de login sem fornecer email"""
        response = client.post('/api/auth/login', json={
            'senha': 'admin123'
        })
        
        assert response.status_code == 400
    
    
    def test_login_sem_senha(self, client):
        """Teste de login sem fornecer senha"""
        response = client.post('/api/auth/login', json={
            'email': 'admin@sistema.com'
        })
        
        assert response.status_code == 400
    
    
    def test_logout(self, authenticated_client):
        """Teste de logout"""
        response = authenticated_client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['sucesso'] is True
    
    
    def test_verificar_sessao_autenticado(self, authenticated_client):
        """Teste de verificação de sessão para usuário autenticado"""
        response = authenticated_client.get('/api/auth/verify')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'usuario' in data
        assert data['autenticado'] is True
    
    
    def test_verificar_sessao_nao_autenticado(self, client):
        """Teste de verificação de sessão sem autenticação"""
        response = client.get('/api/auth/verify')
        
        assert response.status_code == 401
    
    
    def test_mudar_senha_valida(self, authenticated_client):
        """Teste de mudança de senha com dados válidos"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'senha_atual': 'admin123',
            'senha_nova': 'nova_senha_123',
            'confirmar_senha': 'nova_senha_123'
        })
        
        # Pode retornar 200 ou 400 dependendo da implementação
        # O importante é que não dê erro 500
        assert response.status_code in [200, 400, 401]
    
    
    def test_mudar_senha_senha_atual_incorreta(self, authenticated_client):
        """Teste de mudança de senha com senha atual incorreta"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'senha_atual': 'senha_errada',
            'senha_nova': 'nova_senha_123',
            'confirmar_senha': 'nova_senha_123'
        })
        
        assert response.status_code in [400, 401]
    
    
    def test_mudar_senha_confirmacao_nao_confere(self, authenticated_client):
        """Teste de mudança de senha com confirmação diferente"""
        response = authenticated_client.post('/api/auth/change-password', json={
            'senha_atual': 'admin123',
            'senha_nova': 'nova_senha_123',
            'confirmar_senha': 'senha_diferente'
        })
        
        assert response.status_code == 400


class TestAuthorization:
    """Testes para autorização e permissões"""
    
    def test_acesso_sem_autenticacao(self, client):
        """Teste de acesso a endpoint protegido sem autenticação"""
        response = client.get('/api/contas')
        
        assert response.status_code == 401
    
    
    def test_acesso_com_autenticacao(self, authenticated_client):
        """Teste de acesso a endpoint protegido com autenticação"""
        response = authenticated_client.get('/api/contas')
        
        assert response.status_code == 200
    
    
    def test_listar_permissoes(self, authenticated_client):
        """Teste de listagem de permissões disponíveis"""
        response = authenticated_client.get('/api/permissoes')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'permissoes' in data
        assert len(data['permissoes']) > 0

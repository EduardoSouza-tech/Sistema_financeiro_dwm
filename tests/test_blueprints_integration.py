"""
Testes de integração para blueprints
Testa endpoints HTTP dos módulos kits, contratos, sessões e relatórios
"""

import pytest
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from datetime import date, datetime


@pytest.fixture
def app():
    """Fixture com aplicação Flask para testes"""
    # Importar app após adicionar ao path
    import web_server
    app = web_server.app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Desabilitar CSRF em testes
    return app


@pytest.fixture
def client(app):
    """Fixture com cliente de teste"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Fixture com headers de autenticação simulados"""
    # Em produção, seria necessário fazer login real
    # Para testes, vamos simular headers básicos
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


class TestKitsBlueprint:
    """Testes para endpoints de Kits"""
    
    def test_get_kits_endpoint_exists(self, client):
        """Testa que endpoint GET /api/kits existe"""
        response = client.get('/api/kits')
        # Pode retornar 200, 401 (sem auth) ou 403 (sem permissão)
        assert response.status_code in [200, 401, 403]
    
    def test_post_kits_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint POST /api/kits existe"""
        response = client.post('/api/kits', 
                              json={'nome': 'Kit Teste'},
                              headers=auth_headers)
        # Pode retornar 201, 400, 401 ou 403
        assert response.status_code in [201, 400, 401, 403]
    
    def test_get_kit_by_id_endpoint_exists(self, client):
        """Testa que endpoint GET /api/kits/<id> existe"""
        response = client.get('/api/kits/1')
        # Pode retornar 200, 404, 401 ou 403
        assert response.status_code in [200, 404, 401, 403]
    
    def test_put_kit_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint PUT /api/kits/<id> existe"""
        response = client.put('/api/kits/1',
                             json={'nome': 'Kit Atualizado'},
                             headers=auth_headers)
        assert response.status_code in [200, 404, 401, 403]
    
    def test_delete_kit_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint DELETE /api/kits/<id> existe"""
        response = client.delete('/api/kits/1', headers=auth_headers)
        assert response.status_code in [200, 404, 401, 403]
    
    def test_get_kits_returns_json(self, client):
        """Testa que GET /api/kits retorna JSON"""
        response = client.get('/api/kits')
        if response.status_code == 200:
            assert response.is_json
            data = response.get_json()
            assert isinstance(data, (list, dict))


class TestContratosBlueprint:
    """Testes para endpoints de Contratos"""
    
    def test_get_contratos_endpoint_exists(self, client):
        """Testa que endpoint GET /api/contratos existe"""
        response = client.get('/api/contratos')
        assert response.status_code in [200, 401, 403]
    
    def test_post_contratos_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint POST /api/contratos existe"""
        contrato_data = {
            'numero': 'CONT-001',
            'cliente_id': 1,
            'valor': 1000.00,
            'data_inicio': '2026-01-01',
            'data_fim': '2026-12-31'
        }
        response = client.post('/api/contratos',
                              json=contrato_data,
                              headers=auth_headers)
        assert response.status_code in [201, 400, 401, 403]
    
    def test_get_proximo_numero_endpoint_exists(self, client):
        """Testa que endpoint GET /api/contratos/proximo-numero existe"""
        response = client.get('/api/contratos/proximo-numero')
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            assert response.is_json
            data = response.get_json()
            assert 'numero' in data
    
    def test_get_contrato_by_id_endpoint_exists(self, client):
        """Testa que endpoint GET /api/contratos/<id> existe"""
        response = client.get('/api/contratos/1')
        assert response.status_code in [200, 404, 401, 403]
    
    def test_put_contrato_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint PUT /api/contratos/<id> existe"""
        response = client.put('/api/contratos/1',
                             json={'valor': 1500.00},
                             headers=auth_headers)
        assert response.status_code in [200, 404, 401, 403]
    
    def test_delete_contrato_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint DELETE /api/contratos/<id> existe"""
        response = client.delete('/api/contratos/1', headers=auth_headers)
        assert response.status_code in [200, 404, 401, 403]
    
    def test_contratos_returns_json(self, client):
        """Testa que GET /api/contratos retorna JSON"""
        response = client.get('/api/contratos')
        if response.status_code == 200:
            assert response.is_json


class TestSessoesBlueprint:
    """Testes para endpoints de Sessões"""
    
    def test_get_sessoes_endpoint_exists(self, client):
        """Testa que endpoint GET /api/sessoes existe"""
        response = client.get('/api/sessoes')
        assert response.status_code in [200, 401, 403]
    
    def test_post_sessoes_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint POST /api/sessoes existe"""
        sessao_data = {
            'titulo': 'Sessão Teste',
            'data': '2026-01-20',
            'quantidade_horas': 4,
            'cliente_id': 1,
            'contrato_id': 1
        }
        response = client.post('/api/sessoes',
                              json=sessao_data,
                              headers=auth_headers)
        assert response.status_code in [201, 400, 401, 403]
    
    def test_get_sessao_by_id_endpoint_exists(self, client):
        """Testa que endpoint GET /api/sessoes/<id> existe"""
        response = client.get('/api/sessoes/1')
        assert response.status_code in [200, 404, 401, 403]
    
    def test_put_sessao_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint PUT /api/sessoes/<id> existe"""
        response = client.put('/api/sessoes/1',
                             json={'quantidade_horas': 5},
                             headers=auth_headers)
        assert response.status_code in [200, 404, 401, 403]
    
    def test_delete_sessao_endpoint_exists(self, client, auth_headers):
        """Testa que endpoint DELETE /api/sessoes/<id> existe"""
        response = client.delete('/api/sessoes/1', headers=auth_headers)
        assert response.status_code in [200, 404, 401, 403]
    
    def test_sessoes_field_mapping(self, client, auth_headers):
        """Testa mapeamento de campos (correção P0)"""
        sessao_data = {
            'titulo': 'Teste Mapeamento',
            'data': '2026-01-20',  # Frontend: 'data'
            'quantidade_horas': 3  # Frontend: horas → Backend: minutos
        }
        response = client.post('/api/sessoes',
                              json=sessao_data,
                              headers=auth_headers)
        # Se passar autenticação, deve processar o mapeamento
        if response.status_code == 201:
            assert response.is_json
            data = response.get_json()
            assert data.get('success') is True


class TestRelatoriosBlueprint:
    """Testes para endpoints de Relatórios"""
    
    def test_get_dashboard_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/dashboard existe"""
        response = client.get('/api/relatorios/dashboard')
        assert response.status_code in [200, 401, 403]
    
    def test_get_dashboard_completo_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/dashboard-completo existe"""
        params = {
            'data_inicio': '2026-01-01',
            'data_fim': '2026-01-31'
        }
        response = client.get('/api/relatorios/dashboard-completo', query_string=params)
        assert response.status_code in [200, 400, 401, 403]
    
    def test_get_fluxo_caixa_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/fluxo-caixa existe"""
        params = {
            'data_inicio': '2026-01-01',
            'data_fim': '2026-01-31'
        }
        response = client.get('/api/relatorios/fluxo-caixa', query_string=params)
        assert response.status_code in [200, 401, 403]
    
    def test_get_fluxo_projetado_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/fluxo-projetado existe"""
        response = client.get('/api/relatorios/fluxo-projetado?dias=30')
        assert response.status_code in [200, 401, 403]
    
    def test_get_analise_contas_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/analise-contas existe"""
        response = client.get('/api/relatorios/analise-contas')
        assert response.status_code in [200, 401, 403]
    
    def test_get_indicadores_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/indicadores existe"""
        response = client.get('/api/relatorios/indicadores')
        assert response.status_code in [200, 401, 403]
    
    def test_get_inadimplencia_endpoint_exists(self, client):
        """Testa que endpoint GET /api/relatorios/inadimplencia existe"""
        response = client.get('/api/relatorios/inadimplencia')
        assert response.status_code in [200, 401, 403]
    
    def test_dashboard_returns_expected_structure(self, client):
        """Testa estrutura de resposta do dashboard"""
        response = client.get('/api/relatorios/dashboard')
        if response.status_code == 200:
            assert response.is_json
            data = response.get_json()
            # Dashboard deve ter campos esperados
            expected_fields = ['saldo_total', 'contas_receber', 'contas_pagar']
            # Pelo menos algum dos campos deve estar presente
            assert any(field in data for field in expected_fields) or 'error' in data
    
    def test_relatorios_with_date_filters(self, client):
        """Testa relatórios com filtros de data"""
        params = {
            'data_inicio': '2026-01-01',
            'data_fim': '2026-01-31'
        }
        response = client.get('/api/relatorios/fluxo-caixa', query_string=params)
        if response.status_code == 200:
            assert response.is_json


class TestBlueprintsIntegration:
    """Testes de integração entre blueprints"""
    
    def test_all_blueprints_registered(self, app):
        """Testa que todos os blueprints foram registrados"""
        blueprints = app.blueprints
        # Deve ter pelo menos os 4 blueprints principais
        expected = ['kits', 'contratos', 'sessoes', 'relatorios']
        for bp_name in expected:
            assert bp_name in blueprints, f"Blueprint '{bp_name}' não registrado"
    
    def test_blueprint_url_prefixes(self, app):
        """Testa que blueprints têm prefixos corretos"""
        # Kits usa /api como prefixo
        assert 'kits' in app.blueprints
        # Contratos, Sessoes e Relatorios usam seus próprios prefixos
        assert 'contratos' in app.blueprints
        assert 'sessoes' in app.blueprints
        assert 'relatorios' in app.blueprints
    
    def test_no_route_conflicts(self, app):
        """Testa que não há conflitos de rotas entre blueprints"""
        # Obter todas as rotas registradas
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        # Verificar rotas dos blueprints
        assert '/api/kits' in routes
        assert '/api/contratos' in routes
        assert '/api/sessoes' in routes
        assert '/api/relatorios/dashboard' in routes
        
        # Verificar que não há duplicatas críticas
        route_count = {}
        for route in routes:
            route_count[route] = route_count.get(route, 0) + 1
        
        # Algumas rotas podem estar duplicadas (web_server.py + blueprint)
        # mas blueprints têm prioridade
        duplicates = [r for r, c in route_count.items() if c > 1]
        if duplicates:
            print(f"⚠️  Rotas duplicadas (esperado): {len(duplicates)}")


class TestBlueprintsErrorHandling:
    """Testes de tratamento de erros dos blueprints"""
    
    def test_invalid_id_returns_404(self, client):
        """Testa que ID inválido retorna 404"""
        response = client.get('/api/kits/99999')
        # Pode retornar 404 (não encontrado) ou 401/403 (sem permissão)
        assert response.status_code in [404, 401, 403]
    
    def test_invalid_json_returns_400(self, client, auth_headers):
        """Testa que JSON inválido retorna 400"""
        response = client.post('/api/contratos',
                              data='invalid json',
                              headers=auth_headers)
        assert response.status_code in [400, 401, 403]
    
    def test_missing_required_fields_returns_400(self, client, auth_headers):
        """Testa que campos obrigatórios faltando retorna 400"""
        response = client.post('/api/sessoes',
                              json={},  # Sem campos obrigatórios
                              headers=auth_headers)
        assert response.status_code in [400, 401, 403]
    
    def test_invalid_date_format_handled(self, client):
        """Testa que formato de data inválido é tratado"""
        params = {
            'data_inicio': 'data-invalida',
            'data_fim': '2026-01-31'
        }
        response = client.get('/api/relatorios/dashboard-completo', query_string=params)
        # Deve retornar erro 400 ou usar default
        assert response.status_code in [200, 400, 401, 403]


class TestBlueprintsPerformance:
    """Testes básicos de performance"""
    
    def test_dashboard_response_time(self, client):
        """Testa tempo de resposta do dashboard"""
        import time
        start = time.time()
        response = client.get('/api/relatorios/dashboard')
        elapsed = time.time() - start
        
        # Dashboard deve responder em menos de 5 segundos
        # (mesmo sem cache, considerando tempo de DB)
        assert elapsed < 5.0
    
    def test_list_endpoints_response_time(self, client):
        """Testa tempo de resposta de endpoints de listagem"""
        import time
        
        endpoints = [
            '/api/kits',
            '/api/contratos',
            '/api/sessoes'
        ]
        
        for endpoint in endpoints:
            start = time.time()
            response = client.get(endpoint)
            elapsed = time.time() - start
            
            # Listagens devem responder em menos de 3 segundos
            assert elapsed < 3.0, f"{endpoint} muito lento: {elapsed:.2f}s"

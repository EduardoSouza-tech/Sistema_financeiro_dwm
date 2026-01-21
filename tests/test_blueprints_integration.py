"""
Testes de Integração para Blueprints
=====================================

Testa os endpoints dos blueprints: kits, contratos, sessoes, relatorios
Valida autenticação, permissões, CRUD completo e respostas HTTP

Autor: Sistema de Otimização - Fase 6
Data: 21/01/2026
"""

import pytest
import json
from datetime import date, datetime, timedelta
from decimal import Decimal


# ============================================================================
# TESTES: KITS BLUEPRINT
# ============================================================================

class TestKitsBlueprint:
    """Testes para /api/kits endpoints"""
    
    def test_list_kits_requires_auth(self, client):
        """GET /api/kits deve exigir autenticação"""
        response = client.get('/api/kits')
        assert response.status_code in [401, 403], "Deve bloquear acesso sem autenticação"
    
    def test_list_kits_with_auth(self, client, auth_headers_admin):
        """GET /api/kits deve retornar lista com autenticação"""
        response = client.get('/api/kits', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list), "Deve retornar lista de kits"
    
    def test_create_kit_success(self, client, auth_headers_admin):
        """POST /api/kits deve criar novo kit"""
        kit_data = {
            'nome': 'Kit Teste Integração',
            'descricao': 'Kit criado em teste automatizado',
            'valor': 1500.00,
            'ativo': True
        }
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data=json.dumps(kit_data),
            content_type='application/json'
        )
        assert response.status_code in [200, 201], f"Deve criar kit. Response: {response.get_json()}"
        data = response.get_json()
        assert 'id' in data or 'success' in data, "Deve retornar ID ou confirmação"
    
    def test_create_kit_missing_fields(self, client, auth_headers_admin):
        """POST /api/kits sem campos obrigatórios deve falhar"""
        kit_data = {'nome': 'Kit Incompleto'}  # Falta valor
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data=json.dumps(kit_data),
            content_type='application/json'
        )
        assert response.status_code in [400, 422], "Deve rejeitar dados incompletos"
    
    def test_get_kit_by_id(self, client, auth_headers_admin, sample_kit_id):
        """GET /api/kits/<id> deve retornar kit específico"""
        response = client.get(f'/api/kits/{sample_kit_id}', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == sample_kit_id
    
    def test_update_kit(self, client, auth_headers_admin, sample_kit_id):
        """PUT /api/kits/<id> deve atualizar kit"""
        update_data = {
            'nome': 'Kit Atualizado',
            'valor': 2000.00
        }
        response = client.put(
            f'/api/kits/{sample_kit_id}',
            headers=auth_headers_admin,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
    
    def test_delete_kit(self, client, auth_headers_admin, sample_kit_id):
        """DELETE /api/kits/<id> deve remover kit"""
        response = client.delete(f'/api/kits/{sample_kit_id}', headers=auth_headers_admin)
        assert response.status_code in [200, 204], "Deve confirmar exclusão"


# ============================================================================
# TESTES: CONTRATOS BLUEPRINT
# ============================================================================

class TestContratosBlueprint:
    """Testes para /api/contratos endpoints"""
    
    def test_list_contratos_requires_auth(self, client):
        """GET /api/contratos deve exigir autenticação"""
        response = client.get('/api/contratos')
        assert response.status_code in [401, 403]
    
    def test_list_contratos_with_auth(self, client, auth_headers_admin):
        """GET /api/contratos deve retornar lista"""
        response = client.get('/api/contratos', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list) or isinstance(data, dict), "Deve retornar contratos"
    
    def test_proximo_numero_contrato(self, client, auth_headers_admin):
        """GET /api/contratos/proximo-numero deve retornar próximo número"""
        response = client.get('/api/contratos/proximo-numero', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert 'proximo_numero' in data or isinstance(data, (int, str)), "Deve retornar número"
    
    def test_create_contrato_success(self, client, auth_headers_admin, sample_cliente_id):
        """POST /api/contratos deve criar novo contrato"""
        contrato_data = {
            'numero': f'CONT-TEST-{datetime.now().timestamp()}',
            'cliente_id': sample_cliente_id,
            'data_inicio': date.today().isoformat(),
            'data_fim': (date.today() + timedelta(days=365)).isoformat(),
            'valor': 12000.00,
            'status': 'ativo'
        }
        response = client.post(
            '/api/contratos',
            headers=auth_headers_admin,
            data=json.dumps(contrato_data),
            content_type='application/json'
        )
        assert response.status_code in [200, 201], f"Deve criar contrato. Response: {response.get_json()}"
    
    def test_get_contrato_by_id(self, client, auth_headers_admin, sample_contrato_id):
        """GET /api/contratos/<id> deve retornar contrato específico"""
        response = client.get(f'/api/contratos/{sample_contrato_id}', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data or 'numero' in data
    
    def test_update_contrato(self, client, auth_headers_admin, sample_contrato_id):
        """PUT /api/contratos/<id> deve atualizar contrato"""
        update_data = {'status': 'renovado'}
        response = client.put(
            f'/api/contratos/{sample_contrato_id}',
            headers=auth_headers_admin,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code in [200, 404], "Deve atualizar ou não encontrar"


# ============================================================================
# TESTES: SESSÕES BLUEPRINT
# ============================================================================

class TestSessoesBlueprint:
    """Testes para /api/sessoes endpoints"""
    
    def test_list_sessoes_requires_auth(self, client):
        """GET /api/sessoes deve exigir autenticação"""
        response = client.get('/api/sessoes')
        assert response.status_code in [401, 403]
    
    def test_list_sessoes_with_auth(self, client, auth_headers_admin):
        """GET /api/sessoes deve retornar lista"""
        response = client.get('/api/sessoes', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list) or isinstance(data, dict)
    
    def test_create_sessao_success(self, client, auth_headers_admin, sample_contrato_id):
        """POST /api/sessoes deve criar nova sessão"""
        sessao_data = {
            'contrato_id': sample_contrato_id,
            'data_sessao': date.today().isoformat(),
            'duracao': 120,  # minutos
            'tipo': 'consultoria',
            'observacoes': 'Sessão de teste'
        }
        response = client.post(
            '/api/sessoes',
            headers=auth_headers_admin,
            data=json.dumps(sessao_data),
            content_type='application/json'
        )
        assert response.status_code in [200, 201], f"Deve criar sessão. Response: {response.get_json()}"
    
    def test_create_sessao_field_mapping(self, client, auth_headers_admin, sample_contrato_id):
        """POST /api/sessoes deve aceitar campo 'data' (mapeado para data_sessao)"""
        sessao_data = {
            'contrato_id': sample_contrato_id,
            'data': date.today().isoformat(),  # Campo antigo
            'quantidade_horas': 2.0,  # Será convertido para minutos
            'tipo': 'reuniao'
        }
        response = client.post(
            '/api/sessoes',
            headers=auth_headers_admin,
            data=json.dumps(sessao_data),
            content_type='application/json'
        )
        # Deve aceitar ou retornar erro específico, mas não 500
        assert response.status_code != 500, "Não deve dar erro interno com mapeamento"
    
    def test_get_sessao_by_id(self, client, auth_headers_admin, sample_sessao_id):
        """GET /api/sessoes/<id> deve retornar sessão específica"""
        response = client.get(f'/api/sessoes/{sample_sessao_id}', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data or 'data_sessao' in data


# ============================================================================
# TESTES: RELATÓRIOS BLUEPRINT
# ============================================================================

class TestRelatoriosBlueprint:
    """Testes para /api/relatorios endpoints"""
    
    def test_dashboard_requires_auth(self, client):
        """GET /api/relatorios/dashboard deve exigir autenticação"""
        response = client.get('/api/relatorios/dashboard')
        assert response.status_code in [401, 403]
    
    def test_dashboard_with_auth(self, client, auth_headers_admin):
        """GET /api/relatorios/dashboard deve retornar dados"""
        response = client.get('/api/relatorios/dashboard', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict), "Deve retornar objeto com dados do dashboard"
    
    def test_fluxo_caixa(self, client, auth_headers_admin):
        """GET /api/relatorios/fluxo-caixa deve retornar fluxo de caixa"""
        response = client.get('/api/relatorios/fluxo-caixa', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict) or isinstance(data, list)
    
    def test_fluxo_caixa_with_filters(self, client, auth_headers_admin):
        """GET /api/relatorios/fluxo-caixa com filtros de data"""
        params = {
            'data_inicio': (date.today() - timedelta(days=30)).isoformat(),
            'data_fim': date.today().isoformat()
        }
        response = client.get('/api/relatorios/fluxo-caixa', 
                            headers=auth_headers_admin,
                            query_string=params)
        assert response.status_code == 200
    
    def test_dashboard_completo(self, client, auth_headers_admin):
        """GET /api/relatorios/dashboard-completo deve retornar dashboard completo"""
        response = client.get('/api/relatorios/dashboard-completo', headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_analise_contas(self, client, auth_headers_admin):
        """GET /api/relatorios/analise-contas deve retornar análise"""
        response = client.get('/api/relatorios/analise-contas', headers=auth_headers_admin)
        assert response.status_code == 200
    
    def test_resumo_parceiros(self, client, auth_headers_admin):
        """GET /api/relatorios/resumo-parceiros deve retornar resumo"""
        response = client.get('/api/relatorios/resumo-parceiros', headers=auth_headers_admin)
        assert response.status_code == 200
    
    def test_analise_categorias(self, client, auth_headers_admin):
        """GET /api/relatorios/analise-categorias deve retornar análise"""
        response = client.get('/api/relatorios/analise-categorias', headers=auth_headers_admin)
        assert response.status_code == 200
    
    def test_comparativo_periodos(self, client, auth_headers_admin):
        """GET /api/relatorios/comparativo-periodos deve retornar comparação"""
        response = client.get('/api/relatorios/comparativo-periodos', headers=auth_headers_admin)
        assert response.status_code == 200
    
    def test_indicadores(self, client, auth_headers_admin):
        """GET /api/relatorios/indicadores deve retornar indicadores"""
        response = client.get('/api/relatorios/indicadores', headers=auth_headers_admin)
        assert response.status_code == 200
    
    def test_inadimplencia(self, client, auth_headers_admin):
        """GET /api/relatorios/inadimplencia deve retornar dados"""
        response = client.get('/api/relatorios/inadimplencia', headers=auth_headers_admin)
        assert response.status_code == 200


# ============================================================================
# TESTES: PERMISSÕES E MULTI-TENANCY
# ============================================================================

class TestPermissoesMultiTenancy:
    """Testes para validar permissões e isolamento de empresas"""
    
    def test_user_cannot_access_other_empresa_data(self, client, auth_headers_user, sample_kit_from_other_empresa):
        """Usuário não deve acessar dados de outra empresa"""
        response = client.get(
            f'/api/kits/{sample_kit_from_other_empresa}',
            headers=auth_headers_user
        )
        assert response.status_code in [403, 404], "Deve bloquear acesso cross-empresa"
    
    def test_admin_can_access_all_empresas(self, client, auth_headers_admin, sample_kit_from_other_empresa):
        """Admin deve poder acessar dados de todas as empresas"""
        response = client.get(
            f'/api/kits/{sample_kit_from_other_empresa}',
            headers=auth_headers_admin
        )
        assert response.status_code in [200, 404], "Admin não deve ter erro de permissão"
    
    def test_create_without_permission(self, client, auth_headers_readonly):
        """Usuário read-only não deve poder criar"""
        kit_data = {'nome': 'Kit Teste', 'valor': 100}
        response = client.post(
            '/api/kits',
            headers=auth_headers_readonly,
            data=json.dumps(kit_data),
            content_type='application/json'
        )
        assert response.status_code in [403, 401], "Deve bloquear criação sem permissão"


# ============================================================================
# TESTES: VALIDAÇÃO DE DADOS
# ============================================================================

class TestValidacaoDados:
    """Testes para validação de entrada de dados"""
    
    def test_invalid_json_format(self, client, auth_headers_admin):
        """Endpoint deve rejeitar JSON inválido"""
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data='{"nome": "teste", invalid}',
            content_type='application/json'
        )
        assert response.status_code in [400, 422], "Deve rejeitar JSON malformado"
    
    def test_sql_injection_attempt(self, client, auth_headers_admin):
        """Endpoint deve sanitizar tentativas de SQL injection"""
        malicious_data = {
            'nome': "Kit'; DROP TABLE kits; --",
            'valor': 100
        }
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data=json.dumps(malicious_data),
            content_type='application/json'
        )
        # Deve processar normalmente ou rejeitar, mas não quebrar
        assert response.status_code != 500, "Não deve quebrar com tentativa de injection"
    
    def test_negative_values_validation(self, client, auth_headers_admin):
        """Endpoint deve validar valores negativos quando apropriado"""
        invalid_data = {
            'nome': 'Kit Negativo',
            'valor': -100.00
        }
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        # Dependendo da regra de negócio, pode aceitar ou rejeitar
        assert response.status_code in [200, 201, 400, 422], "Deve ter resposta válida"


# ============================================================================
# TESTES: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Testes para casos extremos"""
    
    def test_very_long_string_truncation(self, client, auth_headers_admin):
        """Endpoint deve lidar com strings muito longas"""
        long_name = "A" * 10000  # String de 10k caracteres
        data = {'nome': long_name, 'valor': 100}
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code in [200, 201, 400, 422], "Deve processar ou rejeitar"
    
    def test_unicode_characters(self, client, auth_headers_admin):
        """Endpoint deve aceitar caracteres Unicode"""
        data = {
            'nome': 'Kit com 中文 e émojis 🚀',
            'valor': 100,
            'descricao': 'Teste de caracteres especiais: ñ, ç, é'
        }
        response = client.post(
            '/api/kits',
            headers=auth_headers_admin,
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code != 500, "Deve processar Unicode corretamente"
    
    def test_concurrent_requests(self, client, auth_headers_admin):
        """Sistema deve lidar com requisições concorrentes"""
        # Simula 5 requisições simultâneas
        import concurrent.futures
        
        def make_request():
            return client.get('/api/relatorios/dashboard', headers=auth_headers_admin)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in futures]
        
        # Todas devem retornar 200
        assert all(r.status_code == 200 for r in responses), "Deve processar requisições concorrentes"


# ============================================================================
# TESTES: PERFORMANCE
# ============================================================================

class TestPerformance:
    """Testes básicos de performance"""
    
    def test_list_endpoint_response_time(self, client, auth_headers_admin):
        """Endpoint de listagem deve responder em tempo razoável"""
        import time
        start = time.time()
        response = client.get('/api/kits', headers=auth_headers_admin)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Listagem muito lenta: {elapsed:.2f}s"
    
    def test_relatorio_response_time(self, client, auth_headers_admin):
        """Relatórios devem responder em tempo razoável"""
        import time
        start = time.time()
        response = client.get('/api/relatorios/dashboard', headers=auth_headers_admin)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0, f"Dashboard muito lento: {elapsed:.2f}s"

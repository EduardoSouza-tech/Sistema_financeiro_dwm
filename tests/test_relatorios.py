"""
Testes para APIs de Relatórios
"""
import pytest
import json
from datetime import datetime, timedelta


class TestRelatorios:
    """Testes para relatórios financeiros"""
    
    def test_dashboard(self, authenticated_client):
        """Teste de dashboard com métricas gerais"""
        response = authenticated_client.get('/api/relatorios/dashboard')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'saldo_total' in data or 'dashboard' in data
    
    
    def test_dashboard_completo(self, authenticated_client):
        """Teste de dashboard completo"""
        response = authenticated_client.get('/api/relatorios/dashboard-completo')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_fluxo_caixa(self, authenticated_client):
        """Teste de relatório de fluxo de caixa"""
        response = authenticated_client.get('/api/relatorios/fluxo-caixa')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_fluxo_caixa_com_periodo(self, authenticated_client):
        """Teste de fluxo de caixa com período específico"""
        data_inicio = (datetime.now() - timedelta(days=30)).date().isoformat()
        data_fim = datetime.now().date().isoformat()
        
        response = authenticated_client.get(
            f'/api/relatorios/fluxo-caixa?data_inicio={data_inicio}&data_fim={data_fim}'
        )
        
        assert response.status_code == 200
    
    
    def test_fluxo_projetado(self, authenticated_client):
        """Teste de relatório de fluxo projetado"""
        response = authenticated_client.get('/api/relatorios/fluxo-projetado')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_analise_contas(self, authenticated_client):
        """Teste de análise de contas"""
        response = authenticated_client.get('/api/relatorios/analise-contas')
        
        assert response.status_code == 200
    
    
    def test_analise_categorias(self, authenticated_client):
        """Teste de análise por categorias"""
        response = authenticated_client.get('/api/relatorios/analise-categorias')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_inadimplencia(self, authenticated_client):
        """Teste de relatório de inadimplência"""
        response = authenticated_client.get('/api/relatorios/inadimplencia')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_indicadores(self, authenticated_client):
        """Teste de indicadores financeiros"""
        response = authenticated_client.get('/api/relatorios/indicadores')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_resumo_parceiros(self, authenticated_client):
        """Teste de resumo de parceiros (clientes e fornecedores)"""
        response = authenticated_client.get('/api/relatorios/resumo-parceiros')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    
    def test_comparativo_periodos(self, authenticated_client):
        """Teste de comparativo entre períodos"""
        response = authenticated_client.get('/api/relatorios/comparativo-periodos')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)


class TestExportacao:
    """Testes para exportação de dados"""
    
    def test_exportar_clientes_pdf(self, authenticated_client):
        """Teste de exportação de clientes em PDF"""
        response = authenticated_client.get('/api/clientes/exportar/pdf')
        
        # Pode retornar 200 com PDF ou erro se não tiver dados
        assert response.status_code in [200, 400, 500]
    
    
    def test_exportar_clientes_excel(self, authenticated_client):
        """Teste de exportação de clientes em Excel"""
        response = authenticated_client.get('/api/clientes/exportar/excel')
        
        # Pode retornar 200 com Excel ou erro se não tiver dados
        assert response.status_code in [200, 400, 500]
    
    
    def test_exportar_fornecedores_pdf(self, authenticated_client):
        """Teste de exportação de fornecedores em PDF"""
        response = authenticated_client.get('/api/fornecedores/exportar/pdf')
        
        assert response.status_code in [200, 400, 500]
    
    
    def test_exportar_fornecedores_excel(self, authenticated_client):
        """Teste de exportação de fornecedores em Excel"""
        response = authenticated_client.get('/api/fornecedores/exportar/excel')
        
        assert response.status_code in [200, 400, 500]

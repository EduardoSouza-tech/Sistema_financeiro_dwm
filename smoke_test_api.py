#!/usr/bin/env python3
"""
🔥 SMOKE TESTS AUTOMATIZADOS - API
=====================================

Testa endpoints críticos da API antes de deploy.

USO:
    python smoke_test_api.py

RESULTADO:
    Exit 0 = Todos os testes passaram (deploy LIBERADO)
    Exit 1 = Algum teste falhou (deploy BLOQUEADO)

INTEGRAÇÃO COM CI/CD:
    # .github/workflows/ci.yml
    - run: python smoke_test_api.py
      
Se falhar, GitHub Actions bloqueia merge/deploy.
"""

import sys
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# ========================================
# CONFIGURAÇÃO
# ========================================

# URL base da API (alterar conforme ambiente)
API_BASE = "http://localhost:5000"  # Local
# API_BASE = "https://your-staging.railway.app"  # Staging
# API_BASE = "https://your-production.railway.app"  # Produção

# Credenciais de teste (NUNCA usar admin em produção!)
TEST_USER = {
    "username": "teste",
    "password": "teste123"
}

# Timeout das requisições (segundos)
REQUEST_TIMEOUT = 10

# ========================================
# CLASSE DE TESTE
# ========================================

class SmokeTest:
    def __init__(self):
        self.session = requests.Session()
        self.session_token = None
        self.empresa_id = None
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def log_success(self, test_name: str):
        """Registra teste que passou"""
        self.passed += 1
        print(f"✅ {test_name}")
        
    def log_failure(self, test_name: str, error: str):
        """Registra teste que falhou"""
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}")
        print(f"   Erro: {error}")
        
    def assert_status(self, response: requests.Response, expected: int, test_name: str) -> bool:
        """Verifica status code da resposta"""
        if response.status_code != expected:
            self.log_failure(
                test_name,
                f"Status esperado {expected}, recebido {response.status_code}"
            )
            return False
        return True
        
    def assert_not_empty(self, data: List, test_name: str) -> bool:
        """Verifica se lista não está vazia"""
        if not data or len(data) == 0:
            self.log_failure(test_name, "Lista vazia quando esperado ter dados")
            return False
        return True

    # ========================================
    # TESTES
    # ========================================
    
    def test_01_health_check(self):
        """Servidor está online?"""
        test_name = "01. Health Check"
        try:
            response = self.session.get(
                f"{API_BASE}/health",
                timeout=REQUEST_TIMEOUT
            )
            
            if self.assert_status(response, 200, test_name):
                self.log_success(test_name)
                return True
                
        except requests.exceptions.ConnectionError:
            self.log_failure(test_name, "Não foi possível conectar ao servidor")
        except Exception as e:
            self.log_failure(test_name, str(e))
        
        return False
    
    def test_02_login(self):
        """Login funciona?"""
        test_name = "02. Login"
        try:
            response = self.session.post(
                f"{API_BASE}/api/login",
                json=TEST_USER,
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            data = response.json()
            
            # Verificar se retornou session_token
            if 'session_token' not in data:
                self.log_failure(test_name, "Resposta não contém session_token")
                return False
                
            # Armazenar token para próximos testes
            self.session_token = data['session_token']
            self.empresa_id = data.get('empresa_id')
            
            # Adicionar token nos headers
            self.session.headers.update({
                'X-Session-Token': self.session_token
            })
            
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_03_check_auth(self):
        """Autenticação persiste?"""
        test_name = "03. Verificar Autenticação"
        try:
            response = self.session.get(
                f"{API_BASE}/api/check_session",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            data = response.json()
            
            if not data.get('authenticated'):
                self.log_failure(test_name, "Usuário não está autenticado")
                return False
                
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_04_categorias(self):
        """Categorias carregam?"""
        test_name = "04. Listar Categorias"
        try:
            response = self.session.get(
                f"{API_BASE}/api/categorias",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            categorias = response.json()
            
            # Deve ter ao menos 1 categoria
            if not self.assert_not_empty(categorias, test_name):
                return False
                
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_05_fornecedores(self):
        """⚠️ CRÍTICO: Fornecedores carregam? (Bug histórico: Modal vazio)"""
        test_name = "05. Listar Fornecedores [CRÍTICO]"
        try:
            response = self.session.get(
                f"{API_BASE}/api/fornecedores",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            data = response.json()
            fornecedores = data.get('data', [])
            
            # ⚠️ CRÍTICO: Deve ter ao menos 1 fornecedor
            # Se estiver vazio, modal de despesa ficará sem opções
            if not self.assert_not_empty(fornecedores, test_name):
                return False
                
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_06_clientes(self):
        """Clientes carregam?"""
        test_name = "06. Listar Clientes"
        try:
            response = self.session.get(
                f"{API_BASE}/api/clientes",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            # Pode estar vazio (sistema novo), mas deve retornar 200
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_07_contas_bancarias(self):
        """Contas bancárias carregam?"""
        test_name = "07. Listar Contas Bancárias"
        try:
            response = self.session.get(
                f"{API_BASE}/api/bancos",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            data = response.json()
            bancos = data.get('data', [])
            
            # Deve ter ao menos 1 conta
            if not self.assert_not_empty(bancos, test_name):
                return False
                
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_08_lancamentos(self):
        """Lançamentos carregam?"""
        test_name = "08. Listar Lançamentos"
        try:
            response = self.session.get(
                f"{API_BASE}/api/lancamentos",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            # Pode estar vazio, mas deve retornar 200
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_09_eventos_listar(self):
        """Eventos carregam?"""
        test_name = "09. Listar Eventos"
        try:
            response = self.session.get(
                f"{API_BASE}/api/eventos",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name):
                return False
                
            # Pode estar vazio, mas deve retornar 200
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            return False
    
    def test_10_evento_crud(self):
        """⚠️ CRÍTICO: CRUD de eventos funciona? (Bugs históricos: Update/Delete)"""
        test_name = "10. CRUD Eventos [CRÍTICO]"
        evento_id = None
        
        try:
            # 1. Criar evento
            hoje = datetime.now().strftime("%Y-%m-%d")
            novo_evento = {
                "nome_evento": "SMOKE TEST - Pode deletar",
                "data_evento": hoje,
                "tipo_evento": "Outros",
                "local_evento": "Teste Automatizado",
                "status": "Planejamento"
            }
            
            response = self.session.post(
                f"{API_BASE}/api/eventos",
                json=novo_evento,
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 201, test_name + " (CREATE)"):
                return False
                
            data = response.json()
            evento_id = data.get('id')
            
            if not evento_id:
                self.log_failure(test_name, "Evento criado mas sem ID retornado")
                return False
            
            # 2. ⚠️ CRÍTICO: Atualizar evento (Bug histórico: data não persistia)
            amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            evento_atualizado = {
                "nome_evento": "SMOKE TEST - EDITADO",
                "data_evento": amanha,
                "status": "Em Andamento"
            }
            
            response = self.session.put(
                f"{API_BASE}/api/eventos/{evento_id}",
                json=evento_atualizado,
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name + " (UPDATE)"):
                return False
            
            # 3. Verificar se mudança persistiu (ler de volta)
            response = self.session.get(
                f"{API_BASE}/api/eventos/{evento_id}",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name + " (READ)"):
                return False
                
            evento_verificado = response.json()
            
            # ⚠️ CRÍTICO: Data DEVE ter sido alterada
            if evento_verificado.get('data_evento') != amanha:
                self.log_failure(
                    test_name,
                    f"Data não persistiu! Esperado {amanha}, obtido {evento_verificado.get('data_evento')}"
                )
                return False
            
            # 4. ⚠️ CRÍTICO: Deletar evento (Bug histórico: erro 500)
            response = self.session.delete(
                f"{API_BASE}/api/eventos/{evento_id}",
                timeout=REQUEST_TIMEOUT
            )
            
            if not self.assert_status(response, 200, test_name + " (DELETE)"):
                return False
            
            # Sucesso!
            self.log_success(test_name)
            return True
            
        except Exception as e:
            self.log_failure(test_name, str(e))
            
            # Tentar limpar evento de teste se foi criado
            if evento_id:
                try:
                    self.session.delete(f"{API_BASE}/api/eventos/{evento_id}")
                except:
                    pass
            
            return False
    
    # ========================================
    # EXECUÇÃO DOS TESTES
    # ========================================
    
    def run_all_tests(self):
        """Executa todos os testes em ordem"""
        print("=" * 60)
        print("🔥 SMOKE TESTS - Iniciando...")
        print(f"📍 API Base: {API_BASE}")
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # Lista de testes na ordem
        tests = [
            self.test_01_health_check,
            self.test_02_login,
            self.test_03_check_auth,
            self.test_04_categorias,
            self.test_05_fornecedores,  # ⚠️ CRÍTICO
            self.test_06_clientes,
            self.test_07_contas_bancarias,
            self.test_08_lancamentos,
            self.test_09_eventos_listar,
            self.test_10_evento_crud,  # ⚠️ CRÍTICO
        ]
        
        # Executar cada teste
        for test in tests:
            test()
            print()  # Linha em branco entre testes
        
        # Resultado final
        print("=" * 60)
        print("📊 RESULTADO FINAL:")
        print(f"   ✅ Testes passaram: {self.passed}")
        print(f"   ❌ Testes falharam: {self.failed}")
        print("=" * 60)
        
        if self.failed == 0:
            print()
            print("🎉 SUCESSO! Todos os testes passaram.")
            print("✅ Deploy LIBERADO")
            print()
            return 0  # Exit code 0 = sucesso
        else:
            print()
            print("⚠️ FALHA! Alguns testes não passaram:")
            print()
            for error in self.errors:
                print(f"   • {error}")
            print()
            print("❌ Deploy BLOQUEADO")
            print("🛠️ Corrija os erros antes de fazer push!")
            print()
            return 1  # Exit code 1 = falha

# ========================================
# MAIN
# ========================================

def main():
    """Entry point do script"""
    try:
        smoker = SmokeTest()
        exit_code = smoker.run_all_tests()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos pelo usuário")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erro fatal ao executar testes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

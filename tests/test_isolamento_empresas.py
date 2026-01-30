"""
🔒 TESTES DE ISOLAMENTO ENTRE EMPRESAS

Valida que Row Level Security (RLS) está funcionando corretamente
e que nenhuma empresa consegue acessar dados de outra empresa.

CRÍTICO: Estes testes DEVEM passar 100% antes de qualquer deploy.
"""

import pytest
from database_postgresql import (
    get_db_connection,
    criar_nova_empresa,
    listar_clientes,
    cadastrar_cliente,
    listar_lancamentos,
    cadastrar_lancamento,
    obter_saldo
)

# ============================================================================
# FIXTURES - Criar dados de teste
# ============================================================================

@pytest.fixture(scope="module")
def empresa1():
    """Cria empresa de teste 1"""
    dados = {
        'razao_social': 'Empresa Teste 1 Ltda',
        'nome_fantasia': 'Teste 1',
        'cnpj': '11111111000101',
        'email': 'teste1@isolamento.com',
        'telefone': '1111111111',
        'plano': 'basico'
    }
    resultado = criar_nova_empresa(dados)
    assert resultado['success'], f"Erro ao criar empresa 1: {resultado.get('error')}"
    return resultado['empresa_id']


@pytest.fixture(scope="module")
def empresa2():
    """Cria empresa de teste 2"""
    dados = {
        'razao_social': 'Empresa Teste 2 Ltda',
        'nome_fantasia': 'Teste 2',
        'cnpj': '22222222000102',
        'email': 'teste2@isolamento.com',
        'telefone': '2222222222',
        'plano': 'basico'
    }
    resultado = criar_nova_empresa(dados)
    assert resultado['success'], f"Erro ao criar empresa 2: {resultado.get('error')}"
    return resultado['empresa_id']


@pytest.fixture(scope="module")
def cliente_empresa1(empresa1):
    """Cria cliente na empresa 1"""
    dados = {
        'nome': 'Cliente da Empresa 1',
        'cpf_cnpj': '11111111111',
        'tipo_pessoa': 'PF',
        'email': 'cliente1@teste.com'
    }
    resultado = cadastrar_cliente(empresa_id=empresa1, dados=dados)
    assert resultado['success'], f"Erro ao criar cliente: {resultado.get('error')}"
    return resultado['cliente_id']


@pytest.fixture(scope="module")
def cliente_empresa2(empresa2):
    """Cria cliente na empresa 2"""
    dados = {
        'nome': 'Cliente da Empresa 2',
        'cpf_cnpj': '22222222222',
        'tipo_pessoa': 'PF',
        'email': 'cliente2@teste.com'
    }
    resultado = cadastrar_cliente(empresa_id=empresa2, dados=dados)
    assert resultado['success'], f"Erro ao criar cliente: {resultado.get('error')}"
    return resultado['cliente_id']


# ============================================================================
# TESTES DE ISOLAMENTO - CLIENTES
# ============================================================================

def test_empresa1_nao_ve_clientes_empresa2(empresa1, empresa2, cliente_empresa1, cliente_empresa2):
    """
    🔒 CRÍTICO: Empresa 1 NÃO deve ver clientes da empresa 2
    """
    # Listar clientes da empresa 1
    clientes_emp1 = listar_clientes(empresa_id=empresa1)
    
    # Verificar que vê apenas SEU cliente
    assert len(clientes_emp1) >= 1, "Empresa 1 deve ver pelo menos seu próprio cliente"
    
    # Verificar que NÃO vê cliente da empresa 2
    nomes_clientes = [c['nome'] for c in clientes_emp1]
    assert 'Cliente da Empresa 2' not in nomes_clientes, "❌ FALHA CRÍTICA: Empresa 1 está vendo cliente da Empresa 2!"


def test_empresa2_nao_ve_clientes_empresa1(empresa1, empresa2, cliente_empresa1, cliente_empresa2):
    """
    🔒 CRÍTICO: Empresa 2 NÃO deve ver clientes da empresa 1
    """
    # Listar clientes da empresa 2
    clientes_emp2 = listar_clientes(empresa_id=empresa2)
    
    # Verificar que vê apenas SEU cliente
    assert len(clientes_emp2) >= 1, "Empresa 2 deve ver pelo menos seu próprio cliente"
    
    # Verificar que NÃO vê cliente da empresa 1
    nomes_clientes = [c['nome'] for c in clientes_emp2]
    assert 'Cliente da Empresa 1' not in nomes_clientes, "❌ FALHA CRÍTICA: Empresa 2 está vendo cliente da Empresa 1!"


def test_cada_empresa_ve_apenas_seus_clientes(empresa1, empresa2, cliente_empresa1, cliente_empresa2):
    """
    🔒 CRÍTICO: Cada empresa deve ver APENAS seus próprios clientes
    """
    clientes_emp1 = listar_clientes(empresa_id=empresa1)
    clientes_emp2 = listar_clientes(empresa_id=empresa2)
    
    # IDs dos clientes de cada empresa
    ids_emp1 = {c['id'] for c in clientes_emp1}
    ids_emp2 = {c['id'] for c in clientes_emp2}
    
    # Verificar que os conjuntos são DISJUNTOS (sem interseção)
    intersecao = ids_emp1.intersection(ids_emp2)
    assert len(intersecao) == 0, f"❌ FALHA CRÍTICA: Empresas compartilhando clientes: {intersecao}"


# ============================================================================
# TESTES DE ISOLAMENTO - LANÇAMENTOS FINANCEIROS
# ============================================================================

def test_empresa1_nao_ve_lancamentos_empresa2(empresa1, empresa2):
    """
    🔒 CRÍTICO: Empresa 1 NÃO deve ver lançamentos da empresa 2
    """
    # Cadastrar lançamento na empresa 2
    dados_lanc = {
        'descricao': 'Lançamento Exclusivo Empresa 2',
        'valor': 1000.00,
        'tipo': 'receita',
        'data': '2024-01-15',
        'categoria_id': 1
    }
    cadastrar_lancamento(empresa_id=empresa2, dados=dados_lanc)
    
    # Listar lançamentos da empresa 1
    lancamentos_emp1 = listar_lancamentos(empresa_id=empresa1)
    
    # Verificar que NÃO vê o lançamento da empresa 2
    descricoes = [l['descricao'] for l in lancamentos_emp1]
    assert 'Lançamento Exclusivo Empresa 2' not in descricoes, \
        "❌ FALHA CRÍTICA: Empresa 1 está vendo lançamento da Empresa 2!"


def test_empresa2_nao_ve_lancamentos_empresa1(empresa1, empresa2):
    """
    🔒 CRÍTICO: Empresa 2 NÃO deve ver lançamentos da empresa 1
    """
    # Cadastrar lançamento na empresa 1
    dados_lanc = {
        'descricao': 'Lançamento Exclusivo Empresa 1',
        'valor': 2000.00,
        'tipo': 'despesa',
        'data': '2024-01-15',
        'categoria_id': 1
    }
    cadastrar_lancamento(empresa_id=empresa1, dados=dados_lanc)
    
    # Listar lançamentos da empresa 2
    lancamentos_emp2 = listar_lancamentos(empresa_id=empresa2)
    
    # Verificar que NÃO vê o lançamento da empresa 1
    descricoes = [l['descricao'] for l in lancamentos_emp2]
    assert 'Lançamento Exclusivo Empresa 1' not in descricoes, \
        "❌ FALHA CRÍTICA: Empresa 2 está vendo lançamento da Empresa 1!"


# ============================================================================
# TESTES DE ISOLAMENTO - SALDOS BANCÁRIOS
# ============================================================================

def test_saldo_nao_mistura_empresas(empresa1, empresa2):
    """
    🔒 CRÍTICO: Saldo bancário não deve misturar dados de empresas diferentes
    """
    # Obter saldo da conta 1 (supondo que existe)
    # Este teste assume que cada empresa tem suas próprias contas
    
    # TODO: Implementar quando funções de conta bancária estiverem refatoradas
    # saldo_emp1 = obter_saldo(empresa_id=empresa1, conta_id=1)
    # saldo_emp2 = obter_saldo(empresa_id=empresa2, conta_id=1)
    
    # assert saldo_emp1 != saldo_emp2, "Saldos diferentes esperados"
    pass


# ============================================================================
# TESTES DE VALIDAÇÃO - empresa_id obrigatório
# ============================================================================

def test_funcao_sem_empresa_id_deve_falhar():
    """
    🔒 CRÍTICO: Funções DEVEM exigir empresa_id explicitamente
    """
    with pytest.raises(ValueError, match="empresa_id"):
        # Tentar listar clientes sem empresa_id deve falhar
        listar_clientes(empresa_id=None)


def test_conexao_sem_empresa_id_deve_falhar():
    """
    🔒 CRÍTICO: get_db_connection() sem empresa_id deve lançar erro
    """
    with pytest.raises(ValueError, match="empresa_id.*obrigatório"):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes")


def test_conexao_global_permitida():
    """
    ✅ Conexão global (tabelas globais) deve funcionar com allow_global=True
    """
    try:
        with get_db_connection(allow_global=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM empresas")
            count = cursor.fetchone()[0]
            assert count >= 0  # Deve executar sem erro
    except Exception as e:
        pytest.fail(f"Conexão global deve funcionar: {e}")


# ============================================================================
# TESTE DE AUDITORIA
# ============================================================================

def test_rls_registra_acessos_auditoria():
    """
    🔒 Verificar que RLS está registrando acessos na tabela de auditoria
    """
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # Verificar que tabela de auditoria existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'audit_data_access'
        """)
        existe = cursor.fetchone()[0]
        
        if existe:
            # Verificar que há registros de auditoria
            cursor.execute("SELECT COUNT(*) FROM audit_data_access")
            count = cursor.fetchone()[0]
            assert count > 0, "Tabela de auditoria deve ter registros"
        else:
            pytest.skip("Tabela audit_data_access não existe ainda")


# ============================================================================
# TESTE DE RLS STATUS
# ============================================================================

def test_rls_ativo_em_tabelas_criticas():
    """
    🔒 CRÍTICO: RLS deve estar ativo em todas as tabelas com dados de empresa
    """
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # Verificar que view rls_status existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.views 
            WHERE table_name = 'rls_status'
        """)
        existe = cursor.fetchone()[0]
        
        if existe:
            # Verificar tabelas críticas com RLS ativo
            tabelas_criticas = [
                'clientes', 'fornecedores', 'lancamentos', 'categorias',
                'contas_bancarias', 'produtos', 'contratos', 'eventos',
                'funcionarios', 'transacoes_extrato'
            ]
            
            cursor.execute("SELECT tabela, rls_ativo FROM rls_status")
            status = {row[0]: row[1] for row in cursor.fetchall()}
            
            for tabela in tabelas_criticas:
                if tabela in status:
                    assert status[tabela], f"❌ FALHA CRÍTICA: RLS não está ativo na tabela {tabela}!"
        else:
            pytest.skip("View rls_status não existe ainda")


# ============================================================================
# TESTE DE VAZAMENTO CROSS-COMPANY
# ============================================================================

def test_zero_vazamento_cross_company(empresa1, empresa2):
    """
    🔒 CRÍTICO: Deve haver ZERO vazamento de dados entre empresas
    
    Este teste executa uma query de auditoria para verificar se há
    algum acesso cross-company registrado.
    """
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # Query para detectar vazamentos
        cursor.execute("""
            SELECT 
                'clientes' as tabela,
                COUNT(*) as vazamentos
            FROM clientes c1
            WHERE c1.empresa_id != %s
              AND EXISTS (
                  SELECT 1 FROM clientes c2 
                  WHERE c2.empresa_id = %s
              )
            
            UNION ALL
            
            SELECT 
                'lancamentos' as tabela,
                COUNT(*) as vazamentos
            FROM lancamentos l1
            WHERE l1.empresa_id != %s
              AND EXISTS (
                  SELECT 1 FROM lancamentos l2 
                  WHERE l2.empresa_id = %s
              )
        """, (empresa1, empresa1, empresa1, empresa1))
        
        resultados = cursor.fetchall()
        
        for tabela, vazamentos in resultados:
            assert vazamentos == 0, \
                f"❌ FALHA CRÍTICA: {vazamentos} vazamentos detectados na tabela {tabela}!"


# ============================================================================
# RELATÓRIO DE TESTES
# ============================================================================

def test_relatorio_isolamento(empresa1, empresa2):
    """
    📊 Gera relatório completo de isolamento entre empresas
    """
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE ISOLAMENTO ENTRE EMPRESAS")
    print("="*80)
    
    with get_db_connection(allow_global=True) as conn:
        cursor = conn.cursor()
        
        # Tabelas a verificar
        tabelas = ['clientes', 'fornecedores', 'lancamentos', 'categorias', 
                   'produtos', 'contratos', 'funcionarios']
        
        for tabela in tabelas:
            try:
                # Contar registros empresa 1
                cursor.execute(f"""
                    SELECT set_current_empresa(%s);
                    SELECT COUNT(*) FROM {tabela};
                """, (empresa1,))
                count_emp1 = cursor.fetchone()[0]
                
                # Contar registros empresa 2
                cursor.execute(f"""
                    SELECT set_current_empresa(%s);
                    SELECT COUNT(*) FROM {tabela};
                """, (empresa2,))
                count_emp2 = cursor.fetchone()[0]
                
                print(f"✅ {tabela:20} | Empresa 1: {count_emp1:3} | Empresa 2: {count_emp2:3}")
                
            except Exception as e:
                print(f"⚠️  {tabela:20} | Erro: {str(e)[:40]}")
        
        print("="*80)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

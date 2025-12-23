"""
Sistema de Auto-Teste Completo
Executa testes automáticos de TODAS as funcionalidades ao iniciar
"""
from datetime import datetime, date, timedelta
from models import ContaBancaria, Categoria, TipoLancamento, Lancamento, StatusLancamento
from decimal import Decimal


def executar_testes(db):
    """Executa bateria completa de testes automáticos"""
    print("\n" + "="*70)
    print("🧪 INICIANDO AUTO-TESTE COMPLETO DO SISTEMA")
    print("="*70)
    
    resultados = {
        'sucesso': [],
        'falhas': []
    }
    
    timestamp = datetime.now().strftime('%H%M%S')
    
    # ========== TESTES DE CONTAS BANCÁRIAS ==========
    print("\n📊 Testando CONTAS BANCÁRIAS...")
    
    # TESTE 1: Listar Contas
    try:
        contas = db.listar_contas()
        resultados['sucesso'].append(f"✅ [CONTAS] Listar: {len(contas)} encontradas")
    except Exception as e:
        resultados['falhas'].append(f"❌ [CONTAS] Listar: {str(e)}")
    
    # TESTE 2-4: CRUD Completo de Conta
    conta_teste_nome = f"TESTE-AUTO-{timestamp}"
    try:
        conta_teste = ContaBancaria(
            nome=conta_teste_nome,
            banco="BANCO TESTE",
            agencia="0001",
            conta="12345-6",
            saldo_inicial=1000.0
        )
        conta_id = db.adicionar_conta(conta_teste)
        resultados['sucesso'].append(f"✅ [CONTAS] Criar: ID {conta_id}")
        
        # Atualizar
        try:
            conta_teste.banco = "BANCO ATUALIZADO"
            conta_teste.saldo_inicial = 2000.0
            sucesso = db.atualizar_conta(conta_teste_nome, conta_teste)
            if sucesso:
                resultados['sucesso'].append("✅ [CONTAS] Atualizar")
            else:
                resultados['falhas'].append("❌ [CONTAS] Atualizar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CONTAS] Atualizar: {str(e)}")
        
        # Excluir
        try:
            sucesso = db.excluir_conta(conta_teste_nome)
            if sucesso:
                resultados['sucesso'].append("✅ [CONTAS] Excluir")
            else:
                resultados['falhas'].append("❌ [CONTAS] Excluir: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CONTAS] Excluir: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ [CONTAS] Criar: {str(e)}")
    
    # ========== TESTES DE CATEGORIAS ==========
    print("📁 Testando CATEGORIAS...")
    
    # TESTE 5: Listar Categorias
    try:
        categorias = db.listar_categorias()
        resultados['sucesso'].append(f"✅ [CATEGORIAS] Listar: {len(categorias)} encontradas")
    except Exception as e:
        resultados['falhas'].append(f"❌ [CATEGORIAS] Listar: {str(e)}")
    
    # TESTE 6-8: CRUD Completo de Categoria
    cat_teste_nome = f"TESTE-AUTO-{timestamp}"
    try:
        # Limpar categoria de teste anterior se existir
        try:
            db.excluir_categoria(cat_teste_nome)
        except:
            pass
        
        cat_teste = Categoria(
            nome=cat_teste_nome,
            tipo=TipoLancamento.RECEITA,
            subcategorias=["Sub1", "Sub2"]
        )
        cat_id = db.adicionar_categoria(cat_teste)
        resultados['sucesso'].append(f"✅ [CATEGORIAS] Criar: ID {cat_id}")
        
        # Atualizar
        try:
            cat_teste.subcategorias = ["Sub1", "Sub2", "Sub3"]
            sucesso = db.atualizar_categoria(cat_teste)
            if sucesso:
                resultados['sucesso'].append("✅ [CATEGORIAS] Atualizar")
            else:
                resultados['falhas'].append("❌ [CATEGORIAS] Atualizar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CATEGORIAS] Atualizar: {str(e)}")
        
        # Excluir
        try:
            sucesso = db.excluir_categoria(cat_teste_nome)
            if sucesso:
                resultados['sucesso'].append("✅ [CATEGORIAS] Excluir")
            else:
                resultados['falhas'].append("❌ [CATEGORIAS] Excluir: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CATEGORIAS] Excluir: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ [CATEGORIAS] Criar: {str(e)}")
    
    # ========== TESTES DE CLIENTES ==========
    print("👤 Testando CLIENTES...")
    
    # TESTE 9: Listar Clientes
    try:
        clientes = db.listar_clientes()
        resultados['sucesso'].append(f"✅ [CLIENTES] Listar ativos: {len(clientes)} encontrados")
    except Exception as e:
        resultados['falhas'].append(f"❌ [CLIENTES] Listar: {str(e)}")
    
    # TESTE 10-13: CRUD Completo de Cliente
    cliente_teste_nome = f"CLIENTE-TESTE-{timestamp}"
    try:
        # Limpar cliente de teste anterior se existir
        try:
            db.inativar_cliente(cliente_teste_nome, "Limpeza auto-teste")
        except:
            pass
        
        # Gerar CPF único baseado em timestamp
        cpf_unico = timestamp.ljust(11, '0')  # Preencher com zeros até 11 dígitos
        
        cliente_data = {
            'nome': cliente_teste_nome,
            'cpf': cpf_unico,
            'email': f'teste{timestamp}@teste.com',
            'telefone': '11999999999',
            'endereco': 'Rua Teste, 123'
        }
        cliente_id = db.adicionar_cliente(cliente_data)
        resultados['sucesso'].append(f"✅ [CLIENTES] Criar: ID {cliente_id}")
        
        # Atualizar
        try:
            cliente_data['email'] = 'atualizado@teste.com'
            sucesso = db.atualizar_cliente(cliente_teste_nome, cliente_data)
            if sucesso:
                resultados['sucesso'].append("✅ [CLIENTES] Atualizar")
            else:
                resultados['falhas'].append("❌ [CLIENTES] Atualizar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CLIENTES] Atualizar: {str(e)}")
        
        # Inativar
        try:
            sucesso, msg = db.inativar_cliente(cliente_teste_nome, "Teste automático")
            if sucesso:
                resultados['sucesso'].append("✅ [CLIENTES] Inativar")
            else:
                resultados['falhas'].append(f"❌ [CLIENTES] Inativar: {msg}")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CLIENTES] Inativar: {str(e)}")
        
        # Reativar
        try:
            sucesso = db.reativar_cliente(cliente_teste_nome)
            if sucesso:
                resultados['sucesso'].append("✅ [CLIENTES] Reativar")
            else:
                resultados['falhas'].append("❌ [CLIENTES] Reativar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [CLIENTES] Reativar: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ [CLIENTES] Criar: {str(e)}")
    
    # ========== TESTES DE FORNECEDORES ==========
    print("🏢 Testando FORNECEDORES...")
    
    # TESTE 14: Listar Fornecedores
    try:
        fornecedores = db.listar_fornecedores()
        resultados['sucesso'].append(f"✅ [FORNECEDORES] Listar ativos: {len(fornecedores)} encontrados")
    except Exception as e:
        resultados['falhas'].append(f"❌ [FORNECEDORES] Listar: {str(e)}")
    
    # TESTE 15-18: CRUD Completo de Fornecedor
    fornecedor_teste_nome = f"FORNECEDOR-TESTE-{timestamp}"
    try:
        # Limpar fornecedor de teste anterior se existir
        try:
            db.inativar_fornecedor(fornecedor_teste_nome, "Limpeza auto-teste")
        except:
            pass
        
        # Gerar CNPJ único baseado em timestamp
        cnpj_unico = timestamp.ljust(14, '0')  # Preencher com zeros até 14 dígitos
        
        fornecedor_data = {
            'nome': fornecedor_teste_nome,
            'cnpj': cnpj_unico,
            'razao_social': 'Teste LTDA',
            'email': f'fornecedor{timestamp}@teste.com',
            'telefone': '11888888888'
        }
        fornecedor_id = db.adicionar_fornecedor(fornecedor_data)
        resultados['sucesso'].append(f"✅ [FORNECEDORES] Criar: ID {fornecedor_id}")
        
        # Atualizar
        try:
            fornecedor_data['email'] = 'novo@teste.com'
            sucesso = db.atualizar_fornecedor(fornecedor_teste_nome, fornecedor_data)
            if sucesso:
                resultados['sucesso'].append("✅ [FORNECEDORES] Atualizar")
            else:
                resultados['falhas'].append("❌ [FORNECEDORES] Atualizar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [FORNECEDORES] Atualizar: {str(e)}")
        
        # Inativar
        try:
            sucesso, msg = db.inativar_fornecedor(fornecedor_teste_nome, "Teste automático")
            if sucesso:
                resultados['sucesso'].append("✅ [FORNECEDORES] Inativar")
            else:
                resultados['falhas'].append(f"❌ [FORNECEDORES] Inativar: {msg}")
        except Exception as e:
            resultados['falhas'].append(f"❌ [FORNECEDORES] Inativar: {str(e)}")
        
        # Reativar
        try:
            sucesso = db.reativar_fornecedor(fornecedor_teste_nome)
            if sucesso:
                resultados['sucesso'].append("✅ [FORNECEDORES] Reativar")
            else:
                resultados['falhas'].append("❌ [FORNECEDORES] Reativar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [FORNECEDORES] Reativar: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ [FORNECEDORES] Criar: {str(e)}")
    
    # ========== TESTES DE LANÇAMENTOS ==========
    print("💰 Testando LANÇAMENTOS...")
    
    # TESTE 19: Listar Lançamentos
    try:
        lancamentos = db.listar_lancamentos()
        resultados['sucesso'].append(f"✅ [LANÇAMENTOS] Listar: {len(lancamentos)} encontrados")
    except Exception as e:
        resultados['falhas'].append(f"❌ [LANÇAMENTOS] Listar: {str(e)}")
    
    # TESTE 20-25: CRUD Completo de Lançamento
    try:
        # Criar Receita
        lanc_receita = Lancamento(
            tipo=TipoLancamento.RECEITA,
            descricao=f"RECEITA-TESTE-{timestamp}",
            valor=Decimal("100.00"),
            data_vencimento=date.today(),
            status=StatusLancamento.PENDENTE,
            categoria="TESTE",
            subcategoria="",
            conta_bancaria="",
            pessoa="",
            observacoes="Auto-teste receita"
        )
        lanc_rec_id = db.adicionar_lancamento(lanc_receita)
        resultados['sucesso'].append(f"✅ [LANÇAMENTOS] Criar receita: ID {lanc_rec_id}")
        
        # Criar Despesa
        lanc_despesa = Lancamento(
            tipo=TipoLancamento.DESPESA,
            descricao=f"DESPESA-TESTE-{timestamp}",
            valor=Decimal("50.00"),
            data_vencimento=date.today() + timedelta(days=30),
            status=StatusLancamento.PENDENTE,
            categoria="TESTE",
            subcategoria="",
            conta_bancaria="",
            pessoa="",
            observacoes="Auto-teste despesa"
        )
        lanc_desp_id = db.adicionar_lancamento(lanc_despesa)
        resultados['sucesso'].append(f"✅ [LANÇAMENTOS] Criar despesa: ID {lanc_desp_id}")
        
        # Pagar lançamento
        try:
            sucesso = db.pagar_lancamento(lanc_rec_id, date.today())
            if sucesso:
                resultados['sucesso'].append("✅ [LANÇAMENTOS] Pagar/Liquidar")
            else:
                resultados['falhas'].append("❌ [LANÇAMENTOS] Pagar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [LANÇAMENTOS] Pagar: {str(e)}")
        
        # Cancelar lançamento
        try:
            sucesso = db.cancelar_lancamento(lanc_desp_id)
            if sucesso:
                resultados['sucesso'].append("✅ [LANÇAMENTOS] Cancelar")
            else:
                resultados['falhas'].append("❌ [LANÇAMENTOS] Cancelar: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [LANÇAMENTOS] Cancelar: {str(e)}")
        
        # Excluir lançamentos
        try:
            sucesso1 = db.excluir_lancamento(lanc_rec_id)
            sucesso2 = db.excluir_lancamento(lanc_desp_id)
            if sucesso1 and sucesso2:
                resultados['sucesso'].append("✅ [LANÇAMENTOS] Excluir")
            else:
                resultados['falhas'].append("❌ [LANÇAMENTOS] Excluir: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ [LANÇAMENTOS] Excluir: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ [LANÇAMENTOS] Criar: {str(e)}")
    
    # EXIBIR RESULTADOS
    print("\n" + "-"*70)
    print("📊 RESULTADO DOS TESTES")
    print("-"*70)
    
    print(f"\n✅ SUCESSOS ({len(resultados['sucesso'])}):")
    for sucesso in resultados['sucesso']:
        print(f"  {sucesso}")
    
    if resultados['falhas']:
        print(f"\n❌ FALHAS ({len(resultados['falhas'])}):")
        for falha in resultados['falhas']:
            print(f"  {falha}")
    else:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    
    # RESUMO
    total = len(resultados['sucesso']) + len(resultados['falhas'])
    taxa_sucesso = (len(resultados['sucesso']) / total * 100) if total > 0 else 0
    
    print("\n" + "-"*70)
    print(f"📈 TAXA DE SUCESSO: {taxa_sucesso:.1f}% ({len(resultados['sucesso'])}/{total})")
    print("="*70 + "\n")
    
    return resultados

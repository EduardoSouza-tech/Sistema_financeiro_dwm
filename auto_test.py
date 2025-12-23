"""
Sistema de Auto-Teste
Executa testes automáticos das principais funcionalidades ao iniciar
"""
from datetime import datetime, date
from models import ContaBancaria, Categoria, TipoLancamento, Lancamento, StatusLancamento
from decimal import Decimal


def executar_testes(db):
    """Executa bateria de testes automáticos"""
    print("\n" + "="*60)
    print("🧪 INICIANDO AUTO-TESTE DO SISTEMA")
    print("="*60)
    
    resultados = {
        'sucesso': [],
        'falhas': []
    }
    
    # TESTE 1: Listar Contas
    try:
        contas = db.listar_contas()
        resultados['sucesso'].append(f"✅ Listar contas: {len(contas)} encontradas")
    except Exception as e:
        resultados['falhas'].append(f"❌ Listar contas: {str(e)}")
    
    # TESTE 2: Criar Conta (temporária para teste)
    try:
        conta_teste = ContaBancaria(
            nome=f"TESTE-AUTO-{datetime.now().strftime('%H%M%S')}",
            banco="BANCO TESTE",
            agencia="0001",
            conta="12345-6",
            saldo_inicial=1000.0
        )
        conta_id = db.adicionar_conta(conta_teste)
        resultados['sucesso'].append(f"✅ Criar conta: ID {conta_id}")
        
        # TESTE 3: Atualizar Conta
        try:
            conta_teste.banco = "BANCO ATUALIZADO"
            sucesso = db.atualizar_conta(conta_teste.nome, conta_teste)
            if sucesso:
                resultados['sucesso'].append("✅ Atualizar conta")
            else:
                resultados['falhas'].append("❌ Atualizar conta: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ Atualizar conta: {str(e)}")
        
        # TESTE 4: Excluir Conta
        try:
            sucesso = db.excluir_conta(conta_teste.nome)
            if sucesso:
                resultados['sucesso'].append("✅ Excluir conta")
            else:
                resultados['falhas'].append("❌ Excluir conta: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ Excluir conta: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ Criar conta: {str(e)}")
    
    # TESTE 5: Listar Categorias
    try:
        categorias = db.listar_categorias()
        resultados['sucesso'].append(f"✅ Listar categorias: {len(categorias)} encontradas")
    except Exception as e:
        resultados['falhas'].append(f"❌ Listar categorias: {str(e)}")
    
    # TESTE 6: Criar Categoria
    try:
        cat_teste = Categoria(
            nome=f"TESTE-AUTO-{datetime.now().strftime('%H%M%S')}",
            tipo=TipoLancamento.RECEITA,
            subcategorias=["Sub1", "Sub2"]
        )
        cat_id = db.adicionar_categoria(cat_teste)
        resultados['sucesso'].append(f"✅ Criar categoria: ID {cat_id}")
        
        # TESTE 7: Atualizar Categoria
        try:
            cat_teste.subcategorias = ["Sub1", "Sub2", "Sub3"]
            sucesso = db.atualizar_categoria(cat_teste)
            if sucesso:
                resultados['sucesso'].append("✅ Atualizar categoria")
            else:
                resultados['falhas'].append("❌ Atualizar categoria: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ Atualizar categoria: {str(e)}")
        
        # TESTE 8: Excluir Categoria
        try:
            sucesso = db.excluir_categoria(cat_teste.nome)
            if sucesso:
                resultados['sucesso'].append("✅ Excluir categoria")
            else:
                resultados['falhas'].append("❌ Excluir categoria: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ Excluir categoria: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ Criar categoria: {str(e)}")
    
    # TESTE 9: Listar Clientes
    try:
        clientes = db.listar_clientes()
        resultados['sucesso'].append(f"✅ Listar clientes: {len(clientes)} encontrados")
    except Exception as e:
        resultados['falhas'].append(f"❌ Listar clientes: {str(e)}")
    
    # TESTE 10: Listar Fornecedores
    try:
        fornecedores = db.listar_fornecedores()
        resultados['sucesso'].append(f"✅ Listar fornecedores: {len(fornecedores)} encontrados")
    except Exception as e:
        resultados['falhas'].append(f"❌ Listar fornecedores: {str(e)}")
    
    # TESTE 11: Listar Lançamentos
    try:
        lancamentos = db.listar_lancamentos()
        resultados['sucesso'].append(f"✅ Listar lançamentos: {len(lancamentos)} encontrados")
    except Exception as e:
        resultados['falhas'].append(f"❌ Listar lançamentos: {str(e)}")
    
    # TESTE 12: Criar Lançamento
    try:
        lanc_teste = Lancamento(
            tipo=TipoLancamento.RECEITA,
            descricao=f"TESTE-AUTO-{datetime.now().strftime('%H%M%S')}",
            valor=Decimal("100.00"),
            data_vencimento=date.today(),
            status=StatusLancamento.PENDENTE,
            categoria="TESTE",
            subcategoria="",
            conta_bancaria="",
            pessoa="",
            observacoes="Auto-teste"
        )
        lanc_id = db.adicionar_lancamento(lanc_teste)
        resultados['sucesso'].append(f"✅ Criar lançamento: ID {lanc_id}")
        
        # TESTE 13: Excluir Lançamento
        try:
            sucesso = db.excluir_lancamento(lanc_id)
            if sucesso:
                resultados['sucesso'].append("✅ Excluir lançamento")
            else:
                resultados['falhas'].append("❌ Excluir lançamento: retornou False")
        except Exception as e:
            resultados['falhas'].append(f"❌ Excluir lançamento: {str(e)}")
            
    except Exception as e:
        resultados['falhas'].append(f"❌ Criar lançamento: {str(e)}")
    
    # EXIBIR RESULTADOS
    print("\n" + "-"*60)
    print("📊 RESULTADO DOS TESTES")
    print("-"*60)
    
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
    
    print("\n" + "-"*60)
    print(f"📈 TAXA DE SUCESSO: {taxa_sucesso:.1f}% ({len(resultados['sucesso'])}/{total})")
    print("="*60 + "\n")
    
    return resultados

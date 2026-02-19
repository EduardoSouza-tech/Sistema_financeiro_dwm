"""
Script DIRETO para popular versão 4 - SEM USAR FUNÇÕES DO SISTEMA
Insere contas diretamente no banco Railway
"""
import psycopg2
from psycopg2.extras import RealDictCursor

print("="*80)
print("🚀 POPULAR VERSÃO 4 - DIRETO NO BANCO")
print("="*80)
print()

DATABASE_URL = input("📋 Cole a DATABASE_URL do Railway: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL vazia!")
    exit(1)

EMPRESA_ID = 20
VERSAO_ID = 4

print(f"\n🔗 Conectando...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Conectado!\n")
    
    # Verificar se versão existe
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM plano_contas
        WHERE empresa_id = %s AND versao_id = %s AND deleted_at IS NULL
    """, (EMPRESA_ID, VERSAO_ID))
    
    total_atual = cursor.fetchone()['total']
    print(f"📊 Versão {VERSAO_ID} tem atualmente {total_atual} contas")
    
    if total_atual > 0:
        resposta = input(f"\n⚠️ Já existem {total_atual} contas. Continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            print("⏭️ Cancelado")
            exit(0)
    
    print(f"\n🚀 Inserindo contas...")
    
    # Contas básicas - estrutura mínima
    contas = [
        # ATIVO
        {'codigo': '1', 'nome': 'ATIVO', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1', 'nome': 'ATIVO CIRCULANTE', 'parent': '1', 'nivel': 2, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.01', 'nome': 'Disponível', 'parent': '1.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.01.001', 'nome': 'Caixa', 'parent': '1.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.01.002', 'nome': 'Bancos Conta Movimento', 'parent': '1.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.01.003', 'nome': 'Aplicações Financeiras', 'parent': '1.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.02', 'nome': 'Clientes', 'parent': '1.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.02.001', 'nome': 'Clientes a Receber', 'parent': '1.1.02', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.02.002', 'nome': 'Duplicatas a Receber', 'parent': '1.1.02', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.03', 'nome': 'Estoques', 'parent': '1.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.1.03.001', 'nome': 'Estoque de Mercadorias', 'parent': '1.1.03', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.2', 'nome': 'ATIVO NÃO CIRCULANTE', 'parent': '1', 'nivel': 2, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.2.01', 'nome': 'Imobilizado', 'parent': '1.2', 'nivel': 3, 'tipo': 'sintetica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.2.01.001', 'nome': 'Móveis e Utensílios', 'parent': '1.2.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        {'codigo': '1.2.01.002', 'nome': 'Veículos', 'parent': '1.2.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'ativo', 'nat': 'devedora'},
        
        # PASSIVO
        {'codigo': '2', 'nome': 'PASSIVO', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1', 'nome': 'PASSIVO CIRCULANTE', 'parent': '2', 'nivel': 2, 'tipo': 'sintetica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1.01', 'nome': 'Fornecedores', 'parent': '2.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1.01.001', 'nome': 'Fornecedores a Pagar', 'parent': '2.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1.02', 'nome': 'Obrigações Trabalhistas', 'parent': '2.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1.02.001', 'nome': 'Salários a Pagar', 'parent': '2.1.02', 'nivel': 4, 'tipo': 'analitica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1.03', 'nome': 'Obrigações Fiscais', 'parent': '2.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'passivo', 'nat': 'credora'},
        {'codigo': '2.1.03.001', 'nome': 'Impostos a Recolher', 'parent': '2.1.03', 'nivel': 4, 'tipo': 'analitica', 'class': 'passivo', 'nat': 'credora'},
        
        # PATRIMÔNIO LÍQUIDO
        {'codigo': '3', 'nome': 'PATRIMÔNIO LÍQUIDO', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'class': 'patrimonio_liquido', 'nat': 'credora'},
        {'codigo': '3.1', 'nome': 'Capital Social', 'parent': '3', 'nivel': 2, 'tipo': 'analitica', 'class': 'patrimonio_liquido', 'nat': 'credora'},
        {'codigo': '3.2', 'nome': 'Reservas', 'parent': '3', 'nivel': 2, 'tipo': 'sintetica', 'class': 'patrimonio_liquido', 'nat': 'credora'},
        {'codigo': '3.2.01', 'nome': 'Reserva Legal', 'parent': '3.2', 'nivel': 3, 'tipo': 'analitica', 'class': 'patrimonio_liquido', 'nat': 'credora'},
        {'codigo': '3.3', 'nome': 'Lucros/Prejuízos Acumulados', 'parent': '3', 'nivel': 2, 'tipo': 'analitica', 'class': 'patrimonio_liquido', 'nat': 'credora'},
        
        # RECEITAS
        {'codigo': '4', 'nome': 'RECEITAS', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'class': 'receita', 'nat': 'credora'},
        {'codigo': '4.1', 'nome': 'RECEITA OPERACIONAL', 'parent': '4', 'nivel': 2, 'tipo': 'sintetica', 'class': 'receita', 'nat': 'credora'},
        {'codigo': '4.1.01', 'nome': 'Receita de Vendas', 'parent': '4.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'receita', 'nat': 'credora'},
        {'codigo': '4.1.01.001', 'nome': 'Venda de Produtos', 'parent': '4.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'receita', 'nat': 'credora'},
        {'codigo': '4.1.01.002', 'nome': 'Prestação de Serviços', 'parent': '4.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'receita', 'nat': 'credora'},
        {'codigo': '4.2', 'nome': 'RECEITAS FINANCEIRAS', 'parent': '4', 'nivel': 2, 'tipo': 'sintetica', 'class': 'receita', 'nat': 'credora'},
        {'codigo': '4.2.01', 'nome': 'Rendimentos de Aplicações', 'parent': '4.2', 'nivel': 3, 'tipo': 'analitica', 'class': 'receita', 'nat': 'credora'},
        
        # DESPESAS
        {'codigo': '5', 'nome': 'DESPESAS', 'parent': None, 'nivel': 1, 'tipo': 'sintetica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1', 'nome': 'DESPESAS OPERACIONAIS', 'parent': '5', 'nivel': 2, 'tipo': 'sintetica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.01', 'nome': 'Despesas Administrativas', 'parent': '5.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.01.001', 'nome': 'Salários e Encargos', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.01.002', 'nome': 'Aluguel', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.01.003', 'nome': 'Energia Elétrica', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.01.004', 'nome': 'Água e Esgoto', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.01.005', 'nome': 'Telefone e Internet', 'parent': '5.1.01', 'nivel': 4, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.02', 'nome': 'Despesas com Vendas', 'parent': '5.1', 'nivel': 3, 'tipo': 'sintetica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.1.02.001', 'nome': 'Comissões sobre Vendas', 'parent': '5.1.02', 'nivel': 4, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.2', 'nome': 'DESPESAS FINANCEIRAS', 'parent': '5', 'nivel': 2, 'tipo': 'sintetica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.2.01', 'nome': 'Juros Pagos', 'parent': '5.2', 'nivel': 3, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
        {'codigo': '5.2.02', 'nome': 'Tarifas Bancárias', 'parent': '5.2', 'nivel': 3, 'tipo': 'analitica', 'class': 'despesa', 'nat': 'devedora'},
    ]
    
    # Mapa de códigos para IDs
    mapa = {}
    criadas = 0
    erros = []
    
    for i, conta in enumerate(contas, 1):
        try:
            # Resolver parent_id
            parent_id = None
            if conta['parent']:
                parent_id = mapa.get(conta['parent'])
                if not parent_id:
                    erros.append(f"❌ Conta {conta['codigo']}: parent {conta['parent']} não encontrado")
                    continue
            
            # Calcular ordem
            cursor.execute("""
                SELECT COALESCE(MAX(ordem), 0) + 1 as proxima
                FROM plano_contas
                WHERE empresa_id = %s AND versao_id = %s 
                  AND parent_id IS NOT DISTINCT FROM %s AND deleted_at IS NULL
            """, (EMPRESA_ID, VERSAO_ID, parent_id))
            
            ordem = cursor.fetchone()['proxima']
            
            # Inserir conta
            cursor.execute("""
                INSERT INTO plano_contas 
                    (empresa_id, versao_id, codigo, descricao, parent_id, nivel, ordem,
                     tipo_conta, classificacao, natureza, is_bloqueada, 
                     requer_centro_custo, permite_lancamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                EMPRESA_ID,
                VERSAO_ID,
                conta['codigo'],
                conta['nome'],
                parent_id,
                conta['nivel'],
                ordem,
                conta['tipo'],
                conta['class'],
                conta['nat'],
                False,
                False,
                conta['tipo'] == 'analitica'
            ))
            
            conta_id = cursor.fetchone()['id']
            mapa[conta['codigo']] = conta_id
            criadas += 1
            
            print(f"  ✅ [{i:02d}/{len(contas)}] {conta['codigo']} - {conta['nome']}")
            
        except Exception as e:
            erros.append(f"❌ Erro ao criar {conta['codigo']}: {str(e)}")
            print(f"  ❌ [{i:02d}/{len(contas)}] {conta['codigo']} - ERRO: {str(e)}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print()
    print("="*80)
    print(f"✅ CONCLUÍDO!")
    print(f"   📊 {criadas} contas criadas")
    if erros:
        print(f"   ⚠️ {len(erros)} erros:")
        for erro in erros[:5]:
            print(f"      {erro}")
    print("="*80)
    print()
    print("🔄 Recarregue a página do Plano de Contas (Ctrl+F5)")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

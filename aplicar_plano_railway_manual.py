"""
Script para aplicar plano de contas padrão via Railway - FORÇAR CRIAÇÃO
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Adicionar diretório ao path para importar funções
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("🚀 APLICAR PLANO DE CONTAS PADRÃO - RAILWAY")
print("="*80)
print()

DATABASE_URL = input("📋 Cole a DATABASE_URL do Railway: ").strip()

if not DATABASE_URL:
    print("❌ DATABASE_URL vazia!")
    exit(1)

print(f"\n🔗 Conectando: {DATABASE_URL[:30]}...")

try:
    # Conectar
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Conectado!\n")
    
    # Listar empresas
    cursor.execute("SELECT id, razao_social FROM empresas ORDER BY id")
    empresas = cursor.fetchall()
    
    print("📊 EMPRESAS DISPONÍVEIS:")
    for emp in empresas:
        print(f"   {emp['id']}. {emp['razao_social']}")
    
    print()
    empresa_id = int(input("📋 Digite o ID da empresa para aplicar o plano: "))
    
    # Verificar versões existentes
    cursor.execute("""
        SELECT v.id, v.nome_versao, v.is_ativa,
               COUNT(c.id) as total_contas
        FROM plano_contas_versao v
        LEFT JOIN plano_contas c ON c.versao_id = v.id AND c.deleted_at IS NULL
        WHERE v.empresa_id = %s
        GROUP BY v.id, v.nome_versao, v.is_ativa
        ORDER BY v.id
    """, (empresa_id,))
    
    versoes = cursor.fetchall()
    
    if versoes:
        print(f"\n📊 VERSÕES EXISTENTES (empresa {empresa_id}):")
        for v in versoes:
            status = "✅ ATIVA" if v['is_ativa'] else "⏸️ Inativa"
            contas_str = f"{v['total_contas']} contas" if v['total_contas'] > 0 else "⚠️ VAZIA"
            print(f"   [{v['id']}] {v['nome_versao']} - {status} - {contas_str}")
        
        # Verificar se há versões vazias
        versoes_vazias = [v for v in versoes if v['total_contas'] == 0]
        
        if versoes_vazias:
            print(f"\n⚠️ Encontradas {len(versoes_vazias)} versão(ões) VAZIA(S)!")
            resposta = input("   Deseja POPULAR uma versão vazia existente? (s/n): ").lower()
            
            if resposta == 's':
                versao_id = int(input("   Digite o ID da versão para popular: "))
                versao_selecionada = next((v for v in versoes_vazias if v['id'] == versao_id), None)
                
                if versao_selecionada:
                    print(f"\n🚀 Populando versão {versao_id} - {versao_selecionada['nome_versao']}...")
                    # Marcar que vamos popular versão existente
                    os.environ['POPULAR_VERSAO_ID'] = str(versao_id)
                else:
                    print(f"❌ Versão {versao_id} não encontrada ou não está vazia!")
                    exit(1)
            else:
                resposta = input("   Deseja criar uma NOVA versão? (s/n): ").lower()
                if resposta != 's':
                    print("⏭️ Operação cancelada")
                    exit(0)
        else:
            resposta = input("   Todas as versões têm contas. Criar uma NOVA versão? (s/n): ").lower()
            if resposta != 's':
                print("⏭️ Operação cancelada")
                exit(0)
    
    print(f"\n🚀 Aplicando plano de contas padrão para empresa {empresa_id}...")
    
    # Verificar se vamos popular versão existente ou criar nova
    versao_id_popular = os.environ.get('POPULAR_VERSAO_ID')
    
    if versao_id_popular:
        # Popular versão existente vazia
        versao_id = int(versao_id_popular)
        print(f"📝 Populando versão existente ID: {versao_id}")
        
        # Importar plano padrão
        from plano_contas_padrao import obter_plano_contas_padrao
        contas_padrao = obter_plano_contas_padrao()
        
        # Mapa para resolver parent_id
        mapa_codigos = {}
        contas_criadas = 0
        erros = []
        
        # Inserir contas em ordem
        for conta in contas_padrao:
            try:
                # Resolver parent_id
                parent_id = None
                if conta['parent_codigo']:
                    parent_id = mapa_codigos.get(conta['parent_codigo'])
                    if not parent_id:
                        erros.append(f"Conta {conta['codigo']}: parent {conta['parent_codigo']} não encontrado")
                        continue
                
                # Determinar tipo_conta
                tipo_conta = 'sintetica' if any(c['parent_codigo'] == conta['codigo'] for c in contas_padrao) else 'analitica'
                
                # Determinar natureza
                if conta['classificacao'] in ['ativo', 'despesa']:
                    natureza = 'devedora'
                elif conta['classificacao'] in ['passivo', 'patrimonio_liquido', 'receita']:
                    natureza = 'credora'
                else:
                    natureza = 'devedora'
                
                # Calcular ordem
                cursor.execute("""
                    SELECT COALESCE(MAX(ordem), 0) + 1 as proxima
                    FROM plano_contas
                    WHERE empresa_id = %s AND versao_id = %s 
                      AND parent_id IS NOT DISTINCT FROM %s AND deleted_at IS NULL
                """, (empresa_id, versao_id, parent_id))
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
                    empresa_id, versao_id, conta['codigo'], conta['nome'], parent_id,
                    conta['nivel'], ordem, tipo_conta, conta['classificacao'], natureza,
                    False, False, tipo_conta == 'analitica'
                ))
                
                conta_id = cursor.fetchone()['id']
                mapa_codigos[conta['codigo']] = conta_id
                contas_criadas += 1
                
                if contas_criadas % 10 == 0:
                    print(f"   ✅ {contas_criadas} contas inseridas...")
                
            except Exception as e:
                erros.append(f"Erro ao criar conta {conta['codigo']}: {str(e)}")
        
        conn.commit()
        
        resultado = {
            'success': True,
            'versao_id': versao_id,
            'contas_criadas': contas_criadas,
            'erros': erros
        }
        
    else:
        # Criar nova versão usando a função original
        from contabilidade_functions import importar_plano_padrao
        
        # Temporariamente definir conexão
        os.environ['USANDO_CONEXAO_MANUAL'] = 'true'
        os.environ['CONEXAO_MANUAL_URL'] = DATABASE_URL
        
        resultado = importar_plano_padrao(empresa_id, ano_fiscal=2026)
    
    if resultado.get('success'):
        print(f"\n✅ SUCESSO!")
        print(f"   📋 Versão ID: {resultado.get('versao_id')}")
        contas = resultado.get('contas_criadas') or resultado.get('contas_importadas', 0)
        print(f"   📊 Contas criadas: {contas}")
        if resultado.get('message'):
            print(f"   📝 Mensagem: {resultado.get('message')}")
        
        if resultado.get('erros') and len(resultado['erros']) > 0:
            print(f"\n⚠️ Erros encontrados ({len(resultado['erros'])}):")
            for erro in resultado['erros'][:5]:  # Mostrar só os 5 primeiros
                print(f"   • {erro}")
    else:
        print(f"\n❌ ERRO: {resultado.get('error')}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*80)
    print("✅ PROCESSO CONCLUÍDO")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 DIAGNÓSTICO - Bug de Arrays Limitados (PARTE 11)

PROBLEMA REPORTADO:
- Funcionários limitados a 1 item
- Equipe só puxa 1 membro
- Comissões limitadas a 1

Este script verifica onde o problema está acontecendo:
1. Verifica estrutura das tabelas
2. Testa salvamento de arrays no banco
3. Verifica leitura dos dados JSON
4. Identifica onde o truncamento ocorre
"""

import psycopg2
import json
import os
from psycopg2.extras import RealDictCursor

def conectar_banco():
    """Conecta ao banco PostgreSQL"""
    database_url = os.getenv('DATABASE_URL') or "postgresql://postgres:123@localhost:5432/sistema_financeiro"
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Conectado ao banco com sucesso")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        raise

def verificar_estrutura_tabelas(cursor):
    """Verifica estrutura das tabelas relevantes"""
    print("\n" + "="*80)
    print("📊 1. VERIFICAÇÃO DE ESTRUTURA DE TABELAS")
    print("="*80)
    
    tabelas = {
        'contratos': ['observacoes'],
        'sessoes': ['dados_json', 'equipe', 'responsaveis'],
        'funcionarios': []
    }
    
    for tabela, campos_json in tabelas.items():
        print(f"\n📋 Tabela: {tabela}")
        
        # Verificar colunas
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (tabela,))
        
        colunas = cursor.fetchall()
        
        for col in colunas:
            col_name = col['column_name']
            data_type = col['data_type']
            max_length = col['character_maximum_length']
            
            # Destacar campos JSON/TEXT
            if col_name in campos_json or 'json' in data_type.lower() or data_type == 'text':
                emoji = "🔍"
                tipo_info = f"{data_type}"
                if max_length:
                    tipo_info += f" (max: {max_length})"
                print(f"   {emoji} {col_name}: {tipo_info}")

def testar_arrays_contratos(cursor):
    """Testa armazenamento de comissões em contratos"""
    print("\n" + "="*80)
    print("📦 2. TESTE DE COMISSÕES EM CONTRATOS")
    print("="*80)
    
    # Buscar um contrato com comissões
    cursor.execute("""
        SELECT id, numero, observacoes
        FROM contratos
        WHERE observacoes IS NOT NULL
        ORDER BY id DESC
        LIMIT 5
    """)
    
    contratos = cursor.fetchall()
    
    print(f"\n📊 Total de contratos com observações: {len(contratos)}")
    
    for contrato in contratos:
        print(f"\n🔍 Contrato #{contrato['id']} (Número: {contrato['numero']})")
        
        if contrato['observacoes']:
            try:
                obs_data = json.loads(contrato['observacoes']) if isinstance(contrato['observacoes'], str) else contrato['observacoes']
                
                comissoes = obs_data.get('comissoes', [])
                
                print(f"   📊 Tipo de comissoes: {type(comissoes)}")
                print(f"   📊 Quantidade de comissões: {len(comissoes) if isinstance(comissoes, list) else 'N/A'}")
                
                if isinstance(comissoes, list) and comissoes:
                    print(f"   ✅ Comissões encontradas:")
                    for i, com in enumerate(comissoes, 1):
                        func_id = com.get('funcionario_id', 'N/A')
                        percentual = com.get('percentual', 'N/A')
                        print(f"      {i}. Funcionário ID {func_id}: {percentual}%")
                    
                    if len(comissoes) == 1:
                        print(f"   ⚠️  POSSÍVEL BUG: Apenas 1 comissão encontrada!")
                elif isinstance(comissoes, list):
                    print(f"   ℹ️  Array vazio (sem comissões)")
                else:
                    print(f"   ❌ comissões não é um array: {type(comissoes)}")
                    print(f"   📄 Valor: {comissoes}")
                
                # Mostrar tamanho do JSON
                obs_str = json.dumps(obs_data)
                print(f"   📏 Tamanho total do JSON: {len(obs_str)} bytes")
                
            except Exception as e:
                print(f"   ❌ Erro ao parsear observacoes: {e}")
                print(f"   📄 Conteúdo bruto (primeiros 200 chars): {str(contrato['observacoes'])[:200]}")

def testar_arrays_sessoes(cursor):
    """Testa armazenamento de equipe em sessões"""
    print("\n" + "="*80)
    print("👥 3. TESTE DE EQUIPE EM SESSÕES")
    print("="*80)
    
    # Verificar se há coluna JSONB separada ou se está em dados_json
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'sessoes'
        AND column_name IN ('equipe', 'dados_json')
    """)
    
    colunas_disponiveis = [row['column_name'] for row in cursor.fetchall()]
    print(f"\n📊 Colunas JSON disponíveis em sessoes: {colunas_disponiveis}")
    
    # Buscar sessões com equipe
    if 'dados_json' in colunas_disponiveis:
        cursor.execute("""
            SELECT id, cliente_id, data, dados_json
            FROM sessoes
            WHERE dados_json IS NOT NULL
            ORDER BY id DESC
            LIMIT 5
        """)
    elif 'equipe' in colunas_disponiveis:
        cursor.execute("""
            SELECT id, cliente_id, data, equipe
            FROM sessoes
            WHERE equipe IS NOT NULL
            ORDER BY id DESC
            LIMIT 5
        """)
    else:
        print("❌ Nenhuma coluna JSON encontrada em sessoes!")
        return
    
    sessoes = cursor.fetchall()
    
    print(f"\n📊 Total de sessões com dados JSON: {len(sessoes)}")
    
    for sessao in sessoes:
        print(f"\n🔍 Sessão #{sessao['id']} (Cliente: {sessao['cliente_id']})")
        
        # Extrair equipe do dados_json ou coluna direta
        equipe = []
        if 'dados_json' in sessao and sessao['dados_json']:
            try:
                dados = json.loads(sessao['dados_json']) if isinstance(sessao['dados_json'], str) else sessao['dados_json']
                equipe = dados.get('equipe', [])
            except Exception as e:
                print(f"   ❌ Erro ao parsear dados_json: {e}")
        elif 'equipe' in sessao and sessao['equipe']:
            try:
                equipe = json.loads(sessao['equipe']) if isinstance(sessao['equipe'], str) else sessao['equipe']
            except Exception as e:
                print(f"   ❌ Erro ao parsear equipe: {e}")
        
        print(f"   📊 Tipo de equipe: {type(equipe)}")
        print(f"   📊 Quantidade de membros: {len(equipe) if isinstance(equipe, list) else 'N/A'}")
        
        if isinstance(equipe, list) and equipe:
            print(f"   ✅ Membros da equipe:")
            for i, membro in enumerate(equipe, 1):
                if isinstance(membro, dict):
                    nome = membro.get('nome', membro.get('funcionario_id', 'N/A'))
                    funcao = membro.get('funcao', 'N/A')
                    print(f"      {i}. {nome} - {funcao}")
                else:
                    print(f"      {i}. {membro}")
            
            if len(equipe) == 1:
                print(f"   ⚠️  POSSÍVEL BUG: Apenas 1 membro na equipe!")
        elif isinstance(equipe, list):
            print(f"   ℹ️  Array vazio (sem equipe)")
        else:
            print(f"   ❌ equipe não é um array: {type(equipe)}")

def testar_funcionarios(cursor):
    """Verifica se há alguma limitação de funcionários"""
    print("\n" + "="*80)
    print("👤 4. VERIFICAÇÃO DE FUNCIONÁRIOS")
    print("="*80)
    
    cursor.execute("SELECT COUNT(*) as total FROM funcionarios")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as ativos FROM funcionarios WHERE ativo = TRUE")
    ativos = cursor.fetchone()['ativos']
    
    print(f"\n📊 Total de funcionários: {total}")
    print(f"✅ Funcionários ativos: {ativos}")
    
    if total < 2:
        print(f"⚠️  Poucos funcionários cadastrados para testar bug!")
    
    # Listar primeiros funcionários
    cursor.execute("""
        SELECT id, nome, ativo
        FROM funcionarios
        ORDER BY id
        LIMIT 10
    """)
    
    funcionarios = cursor.fetchall()
    print(f"\n📋 Primeiros 10 funcionários:")
    for func in funcionarios:
        status = "✅" if func['ativo'] else "❌"
        print(f"   {status} ID {func['id']}: {func['nome']}")

def criar_teste_integracao(cursor, conn):
    """Cria um contrato de teste com múltiplas comissões para verificar o bug"""
    print("\n" + "="*80)
    print("🧪 5. TESTE DE INTEGRAÇÃO - CRIAR CONTRATO COM 3 COMISSÕES")
    print("="*80)
    
    # Buscar empresa_id e cliente_id válidos
    cursor.execute("SELECT id FROM empresas LIMIT 1")
    empresa = cursor.fetchone()
    if not empresa:
        print("❌ Nenhuma empresa encontrada!")
        return
    
    empresa_id = empresa['id']
    
    cursor.execute("SELECT id FROM clientes WHERE empresa_id = %s LIMIT 1", (empresa_id,))
    cliente = cursor.fetchone()
    if not cliente:
        print("❌ Nenhum cliente encontrado!")
        return
    
    cliente_id = cliente['id']
    
    # Buscar 3 funcionários para as comissões
    cursor.execute("""
        SELECT id, nome
        FROM funcionarios
        WHERE empresa_id = %s AND ativo = TRUE
        LIMIT 3
    """, (empresa_id,))
    
    funcionarios = cursor.fetchall()
    
    if len(funcionarios) < 2:
        print(f"⚠️  Apenas {len(funcionarios)} funcionário(s) disponível(is). Necessário pelo menos 2 para testar!")
        return
    
    print(f"\n📋 Funcionários selecionados para teste:")
    for func in funcionarios:
        print(f"   - ID {func['id']}: {func['nome']}")
    
    # Criar comissões de teste
    comissoes_teste = [
        {'funcionario_id': funcionarios[0]['id'], 'percentual': 5.0},
        {'funcionario_id': funcionarios[1]['id'], 'percentual': 3.0},
    ]
    
    if len(funcionarios) >= 3:
        comissoes_teste.append({'funcionario_id': funcionarios[2]['id'], 'percentual': 2.0})
    
    # Preparar observações com as comissões
    observacoes_dict = {
        'tipo': 'Mensal',
        'nome': 'TESTE BUG - Contrato com múltiplas comissões',
        'valor_mensal': 5000.00,
        'quantidade_meses': 6,
        'comissoes': comissoes_teste
    }
    
    observacoes_json = json.dumps(observacoes_dict)
    
    print(f"\n💾 Criando contrato de teste...")
    print(f"   📊 Comissões a salvar: {len(comissoes_teste)}")
    print(f"   📏 Tamanho do JSON: {len(observacoes_json)} bytes")
    
    try:
        cursor.execute("""
            INSERT INTO contratos (
                numero, cliente_id, descricao, valor, 
                data_inicio, status, observacoes, empresa_id
            )
            VALUES (%s, %s, %s, %s, CURRENT_DATE, 'ativo', %s, %s)
            RETURNING id
        """, (
            'TESTE-BUG-001',
            cliente_id,
            'Contrato de teste para bug de comissões limitadas',
            30000.00,
            observacoes_json,
            empresa_id
        ))
        
        contrato_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"   ✅ Contrato criado com ID: {contrato_id}")
        
        # Verificar se foi salvo corretamente
        print(f"\n🔍 Verificando contrato recém-criado...")
        cursor.execute("""
            SELECT id, numero, observacoes
            FROM contratos
            WHERE id = %s
        """, (contrato_id,))
        
        contrato = cursor.fetchone()
        
        if contrato['observacoes']:
            obs_recuperadas = json.loads(contrato['observacoes']) if isinstance(contrato['observacoes'], str) else contrato['observacoes']
            comissoes_recuperadas = obs_recuperadas.get('comissoes', [])
            
            print(f"   📊 Comissões recuperadas: {len(comissoes_recuperadas)}")
            
            if len(comissoes_recuperadas) == len(comissoes_teste):
                print(f"   ✅ SUCESSO: Todas as {len(comissoes_teste)} comissões foram salvas e recuperadas!")
            else:
                print(f"   ❌ BUG CONFIRMADO: Salvamos {len(comissoes_teste)} mas recuperamos apenas {len(comissoes_recuperadas)}!")
                print(f"   📄 Comissões recuperadas: {comissoes_recuperadas}")
        
        return contrato_id
        
    except Exception as e:
        print(f"   ❌ Erro ao criar contrato de teste: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return None

def gerar_relatorio_final():
    """Gera relatório final com recomendações"""
    print("\n" + "="*80)
    print("📝 RELATÓRIO FINAL E RECOMENDAÇÕES")
    print("="*80)
    
    print("""
🔍 RESUMO DO DIAGNÓSTICO:

O bug de "arrays limitados a 1 item" pode ocorrer por:

1. ❌ Campo TEXT/JSON truncado no banco
   └─ Solução: Verificar se campo é JSONB (ilimitado)

2. ❌ Erro no parsing JSON frontend/backend
   └─ Solução: Adicionar logs para rastrear onde o array é reduzido

3. ❌ Erro no código que processa os arrays
   └─ Solução: Verificar loops forEach/map

4. ❌ Limitação de query SQL (LIMIT 1, FIRST, etc)
   └─ Solução: Revisar queries que buscam dados relacionados

📋 PRÓXIMOS PASSOS:

1. Executar este diagnóstico completo
2. Identificar onde exatamente o truncamento ocorre
3. Aplicar correção específica no código identificado
4. Criar migration se necessário (ex: mudar TEXT → JSONB)
5. Testar com múltiplos registros

💡 ATENÇÃO: Se o teste de integração (seção 5) falhou, o problema
   está no BANCO DE DADOS (estrutara ou configuração).
   
   Se o teste passou mas o bug persiste na interface, o problema
   está no FRONTEND ou no BACKEND (código de processamento).
""")

def executar_diagnostico():
    """Executa diagnóstico completo"""
    try:
        conn = conectar_banco()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Verificar estrutura
        verificar_estrutura_tabelas(cursor)
        
        # 2. Testar comissões em contratos
        testar_arrays_contratos(cursor)
        
        # 3. Testar equipe em sessões
        testar_arrays_sessoes(cursor)
        
        # 4. Verificar funcionários
        testar_funcionarios(cursor)
        
        # 5. Teste de integração
        contrato_teste_id = criar_teste_integracao(cursor, conn)
        
        # 6. Relatório final
        gerar_relatorio_final()
        
        print("\n" + "="*80)
        print("✅ DIAGNÓSTICO COMPLETO")
        print("="*80)
        
        if contrato_teste_id:
            print(f"\n💡 Contrato de teste criado com ID {contrato_teste_id}")
            print(f"   Use este ID para testar a interface e verificar se o bug persiste")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    executar_diagnostico()

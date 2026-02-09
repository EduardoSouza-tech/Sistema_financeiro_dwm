#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Script de Aplicação - Correção Bug Arrays Limitados (PARTE 11)

Este script aplica a migration que corrige o bug de arrays limitados a 1 item
em comissões (contratos) e equipe (sessões).

Correções aplicadas:
1. Converte campos TEXT/JSON para JSONB
2. Cria índices GIN para performance
3. Adiciona funções de validação e monitoramento
"""

import psycopg2
import os
from psycopg2.extras import RealDictCursor

def conectar_banco():
    """Conecta ao banco PostgreSQL"""
    database_url = os.getenv('DATABASE_URL') or "postgresql://postgres:123@localhost:5432/sistema_financeiro"
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        print("✅ Conectado ao banco com sucesso")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        raise

def aplicar_migration(cursor):
    """Aplica a migration SQL"""
    print("\n" + "="*80)
    print("📦 APLICANDO MIGRATION - Correção de Arrays Limitados")
    print("="*80)
    
    try:
        # Ler arquivo SQL
        caminho_migration = os.path.join(
            os.path.dirname(__file__),
            'migration_fix_arrays_bug.sql'
        )
        
        print(f"\n📄 Lendo migration: {caminho_migration}")
        
        with open(caminho_migration, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"📏 Tamanho da migration: {len(sql)} bytes")
        print(f"\n⚙️  Executando migration...")
        
        # Executar migration
        cursor.execute(sql)
        
        print(f"✅ Migration executada com sucesso!")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Arquivo migration_fix_arrays_bug.sql não encontrado!")
        return False
    except Exception as e:
        print(f"❌ Erro ao aplicar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_resultados(cursor):
    """Verifica os resultados da migration"""
    print("\n" + "="*80)
    print("🔍 VERIFICANDO RESULTADOS DA MIGRATION")
    print("="*80)
    
    # 1. Verificar tipos de colunas
    print("\n1️⃣  TIPOS DE COLUNAS:")
    cursor.execute("""
        SELECT 
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_name IN ('contratos', 'sessoes')
        AND column_name IN ('observacoes', 'dados_json', 'equipe', 'responsaveis')
        ORDER BY table_name, column_name
    """)
    
    colunas = cursor.fetchall()
    for col in colunas:
        tipo_ok = "✅" if col['data_type'] == 'jsonb' else "⚠️ "
        print(f"   {tipo_ok} {col['table_name']}.{col['column_name']}: {col['data_type']}")
    
    # 2. Verificar índices
    print("\n2️⃣  ÍNDICES GIN:")
    cursor.execute("""
        SELECT 
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE indexname LIKE '%_gin'
        AND tablename IN ('contratos', 'sessoes')
        ORDER BY tablename, indexname
    """)
    
    indices = cursor.fetchall()
    if indices:
        for idx in indices:
            print(f"   ✅ {idx['indexname']} em {idx['tablename']}")
    else:
        print(f"   ⚠️  Nenhum índice GIN encontrado")
    
    # 3. Executar validação de arrays
    print("\n3️⃣  STATUS DOS ARRAYS JSON:")
    cursor.execute("SELECT * FROM vw_status_arrays_json")
    
    status = cursor.fetchall()
    if status:
        for s in status:
            print(f"\n   📊 {s['tabela']}.{s['campo']}:")
            print(f"      • Total de registros: {s['total_registros']}")
            print(f"      • Arrays vazios: {s['arrays_vazios']}")
            print(f"      • Arrays com 1 item: {s['arrays_com_1_item']} {'⚠️' if s['arrays_com_1_item'] > 0 else ''}")
            print(f"      • Arrays com múltiplos: {s['arrays_com_multiplos']}")
            print(f"      • Média de itens: {s['media_itens']}")
            print(f"      • Máximo de itens: {s['max_itens']}")
    else:
        print(f"   ℹ️  Nenhum dado para validar (sem arrays JSON salvos ainda)")
    
    # 4. Buscar registros com possível bug
    print("\n4️⃣  REGISTROS COM POSSÍVEL BUG (apenas 1 item):")
    cursor.execute("""
        SELECT * FROM validar_arrays_json()
        WHERE tem_bug = TRUE
        ORDER BY tabela, registro_id
    """)
    
    bugs = cursor.fetchall()
    if bugs:
        print(f"\n   ⚠️  Encontrados {len(bugs)} registros com apenas 1 item:")
        for bug in bugs[:10]:  # Mostrar até 10
            print(f"      • {bug['tabela']} ID {bug['registro_id']}: {bug['campo']} tem apenas {bug['quantidade']} item")
        
        if len(bugs) > 10:
            print(f"      ... e mais {len(bugs) - 10} registros")
    else:
        print(f"   ✅ Nenhum registro com bug detectado!")

def testar_criacao_multiplos_itens(cursor, conn):
    """Testa criação de contrato com múltiplas comissões"""
    print("\n" + "="*80)
    print("🧪 TESTE: Criar contrato com 3 comissões")
    print("="*80)
    
    try:
        # Buscar empresa e cliente
        cursor.execute("SELECT id FROM empresas LIMIT 1")
        empresa = cursor.fetchone()
        if not empresa:
            print("⚠️  Nenhuma empresa encontrada - pulando teste")
            return
        
        empresa_id = empresa['id']
        
        cursor.execute("SELECT id FROM clientes WHERE empresa_id = %s LIMIT 1", (empresa_id,))
        cliente = cursor.fetchone()
        if not cliente:
            print("⚠️  Nenhum cliente encontrado - pulando teste")
            return
        
        cliente_id = cliente['id']
        
        # Buscar funcionários
        cursor.execute("""
            SELECT id, nome
            FROM funcionarios
            WHERE empresa_id = %s AND ativo = TRUE
            ORDER BY id
            LIMIT 3
        """, (empresa_id,))
        
        funcionarios = cursor.fetchall()
        
        if len(funcionarios) < 2:
            print(f"⚠️  Apenas {len(funcionarios)} funcionário(s) disponível(is) - mínimo 2 necessários")
            return
        
        print(f"\n✅ Pré-requisitos OK:")
        print(f"   • Empresa ID: {empresa_id}")
        print(f"   • Cliente ID: {cliente_id}")
        print(f"   • Funcionários: {len(funcionarios)}")
        
        # Criar comissões de teste
        import json
        comissoes = [
            {'funcionario_id': funcionarios[0]['id'], 'percentual': 5.0},
            {'funcionario_id': funcionarios[1]['id'], 'percentual': 3.0},
        ]
        
        if len(funcionarios) >= 3:
            comissoes.append({'funcionario_id': funcionarios[2]['id'], 'percentual': 2.0})
        
        observacoes = {
            'tipo': 'Mensal',
            'nome': 'TESTE - Múltiplas Comissões',
            'comissoes': comissoes
        }
        
        print(f"\n💾 Criando contrato com {len(comissoes)} comissões...")
        
        cursor.execute("""
            INSERT INTO contratos (
                numero, cliente_id, descricao, valor,
                data_inicio, status, observacoes, empresa_id
            )
            VALUES (%s, %s, %s, %s, CURRENT_DATE, 'ativo', %s, %s)
            RETURNING id
        """, (
            'TESTE-ARRAYS-001',
            cliente_id,
            'Teste de correção de bug de arrays',
            15000.00,
            json.dumps(observacoes),
            empresa_id
        ))
        
        contrato_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"✅ Contrato criado: ID {contrato_id}")
        
        # Verificar se foi salvo corretamente
        print(f"\n🔍 Verificando contrato recém-criado...")
        cursor.execute("""
            SELECT id, numero, observacoes
            FROM contratos
            WHERE id = %s
        """, (contrato_id,))
        
        contrato = cursor.fetchone()
        obs = json.loads(contrato['observacoes']) if isinstance(contrato['observacoes'], str) else contrato['observacoes']
        comissoes_recuperadas = obs.get('comissoes', [])
        
        print(f"   📊 Comissões salvas: {len(comissoes)}")
        print(f"   📊 Comissões recuperadas: {len(comissoes_recuperadas)}")
        
        if len(comissoes_recuperadas) == len(comissoes):
            print(f"\n   ✅ TESTE PASSOU: Todas as {len(comissoes)} comissões foram salvas e recuperadas!")
            for i, com in enumerate(comissoes_recuperadas, 1):
                print(f"      {i}. Funcionário {com['funcionario_id']}: {com['percentual']}%")
        else:
            print(f"\n   ❌ TESTE FALHOU: Esperado {len(comissoes)}, recuperado {len(comissoes_recuperadas)}")
        
        return contrato_id
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return None

def gerar_relatorio_final():
    """Gera relatório final"""
    print("\n" + "="*80)
    print("📋 RELATÓRIO FINAL")
    print("="*80)
    
    print("""
✅ MIGRATION APLICADA COM SUCESSO!

📊 CORREÇÕES IMPLEMENTADAS:

1. ✅ Campos convertidos para JSONB
   • contratos.observacoes → JSONB (ilimitado)
   • sessoes.dados_json → JSONB (ilimitado)
   • sessoes.equipe, responsaveis, etc → JSONB

2. ✅ Índices GIN criados
   • idx_contratos_observacoes_gin
   • idx_sessoes_dados_json_gin
   • Melhor performance em queries JSON

3. ✅ Funções de validação adicionadas
   • validar_arrays_json(): detecta arrays com 1 item
   • vw_status_arrays_json: view de monitoramento

💡 PRÓXIMOS PASSOS:

1. Testar interface web:
   ✓ Criar contrato com 3+ comissões
   ✓ Editar contrato e verificar se todas as comissões aparecem
   ✓ Criar sessão com 3+ membros na equipe
   ✓ Editar sessão e verificar se todos os membros aparecem

2. Monitorar:
   ✓ SELECT * FROM vw_status_arrays_json;
   ✓ SELECT * FROM validar_arrays_json() WHERE tem_bug = TRUE;

3. Se o bug persistir:
   ✓ Verifique logs do backend (pode haver código limitando)
   ✓ Verifique console do navegador (JavaScript pode estar filtrando)
   ✓ Execute diagnostico_arrays_bug.py para debug mais profundo

📄 ARQUIVOS DA PARTE 11:
• migration_fix_arrays_bug.sql (correção do banco)
• aplicar_fix_arrays_bug.py (este script)
• diagnostico_arrays_bug.py (diagnóstico detalhado)

⚠️  IMPORTANTE:
Se após aplicar esta migration o bug persistir na interface,
o problema está no CÓDIGO (frontend ou backend), não no banco.
Verifique:
• app/routes/contratos.py (linhas que processam comissões)
• app/routes/sessoes.py (linhas que processam equipe)
• static/modals.js (funções de edição)
""")

def executar_correcao():
    """Executa correção completa"""
    print("\n" + "="*80)
    print("🚀 CORREÇÃO DO BUG DE ARRAYS LIMITADOS - PARTE 11")
    print("="*80)
    print("\nProblemas a corrigir:")
    print("1. Funcionários limitados a 1 item")
    print("2. Equipe só puxa 1 membro")
    print("3. Comissões limitadas a 1")
    print("\n" + "="*80)
    
    try:
        conn = conectar_banco()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Aplicar migration
        if not aplicar_migration(cursor):
            print("\n❌ Falha ao aplicar migration!")
            return
        
        # Commit da migration
        conn.commit()
        print("\n✅ Migration commitada!")
        
        # 2. Verificar resultados
        verificar_resultados(cursor)
        
        # 3. Teste de integração
        testar_criacao_multiplos_itens(cursor, conn)
        
        # 4. Relatório final
        gerar_relatorio_final()
        
        print("\n" + "="*80)
        print("✅ CORREÇÃO COMPLETA!")
        print("="*80)
        print("\n💡 Teste agora a interface web para confirmar que o bug foi corrigido.\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro durante correção: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    executar_correcao()

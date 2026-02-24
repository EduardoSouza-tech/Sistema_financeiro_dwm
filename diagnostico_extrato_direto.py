#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar dados do extrato no banco - Direto com psycopg2"""

import os
import psycopg2
from psycopg2 import extras

# Carregar DATABASE_URL do ambiente ou usar valor padrão Railway
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL não configurada no ambiente")
    print("💡 Para rodar localmente, defina: $env:DATABASE_URL='postgresql://...'")
    print("💡 Ou vou tentar conectar usando credenciais Railway...")
    exit(1)

print(f"🔗 Conectando ao banco de dados...")
print(f"   URL: {DATABASE_URL[:30]}...")

try:
    # Conectar com SSL requerido (Railway)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    print("✅ Conectado com sucesso!\n")
    
    # Verificar últimas transações do extrato
    print("="*120)
    print("📊 ÚLTIMAS 10 TRANSAÇÕES DO EXTRATO:")
    print("="*120)
    
    cursor.execute('''
        SELECT id, data, descricao, valor, tipo, saldo, conciliado, created_at
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
        ORDER BY data DESC, id DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    if rows:
        print(f"{'ID':<8} {'Data':<12} {'Valor':>15} {'Tipo':<10} {'Saldo':>15} {'Descrição':<40}")
        print("-"*120)
        for row in rows:
            print(f"{row['id']:<8} {str(row['data']):<12} {row['valor']:>15.2f} {row['tipo']:<10} {row['saldo']:>15.2f} {row['descricao'][:40]:<40}")
    else:
        print("   ⚠️ Nenhuma transação encontrada")
    
    # Verificar total de transações
    cursor.execute('''
        SELECT COUNT(*) as total, MIN(data) as data_inicio, MAX(data) as data_fim
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
    ''')
    resumo = cursor.fetchone()
    
    print(f"\n{'='*120}")
    print("📋 RESUMO:")
    print(f"   Total de transações: {resumo['total']}")
    print(f"   Período: {resumo['data_inicio']} até {resumo['data_fim']}")
    
    # Verificar saldo inicial e final
    cursor.execute('''
        SELECT data, saldo
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
        ORDER BY data ASC, id ASC
        LIMIT 1
    ''')
    primeira = cursor.fetchone()
    if primeira:
        print(f"\n💰 PRIMEIRA transação:")
        print(f"   Data: {primeira['data']}")
        print(f"   Saldo: R$ {primeira['saldo']:,.2f}")
    
    cursor.execute('''
        SELECT data, saldo
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
        ORDER BY data DESC, id DESC
        LIMIT 1
    ''')
    ultima = cursor.fetchone()
    if ultima:
        print(f"\n💰 ÚLTIMA transação (SALDO ATUAL DO EXTRATO):")
        print(f"   Data: {ultima['data']}")
        print(f"   Saldo: R$ {ultima['saldo']:,.2f}")
    
    # Verificar duplicatas por FITID
    cursor.execute('''
        SELECT fitid, COUNT(*) as qtd, 
               STRING_AGG(CAST(id AS TEXT), ', ') as ids
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2' 
          AND fitid IS NOT NULL
        GROUP BY fitid
        HAVING COUNT(*) > 1
        ORDER BY qtd DESC
        LIMIT 10
    ''')
    duplicados_fitid = cursor.fetchall()
    
    if duplicados_fitid:
        print(f"\n{'='*120}")
        print(f"⚠️ TRANSAÇÕES DUPLICADAS POR FITID (ID único do banco):")
        print(f"   Total: {len(duplicados_fitid)} FITIDs duplicados")
        print("-"*120)
        for dup in duplicados_fitid:
            print(f"   FITID: {dup['fitid']}")
            print(f"   Quantidade: {dup['qtd']} vezes")
            print(f"   IDs: {dup['ids']}")
            print()
    else:
        print(f"\n✅ Nenhuma transação duplicada por FITID")
    
    # Verificar duplicatas por conteúdo (data + valor + descrição)
    cursor.execute('''
        SELECT data, valor, descricao, COUNT(*) as qtd,
               STRING_AGG(CAST(id AS TEXT), ', ') as ids
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
        GROUP BY data, valor, descricao
        HAVING COUNT(*) > 1
        ORDER BY qtd DESC, data DESC
        LIMIT 10
    ''')
    duplicados_conteudo = cursor.fetchall()
    
    if duplicados_conteudo:
        print(f"\n{'='*120}")
        print(f"⚠️ TRANSAÇÕES DUPLICADAS POR CONTEÚDO (data+valor+descrição):")
        print(f"   Total: {len(duplicados_conteudo)} grupos de duplicatas")
        print("-"*120)
        for dup in duplicados_conteudo:
            print(f"   Data: {dup['data']} | Valor: R$ {dup['valor']:,.2f}")
            print(f"   Descrição: {dup['descricao'][:60]}")
            print(f"   Quantidade: {dup['qtd']} vezes")
            print(f"   IDs: {dup['ids']}")
            print()
    else:
        print(f"\n✅ Nenhuma transação duplicada por conteúdo")
    
    # Verificar múltiplas importações
    cursor.execute('''
        SELECT importacao_id, COUNT(*) as qtd, 
               MIN(data) as data_inicio, MAX(data) as data_fim
        FROM transacoes_extrato
        WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
        GROUP BY importacao_id
        ORDER BY importacao_id DESC
    ''')
    importacoes = cursor.fetchall()
    
    print(f"\n{'='*120}")
    print(f"📦 IMPORTAÇÕES:")
    if len(importacoes) > 1:
        print(f"   ⚠️ MÚLTIPLAS IMPORTAÇÕES DETECTADAS: {len(importacoes)}")
        print("-"*120)
        for imp in importacoes:
            print(f"   ID: {imp['importacao_id']} | Transações: {imp['qtd']} | Período: {imp['data_inicio']} até {imp['data_fim']}")
    else:
        print(f"   ✅ Apenas uma importação no sistema")
        if importacoes:
            imp = importacoes[0]
            print(f"   ID: {imp['importacao_id']} | Transações: {imp['qtd']} | Período: {imp['data_inicio']} até {imp['data_fim']}")
    
    # Verificar conta bancária cadastrada
    cursor.execute('''
        SELECT nome, saldo_inicial, data_inicio, ativa
        FROM contas_bancariasempresa
        WHERE empresa_id = 20 AND nome = 'SICREDI COOPERATIVA - 0258/78895-2'
    ''')
    conta = cursor.fetchone()
    
    if conta:
        print(f"\n{'='*120}")
        print(f"🏦 CONTA CADASTRADA:")
        print(f"   Nome: {conta['nome']}")
        print(f"   Saldo Inicial: R$ {conta['saldo_inicial']:,.2f}")
        print(f"   Data Início: {conta['data_inicio']}")
        print(f"   Ativa: {'✅ Sim' if conta['ativa'] else '❌ Não'}")
    
    print(f"\n{'='*120}")
    print("✅ Diagnóstico concluído!")
    print(f"{'='*120}\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Erro ao conectar/consultar banco de dados:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()

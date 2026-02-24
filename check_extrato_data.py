#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar dados do extrato no banco"""

from database_postgresql import get_database

db = get_database()
cursor = db.cursor()

# Verificar últimas transações do extrato
cursor.execute('''
    SELECT id, data, descricao, valor, tipo, saldo, conciliado, created_at
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
    ORDER BY data DESC, id DESC
    LIMIT 10
''')

print('\n📊 ÚLTIMAS 10 TRANSAÇÕES DO EXTRATO:')
print('='*140)
print(f"{'ID':<8} {'Data':<12} {'Valor':>15} {'Tipo':<10} {'Saldo Após':>15} {'Descrição':<40} {'Criado em'}")
print('='*140)
for row in cursor.fetchall():
    row_id, data, desc, valor, tipo, saldo, conciliado, created = row
    print(f"{row_id:<8} {str(data):<12} {valor:>15.2f} {tipo:<10} {saldo:>15.2f} {desc[:40]:<40} {str(created)}")

# Verificar total de transações
cursor.execute('''
    SELECT COUNT(*), MIN(data), MAX(data)
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
''')
total, min_data, max_data = cursor.fetchone()
print(f'\n📋 Total de transações: {total}')
print(f'📅 Período: {min_data} até {max_data}')

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
    print(f'\n💰 PRIMEIRA transação: {primeira[0]} - Saldo: R$ {primeira[1]:,.2f}')

cursor.execute('''
    SELECT data, saldo
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
    ORDER BY data DESC, id DESC
    LIMIT 1
''')
ultima = cursor.fetchone()
if ultima:
    print(f'💰 ÚLTIMA transação: {ultima[0]} - Saldo: R$ {ultima[1]:,.2f}')

# Verificar se há duplicados (fitid duplicado)
cursor.execute('''
    SELECT fitid, COUNT(*) as qtd
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2' AND fitid IS NOT NULL
    GROUP BY fitid
    HAVING COUNT(*) > 1
    ORDER BY qtd DESC
    LIMIT 10
''')
duplicados = cursor.fetchall()
if duplicados:
    print(f'\n⚠️ TRANSAÇÕES DUPLICADAS (FITID):')
    for fitid, qtd in duplicados:
        print(f'   {fitid}: {qtd} vezes')
else:
    print(f'\n✅ Nenhuma transação duplicada (FITID único)')

# Verificar múltiplas importações
cursor.execute('''
    SELECT importacao_id, COUNT(*) as qtd, MIN(data) as data_inicio, MAX(data) as data_fim
    FROM transacoes_extrato
    WHERE empresa_id = 20 AND conta_bancaria = 'SICREDI COOPERATIVA - 0258/78895-2'
    GROUP BY importacao_id
    ORDER BY importacao_id DESC
''')
importacoes = cursor.fetchall()
if len(importacoes) > 1:
    print(f'\n📦 MÚLTIPLAS IMPORTAÇÕES DETECTADAS:')
    for imp_id, qtd, data_i, data_f in importacoes:
        print(f'   Importação {imp_id}: {qtd} transações ({data_i} até {data_f})')
else:
    print(f'\n✅ Apenas uma importação no sistema')

# Verificar conta bancária cadastrada
cursor.execute('''
    SELECT nome, saldo_inicial, data_inicio, ativa
    FROM contas_bancariasempresa
    WHERE empresa_id = 20 AND nome = 'SICREDI COOPERATIVA - 0258/78895-2'
''')
conta = cursor.fetchone()
if conta:
    print(f'\n🏦 CONTA CADASTRADA:')
    print(f'   Nome: {conta[0]}')
    print(f'   Saldo Inicial: R$ {conta[1]:,.2f}')
    print(f'   Data Início: {conta[2]}')
    print(f'   Ativa: {conta[3]}')

cursor.close()

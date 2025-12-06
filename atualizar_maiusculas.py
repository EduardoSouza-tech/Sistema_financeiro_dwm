#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para converter todos os dados de clientes e fornecedores para MAIÚSCULAS
"""

import sqlite3

def atualizar_maiusculas():
    conn = sqlite3.connect('sistema_financeiro.db')
    cursor = conn.cursor()
    
    print("Atualizando CLIENTES para MAIÚSCULAS...")
    
    # Atualizar clientes
    cursor.execute("""
        UPDATE clientes 
        SET 
            nome = UPPER(nome),
            razao_social = UPPER(razao_social),
            nome_fantasia = UPPER(nome_fantasia),
            rua = UPPER(rua),
            complemento = UPPER(complemento),
            bairro = UPPER(bairro),
            cidade = UPPER(cidade),
            ie = UPPER(ie),
            im = UPPER(im)
    """)
    
    clientes_atualizados = cursor.rowcount
    print(f"✓ {clientes_atualizados} clientes atualizados")
    
    print("\nAtualizando FORNECEDORES para MAIÚSCULAS...")
    
    # Atualizar fornecedores
    cursor.execute("""
        UPDATE fornecedores 
        SET 
            nome = UPPER(nome),
            razao_social = UPPER(razao_social),
            nome_fantasia = UPPER(nome_fantasia),
            rua = UPPER(rua),
            complemento = UPPER(complemento),
            bairro = UPPER(bairro),
            cidade = UPPER(cidade),
            ie = UPPER(ie),
            im = UPPER(im)
    """)
    
    fornecedores_atualizados = cursor.rowcount
    print(f"✓ {fornecedores_atualizados} fornecedores atualizados")
    
    print("\nAtualizando CATEGORIAS para MAIÚSCULAS...")
    
    # Atualizar categorias
    cursor.execute("""
        UPDATE categorias 
        SET nome = UPPER(nome)
    """)
    
    categorias_atualizadas = cursor.rowcount
    print(f"✓ {categorias_atualizadas} categorias atualizadas")
    
    print("\nAtualizando CONTAS BANCÁRIAS para MAIÚSCULAS...")
    
    # Atualizar contas bancárias
    cursor.execute("""
        UPDATE contas_bancarias 
        SET banco = UPPER(banco)
    """)
    
    contas_atualizadas = cursor.rowcount
    print(f"✓ {contas_atualizadas} contas bancárias atualizadas")
    
    print("\nAtualizando LANÇAMENTOS para MAIÚSCULAS...")
    
    # Atualizar lançamentos
    cursor.execute("""
        UPDATE lancamentos 
        SET 
            descricao = UPPER(descricao),
            observacoes = UPPER(observacoes),
            pessoa = UPPER(pessoa),
            categoria = UPPER(categoria),
            subcategoria = UPPER(subcategoria)
    """)
    
    lancamentos_atualizados = cursor.rowcount
    print(f"✓ {lancamentos_atualizados} lançamentos atualizados")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*50)
    print(f"\nResumo:")
    print(f"  • Clientes: {clientes_atualizados}")
    print(f"  • Fornecedores: {fornecedores_atualizados}")
    print(f"  • Categorias: {categorias_atualizadas}")
    print(f"  • Contas Bancárias: {contas_atualizadas}")
    print(f"  • Lançamentos: {lancamentos_atualizados}")
    print(f"\nTOTAL: {clientes_atualizados + fornecedores_atualizados + categorias_atualizadas + contas_atualizadas + lancamentos_atualizados} registros atualizados")

if __name__ == '__main__':
    print("="*50)
    print("CONVERSÃO PARA MAIÚSCULAS")
    print("="*50)
    print("\nEste script irá converter TODOS os dados para MAIÚSCULAS.")
    resposta = input("\nDeseja continuar? (S/N): ").strip().upper()
    
    if resposta == 'S':
        atualizar_maiusculas()
    else:
        print("\nOperação cancelada.")

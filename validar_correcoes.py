#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para validar as correções aplicadas no sistema
"""

import sys
import os

def validar_sintaxe_python():
    """Valida sintaxe do web_server.py"""
    print("🔍 Validando sintaxe Python...")
    
    try:
        import py_compile
        py_compile.compile('web_server.py', doraise=True)
        print("✅ web_server.py: Sintaxe OK")
        return True
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe em web_server.py:")
        print(f"   Linha {e.lineno}: {e.msg}")
        print(f"   {e.text}")
        return False
    except Exception as e:
        print(f"❌ Erro ao validar: {e}")
        return False

def validar_imports():
    """Verifica se imports principais funcionam"""
    print("\n🔍 Validando imports...")
    
    try:
        # Teste de import básico
        from urllib.parse import unquote
        print("✅ urllib.parse.unquote: OK")
        
        # Teste de uso
        teste = unquote("ITAU-ALVES%20E%20SOUZA%20-%204216%2F1236-7")
        esperado = "ITAU-ALVES E SOUZA - 4216/1236-7"
        
        if teste == esperado:
            print(f"✅ Decode funciona: '{teste}'")
        else:
            print(f"❌ Decode incorreto: '{teste}' != '{esperado}'")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

def validar_arquivos_modificados():
    """Verifica se os arquivos foram modificados"""
    print("\n🔍 Validando arquivos modificados...")
    
    arquivos = {
        'web_server.py': [
            'from urllib.parse import unquote',
            'nome = unquote(nome)',
            "data = request.json or {}",
            "motivo = data.get('motivo', 'Inativado pelo usuário')"
        ],
        'static/app.js': [
            'body: JSON.stringify({})'
        ],
        'templates/interface_nova.html': [
            'window.currentEmpresaId = data.empresas_disponiveis[0].id',
            'FALLBACK: Se empresa_atual não existe'
        ]
    }
    
    todos_ok = True
    for arquivo, patterns in arquivos.items():
        if not os.path.exists(arquivo):
            print(f"⚠️ {arquivo}: Arquivo não encontrado")
            continue
            
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        encontrados = 0
        for pattern in patterns:
            if pattern in conteudo:
                encontrados += 1
        
        if encontrados == len(patterns):
            print(f"✅ {arquivo}: {encontrados}/{len(patterns)} padrões encontrados")
        else:
            print(f"❌ {arquivo}: {encontrados}/{len(patterns)} padrões encontrados")
            todos_ok = False
    
    return todos_ok

def main():
    """Executa todas as validações"""
    print("="*70)
    print("🔧 VALIDAÇÃO DAS CORREÇÕES APLICADAS")
    print("="*70)
    
    resultados = []
    
    # 1. Sintaxe Python
    resultados.append(("Sintaxe Python", validar_sintaxe_python()))
    
    # 2. Imports
    resultados.append(("Imports", validar_imports()))
    
    # 3. Arquivos modificados
    resultados.append(("Arquivos Modificados", validar_arquivos_modificados()))
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO DAS VALIDAÇÕES")
    print("="*70)
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status}: {nome}")
    
    total = len(resultados)
    passou = sum(1 for _, r in resultados if r)
    
    print(f"\n🎯 Total: {passou}/{total} validações passaram")
    
    if passou == total:
        print("✅ Todas as correções foram aplicadas corretamente!")
        return 0
    else:
        print("❌ Algumas validações falharam")
        return 1

if __name__ == '__main__':
    sys.exit(main())

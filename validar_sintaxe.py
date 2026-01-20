"""
Validação rápida: Verifica sintaxe dos módulos criados
"""

import sys
import os

print("🔍 Validando sintaxe dos módulos da Fase 7...")
print("="*60)

errors = []
warnings = []

# Verificar cache_helper.py
print("\n📦 Verificando app/utils/cache_helper.py...")
try:
    with open('app/utils/cache_helper.py', 'r', encoding='utf-8') as f:
        code = f.read()
        compile(code, 'cache_helper.py', 'exec')
    print("   ✅ Sintaxe OK")
    print(f"   📏 {len(code.split(chr(10)))} linhas")
except SyntaxError as e:
    print(f"   ❌ Erro de sintaxe: {e}")
    errors.append('cache_helper.py')
except FileNotFoundError:
    print("   ⚠️  Arquivo não encontrado")
    warnings.append('cache_helper.py')

# Verificar pagination_helper.py
print("\n📦 Verificando app/utils/pagination_helper.py...")
try:
    with open('app/utils/pagination_helper.py', 'r', encoding='utf-8') as f:
        code = f.read()
        compile(code, 'pagination_helper.py', 'exec')
    print("   ✅ Sintaxe OK")
    print(f"   📏 {len(code.split(chr(10)))} linhas")
except SyntaxError as e:
    print(f"   ❌ Erro de sintaxe: {e}")
    errors.append('pagination_helper.py')
except FileNotFoundError:
    print("   ⚠️  Arquivo não encontrado")
    warnings.append('pagination_helper.py')

# Verificar migration_performance_indexes.py
print("\n📦 Verificando migration_performance_indexes.py...")
try:
    with open('migration_performance_indexes.py', 'r', encoding='utf-8') as f:
        code = f.read()
        compile(code, 'migration_performance_indexes.py', 'exec')
    print("   ✅ Sintaxe OK")
    print(f"   📏 {len(code.split(chr(10)))} linhas")
    
    # Contar índices
    index_count = code.count("'name':")
    print(f"   📊 {index_count} índices definidos")
    
except SyntaxError as e:
    print(f"   ❌ Erro de sintaxe: {e}")
    errors.append('migration_performance_indexes.py')
except FileNotFoundError:
    print("   ⚠️  Arquivo não encontrado")
    warnings.append('migration_performance_indexes.py')

# Verificar web_server.py (imports)
print("\n📦 Verificando imports em web_server.py...")
try:
    with open('web_server.py', 'r', encoding='utf-8') as f:
        code = f.read()
        
    # Verificar imports importantes
    checks = [
        ('from flask_compress import Compress', 'Flask-Compress import'),
        ('compress = Compress()', 'Compress initialization'),
        ('compress.init_app(app)', 'Compress app init'),
        ('@app.route(\'/api/debug/create-performance-indexes\'', 'Migration endpoint'),
    ]
    
    for check_str, description in checks:
        if check_str in code:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} NÃO ENCONTRADO")
            errors.append(f'web_server.py: {description}')
            
except FileNotFoundError:
    print("   ⚠️  web_server.py não encontrado")
    warnings.append('web_server.py')

# Verificar requirements_web.txt
print("\n📦 Verificando requirements_web.txt...")
try:
    with open('requirements_web.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'flask-compress' in content.lower():
        print("   ✅ flask-compress presente")
    else:
        print("   ❌ flask-compress FALTANDO")
        errors.append('requirements_web.txt: flask-compress')
        
except FileNotFoundError:
    print("   ⚠️  requirements_web.txt não encontrado")
    warnings.append('requirements_web.txt')

# Resumo
print("\n" + "="*60)
print("📊 RESUMO DA VALIDAÇÃO")
print("="*60)

if not errors and not warnings:
    print("✅ TUDO OK! Todos os módulos validados com sucesso")
    print("\n📝 Próximos passos:")
    print("   1. Fazer deploy no Railway")
    print("   2. Executar POST /api/debug/create-performance-indexes")
    print("   3. Testar performance dos relatórios")
    sys.exit(0)
elif errors:
    print(f"❌ {len(errors)} ERRO(S) ENCONTRADO(S):")
    for err in errors:
        print(f"   - {err}")
    if warnings:
        print(f"\n⚠️  {len(warnings)} AVISO(S):")
        for warn in warnings:
            print(f"   - {warn}")
    sys.exit(1)
else:
    print(f"⚠️  {len(warnings)} AVISO(S):")
    for warn in warnings:
        print(f"   - {warn}")
    print("\n⚠️  Alguns arquivos não foram encontrados, mas não há erros de sintaxe")
    sys.exit(0)

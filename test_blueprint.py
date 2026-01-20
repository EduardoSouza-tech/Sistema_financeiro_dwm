"""
Script de teste para verificar se o blueprint de Kits foi carregado corretamente
"""
import sys
sys.path.insert(0, '.')

try:
    print("1️⃣ Testando import do register_blueprints...")
    from app.routes import register_blueprints
    print("   ✅ Import funcionou!\n")
    
    print("2️⃣ Testando import do blueprint de kits...")
    from app.routes.kits import kits_bp
    print("   ✅ Blueprint importado!\n")
    
    print("3️⃣ Verificando rotas registradas no blueprint...")
    for rule in kits_bp.url_map.iter_rules():
        print(f"   - {rule.rule} [{', '.join(rule.methods)}]")
    
    print("\n✅ TODOS OS TESTES PASSARAM!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

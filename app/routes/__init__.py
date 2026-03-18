"""
Rotas da aplicação organizadas por módulo
Cada arquivo contém as rotas de um domínio específico
"""

from flask import Blueprint

def register_blueprints(app):
    """
    Registra todos os blueprints da aplicação
    
    Args:
        app: Instância do Flask
    """
    # Import dinâmico para evitar imports circulares
    try:
        print("🔄 Tentando importar blueprint 'kits'...")
        from .kits import kits_bp
        app.register_blueprint(kits_bp, url_prefix='/api')
        print("✅ Blueprint 'kits' registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar blueprint 'kits': {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("🔄 Tentando importar blueprint 'contratos'...")
        from .contratos import contratos_bp
        app.register_blueprint(contratos_bp)
        print("✅ Blueprint 'contratos' registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar blueprint 'contratos': {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("🔄 Tentando importar blueprint 'sessoes'...")
        from .sessoes import sessoes_bp
        app.register_blueprint(sessoes_bp)
        print("✅ Blueprint 'sessões' registrado")
    except Exception as e:
        print(f"❌ Erro ao registrar blueprint 'sessões': {e}")
        import traceback
        traceback.print_exc()
    
    try:
        from .funcoes_responsaveis import funcoes_bp
        app.register_blueprint(funcoes_bp)
        print("✅ Blueprint 'funções de responsáveis' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'funções de responsáveis' não encontrado: {e}")
    
    try:
        from .custos_operacionais import custos_bp
        app.register_blueprint(custos_bp)
        print("✅ Blueprint 'custos operacionais' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'custos operacionais' não encontrado: {e}")
    
    try:
        from .tags import tags_bp
        app.register_blueprint(tags_bp)
        print("✅ Blueprint 'tags' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'tags' não encontrado: {e}")
    
    try:
        from .relatorios import relatorios_bp
        app.register_blueprint(relatorios_bp)
        print("✅ Blueprint 'relatórios' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'relatórios' não encontrado: {e}")
    
    try:
        from .performance import performance_bp
        app.register_blueprint(performance_bp)
        print("✅ Blueprint 'performance' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'performance' não encontrado: {e}")
    
    try:
        from .agenda import agenda_bp
        app.register_blueprint(agenda_bp)
        print("✅ Blueprint 'agenda' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'agenda' não encontrado: {e}")
    
    try:
        import sys
        import os
        # Adicionar o diretório raiz ao path se necessário
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        
        from import_routes import import_bp
        app.register_blueprint(import_bp)
        print("✅ Blueprint 'import' registrado em /api/admin/import")
        
        # Listar rotas do blueprint
        for rule in app.url_map.iter_rules():
            if 'import' in rule.rule:
                print(f"   📍 {rule.rule} - {list(rule.methods - {'HEAD', 'OPTIONS'})}")
    except ImportError as e:
        print(f"⚠️  Blueprint 'import' não encontrado: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    except Exception as e:
        print(f"❌ Erro ao registrar blueprint 'import': {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    
    # REMESSA DE PAGAMENTOS SICREDI (Módulo independente - não afeta outras rotas)
    try:
        from .remessa import remessa_bp
        app.register_blueprint(remessa_bp)
        print("✅ Blueprint 'remessa de pagamentos' registrado em /api/remessa")
        
        # Listar rotas do blueprint
        for rule in app.url_map.iter_rules():
            if 'remessa' in rule.rule:
                print(f"   📍 {rule.rule} - {list(rule.methods - {'HEAD', 'OPTIONS'})}")
    except ImportError as e:
        print(f"⚠️  Blueprint 'remessa' não encontrado: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    except Exception as e:
        print(f"❌ Erro ao registrar blueprint 'remessa': {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    
    # SUPORTE / CHAMADOS
    try:
        from .suporte import suporte_bp
        app.register_blueprint(suporte_bp)
        print("✅ Blueprint 'suporte' registrado em /api/suporte")
    except ImportError as e:
        print(f"⚠️  Blueprint 'suporte' não encontrado: {e}")
    except Exception as e:
        print(f"❌ Erro ao registrar blueprint 'suporte': {e}")

    # Adicionar outros blueprints aqui conforme forem criados
    # from .clientes import clientes_bp
    # app.register_blueprint(clientes_bp, url_prefix='/api')

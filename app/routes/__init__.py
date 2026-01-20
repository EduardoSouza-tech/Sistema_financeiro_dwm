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
        from .kits import kits_bp
        app.register_blueprint(kits_bp, url_prefix='/api')
        print("✅ Blueprint 'kits' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'kits' não encontrado: {e}")
    
    try:
        from .contratos import contratos_bp
        app.register_blueprint(contratos_bp)
        print("✅ Blueprint 'contratos' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'contratos' não encontrado: {e}")
    
    try:
        from .sessoes import sessoes_bp
        app.register_blueprint(sessoes_bp)
        print("✅ Blueprint 'sessões' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'sessões' não encontrado: {e}")
    
    try:
        from .relatorios import relatorios_bp
        app.register_blueprint(relatorios_bp)
        print("✅ Blueprint 'relatórios' registrado")
    except ImportError as e:
        print(f"⚠️  Blueprint 'relatórios' não encontrado: {e}")
    
    # Adicionar outros blueprints aqui conforme forem criados
    # from .clientes import clientes_bp
    # app.register_blueprint(clientes_bp, url_prefix='/api')

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
    
    # Adicionar outros blueprints aqui conforme forem criados
    # from .clientes import clientes_bp
    # app.register_blueprint(clientes_bp, url_prefix='/api')

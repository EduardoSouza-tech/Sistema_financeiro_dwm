"""
Script de Inicialização do Servidor Web
Carrega variáveis do .env antes de iniciar
"""
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Verificar se DATABASE_URL está configurado
if not os.getenv('DATABASE_URL'):
    print("❌ ERRO: DATABASE_URL não configurado no .env")
    print("   Edite o arquivo .env e configure DATABASE_URL")
    exit(1)

print("✅ Variáveis de ambiente carregadas do .env")
print(f"   DATABASE_URL: {os.getenv('DATABASE_URL')[:30]}...")
print(f"   SECRET_KEY: {'Configurado' if os.getenv('SECRET_KEY') else 'NÃO configurado'}")
print()

# Importar e iniciar o servidor
if __name__ == '__main__':
    try:
        import web_server
        # Se web_server.py tiver if __name__ == '__main__', o servidor já inicia
        # Caso contrário, iniciar manualmente:
        if hasattr(web_server, 'app'):
            web_server.app.run(
                host='0.0.0.0',
                port=int(os.getenv('PORT', 5000)),
                debug=(os.getenv('FLASK_ENV') == 'development')
            )
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        raise

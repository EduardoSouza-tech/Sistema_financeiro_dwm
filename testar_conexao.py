"""
Script para testar conexão com PostgreSQL
"""
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL não configurado!")
    print("Configure no arquivo .env")
    exit(1)

print(f"✅ DATABASE_URL encontrado")
print(f"   URL: {DATABASE_URL[:30]}...") # Mostra só início por segurança

# Testar conexão
try:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    
    print(f"\n✅ Conexão com PostgreSQL bem-sucedida!")
    print(f"   Versão: {version[0][:50]}...")
    
    cur.close()
    conn.close()
    
    print("\n🎉 Tudo pronto! Pode rodar o servidor.")
    
except ImportError:
    print("\n❌ psycopg2 não instalado!")
    print("   Execute: pip install psycopg2-binary")
    
except Exception as e:
    print(f"\n❌ Erro ao conectar:")
    print(f"   {e}")
    print("\n💡 Verifique:")
    print("   1. URL está correta no .env")
    print("   2. Credenciais estão corretas")
    print("   3. Firewall/rede permite conexão")

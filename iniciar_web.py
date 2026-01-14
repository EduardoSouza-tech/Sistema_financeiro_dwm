"""
Script para iniciar o servidor web do Sistema Financeiro
"""
import os
import sys
import webbrowser
from time import sleep
from threading import Timer

def abrir_navegador():
    """Abre o navegador após 2 segundos"""
    sleep(2)
    print("\n🌐 Abrindo navegador...")
    # Detecta a porta do ambiente ou usa 5000 como padrão
    port = os.getenv('PORT', '5000')
    webbrowser.open(f'http://127.0.0.1:{port}')

def iniciar_servidor():
    """Inicia o servidor Flask"""
    print("="*70)
    print(" 🚀 SISTEMA FINANCEIRO - INTERFACE WEB")
    print("="*70)
    print()
    port = os.getenv('PORT', '5000')
    print(" 📋 Instruções:")
    print(f"    • O servidor será iniciado na porta: {port}")
    print("    • O navegador abrirá automaticamente")
    print("    • Para parar o servidor: pressione Ctrl+C")
    print()
    print("="*70)
    print()
    
    # Abrir navegador em 2 segundos
    Timer(2.0, abrir_navegador).start()
    
    # Importar e iniciar o servidor
    try:
        from web_server import app
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n✓ Servidor encerrado pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Erro ao iniciar servidor: {e}")
        input("\nPressione Enter para sair...")
        sys.exit(1)

if __name__ == '__main__':
    iniciar_servidor()

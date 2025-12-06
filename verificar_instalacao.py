#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INSTALAÇÃO E VERIFICAÇÃO DO SISTEMA FINANCEIRO
Execute este script para verificar se tudo está funcionando corretamente
"""

import sys
import os
from pathlib import Path

def verificar_instalacao():
    """Verifica se todos os arquivos necessários estão presentes"""
    
    print("=" * 70)
    print("  VERIFICAÇÃO DE INSTALAÇÃO - SISTEMA FINANCEIRO".center(70))
    print("=" * 70)
    print()
    
    # Diretório atual
    dir_atual = Path(__file__).parent
    print(f"📁 Diretório do sistema: {dir_atual}\n")
    
    # Arquivos necessários
    arquivos_necessarios = {
        "Código Principal": [
            "models.py",
            "gerenciador.py",
            "main.py"
        ],
        "Documentação": [
            "README.md",
            "GUIA_COMPLETO.md",
            "INICIO_RAPIDO.txt",
            "RESUMO_PROJETO.md"
        ],
        "Testes e Exemplos": [
            "teste.py",
            "exemplos.py",
            "demo.py"
        ]
    }
    
    todos_ok = True
    
    # Verificar arquivos
    for categoria, arquivos in arquivos_necessarios.items():
        print(f"📋 {categoria}:")
        for arquivo in arquivos:
            caminho = dir_atual / arquivo
            if caminho.exists():
                tamanho = caminho.stat().st_size
                print(f"   ✓ {arquivo} ({tamanho:,} bytes)")
            else:
                print(f"   ✗ {arquivo} - FALTANDO!")
                todos_ok = False
        print()
    
    # Verificar Python
    print("🐍 Versão do Python:")
    versao = sys.version_info
    print(f"   Python {versao.major}.{versao.minor}.{versao.micro}")
    
    if versao.major < 3 or (versao.major == 3 and versao.minor < 7):
        print("   ⚠️  AVISO: Recomendado Python 3.7 ou superior")
        todos_ok = False
    else:
        print("   ✓ Versão compatível")
    print()
    
    # Verificar importações
    print("📦 Verificando importações:")
    modulos_testar = [
        ("datetime", "datetime"),
        ("json", "json"),
        ("os", "os"),
        ("enum", "enum"),
        ("typing", "typing")
    ]
    
    for nome, modulo in modulos_testar:
        try:
            __import__(modulo)
            print(f"   ✓ {nome}")
        except ImportError:
            print(f"   ✗ {nome} - FALTANDO!")
            todos_ok = False
    print()
    
    # Tentar importar módulos do sistema
    print("🔧 Verificando módulos do sistema:")
    
    sys.path.insert(0, str(dir_atual))
    
    try:
        from models import ContaBancaria, Lancamento, TipoLancamento
        print("   ✓ models.py")
    except Exception as e:
        print(f"   ✗ models.py - ERRO: {e}")
        todos_ok = False
    
    try:
        from gerenciador import GerenciadorFinanceiro
        print("   ✓ gerenciador.py")
    except Exception as e:
        print(f"   ✗ gerenciador.py - ERRO: {e}")
        todos_ok = False
    
    print()
    
    # Resultado final
    print("=" * 70)
    if todos_ok:
        print("  ✅ INSTALAÇÃO COMPLETA E FUNCIONAL!".center(70))
        print("=" * 70)
        print()
        print("🚀 Sistema pronto para uso!")
        print()
        print("📝 Próximos passos:")
        print("   1. Execute 'python main.py' para usar o sistema")
        print("   2. Execute 'python teste.py' para rodar os testes")
        print("   3. Execute 'python demo.py' para ver uma demonstração")
        print("   4. Leia README.md para mais informações")
        print()
        return True
    else:
        print("  ⚠️  PROBLEMAS DETECTADOS NA INSTALAÇÃO".center(70))
        print("=" * 70)
        print()
        print("Alguns arquivos ou módulos estão faltando.")
        print("Verifique os erros acima e corrija antes de usar o sistema.")
        print()
        return False

def teste_rapido():
    """Executa um teste rápido do sistema"""
    print("=" * 70)
    print("  TESTE RÁPIDO DO SISTEMA".center(70))
    print("=" * 70)
    print()
    
    try:
        from datetime import datetime, timedelta
        from gerenciador import GerenciadorFinanceiro
        from models import TipoLancamento
        
        print("Criando gerenciador de testes...")
        ger = GerenciadorFinanceiro("verificacao_teste.json")
        
        # Limpar dados de teste
        ger.contas.clear()
        ger.lancamentos.clear()
        
        print("✓ Gerenciador criado")
        
        print("\nAdicionando conta de teste...")
        conta = ger.adicionar_conta("Teste", "Banco Teste", "0001", "12345", 1000.00)
        print(f"✓ Conta criada: {conta.nome} - Saldo: R$ {conta.saldo_atual:,.2f}")
        
        print("\nAdicionando receita de teste...")
        receita = ger.adicionar_lancamento(
            "Receita Teste",
            500.00,
            TipoLancamento.RECEITA,
            "Vendas",
            datetime.now() + timedelta(days=5)
        )
        print(f"✓ Receita criada: ID {receita.id} - R$ {receita.valor:,.2f}")
        
        print("\nCalculando totais...")
        saldo = ger.calcular_saldo_total()
        receber = ger.calcular_contas_receber()
        print(f"✓ Saldo Total: R$ {saldo:,.2f}")
        print(f"✓ A Receber: R$ {receber:,.2f}")
        
        print("\nSalvando dados...")
        ger.salvar_dados()
        print("✓ Dados salvos em verificacao_teste.json")
        
        print("\n" + "=" * 70)
        print("  ✅ TESTE RÁPIDO CONCLUÍDO COM SUCESSO!".center(70))
        print("=" * 70)
        print()
        print("O sistema está funcionando perfeitamente!")
        print()
        
        # Limpar arquivo de teste
        try:
            os.remove("verificacao_teste.json")
            print("🧹 Arquivo de teste removido.\n")
        except:
            pass
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("  ⚠️  ERRO NO TESTE".center(70))
        print("=" * 70)
        print()
        print(f"Erro: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        return False

def main():
    """Função principal"""
    print()
    
    # Verificar instalação
    instalacao_ok = verificar_instalacao()
    
    if not instalacao_ok:
        print("⚠️  Corrija os problemas de instalação antes de continuar.")
        return
    
    # Perguntar se quer fazer teste rápido
    print()
    resposta = input("Deseja executar um teste rápido do sistema? (s/n): ")
    
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        print()
        teste_ok = teste_rapido()
        
        if teste_ok:
            print("=" * 70)
            print("  SISTEMA 100% FUNCIONAL - PRONTO PARA USO!".center(70))
            print("=" * 70)
            print()
            print("🎉 Parabéns! Tudo está funcionando perfeitamente!")
            print()
            print("📚 Comandos disponíveis:")
            print("   • python main.py      - Interface completa")
            print("   • python teste.py     - Testes automatizados")
            print("   • python demo.py      - Demonstração visual")
            print("   • python exemplos.py  - Exemplos práticos")
            print()
    else:
        print()
        print("Você pode executar este script novamente quando quiser verificar a instalação.")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerificação interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()

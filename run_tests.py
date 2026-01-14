#!/usr/bin/env python
"""
Script para executar testes rapidamente
"""
import subprocess
import sys
import os

def run_tests(args=None):
    """
    Executa a suite de testes
    
    Args:
        args: Argumentos adicionais para pytest
    """
    cmd = ['pytest', 'tests/', '-v']
    
    if args:
        cmd.extend(args)
    
    # Configurar variáveis de ambiente para testes
    test_env = os.environ.copy()
    test_env['TESTING'] = 'true'
    test_env['LOG_LEVEL'] = 'DEBUG'
    
    print("🧪 Executando testes...\n")
    result = subprocess.run(cmd, env=test_env)
    
    return result.returncode


def run_tests_with_coverage():
    """Executa testes com relatório de cobertura"""
    print("📊 Executando testes com cobertura...\n")
    
    cmd = [
        'pytest',
        'tests/',
        '-v',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term',
        '--cov-report=xml'
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Relatório de cobertura gerado em: htmlcov/index.html")
    
    return result.returncode


def run_specific_test(test_path):
    """Executa um teste específico"""
    print(f"🎯 Executando teste: {test_path}\n")
    
    cmd = ['pytest', test_path, '-v', '-s']
    result = subprocess.run(cmd)
    
    return result.returncode


def run_failed_tests():
    """Re-executa apenas os testes que falharam"""
    print("🔄 Re-executando testes que falharam...\n")
    
    cmd = ['pytest', 'tests/', '-v', '--lf']
    result = subprocess.run(cmd)
    
    return result.returncode


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Executar testes do Sistema Financeiro')
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Executar com relatório de cobertura'
    )
    parser.add_argument(
        '--failed',
        action='store_true',
        help='Re-executar apenas testes que falharam'
    )
    parser.add_argument(
        '--test',
        type=str,
        help='Executar teste específico (ex: tests/test_auth.py::test_login)'
    )
    
    args = parser.parse_args()
    
    if args.coverage:
        exit_code = run_tests_with_coverage()
    elif args.failed:
        exit_code = run_failed_tests()
    elif args.test:
        exit_code = run_specific_test(args.test)
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)

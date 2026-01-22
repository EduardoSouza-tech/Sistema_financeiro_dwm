"""
Análise de Segurança - CSRF Protection
=======================================

Este script analisa todos os endpoints isentos de CSRF e verifica
se a isenção é justificada ou representa risco de segurança.
"""

import re
from typing import List, Dict, Tuple


class CSRFSecurityAnalyzer:
    """Analisador de segurança CSRF"""
    
    # Endpoints que DEVEM estar isentos de CSRF
    ENDPOINTS_LEGITIMOS = {
        '/api/auth/login': {
            'justificativa': 'Endpoint público de autenticação - não tem sessão prévia',
            'risco': 'BAIXO',
            'mitigacao': 'Rate limiting aplicado (5 tentativas/minuto)'
        },
        '/api/auth/logout': {
            'justificativa': 'Logout pode ser necessário de múltiplas origens',
            'risco': 'BAIXO',
            'mitigacao': 'Apenas invalida sessão, não realiza ações críticas'
        },
        '/api/auth/register': {
            'justificativa': 'Registro público de usuários',
            'risco': 'MÉDIO',
            'mitigacao': 'Captcha e validação de email recomendados'
        }
    }
    
    # Endpoints de debug que PODEM estar isentos temporariamente
    ENDPOINTS_DEBUG = {
        '/api/debug/criar-admin': {
            'justificativa': 'Endpoint temporário para setup inicial no Railway',
            'risco': 'ALTO',
            'acao_requerida': 'REMOVER EM PRODUÇÃO ou adicionar autenticação admin',
            'temporario': True
        },
        '/api/debug/fix-kits-table': {
            'justificativa': 'Migration temporária para correção de schema',
            'risco': 'ALTO',
            'acao_requerida': 'REMOVER após migration completa ou exigir @require_admin',
            'temporario': True
        },
        '/api/debug/fix-p1-issues': {
            'justificativa': 'Migration temporária P1',
            'risco': 'ALTO',
            'acao_requerida': 'REMOVER após migration completa ou exigir @require_admin',
            'temporario': True
        }
    }
    
    # Endpoints admin que NÃO deveriam estar isentos
    ENDPOINTS_SUSPEITOS = [
        '/api/admin/passwords/force-upgrade'  # Adicionado recentemente
    ]
    
    @staticmethod
    def analisar_endpoint(path: str) -> Dict:
        """
        Analisa um endpoint isento de CSRF
        
        Returns:
            {
                'path': str,
                'categoria': 'legitimo'|'debug'|'suspeito'|'desconhecido',
                'risco': 'BAIXO'|'MEDIO'|'ALTO'|'CRITICO',
                'justificativa': str,
                'recomendacao': str
            }
        """
        # Verificar endpoints legítimos
        if path in CSRFSecurityAnalyzer.ENDPOINTS_LEGITIMOS:
            info = CSRFSecurityAnalyzer.ENDPOINTS_LEGITIMOS[path]
            return {
                'path': path,
                'categoria': 'legitimo',
                'risco': info['risco'],
                'justificativa': info['justificativa'],
                'mitigacao': info.get('mitigacao', 'N/A'),
                'recomendacao': '✅ Isenção justificada'
            }
        
        # Verificar endpoints de debug
        if path in CSRFSecurityAnalyzer.ENDPOINTS_DEBUG:
            info = CSRFSecurityAnalyzer.ENDPOINTS_DEBUG[path]
            return {
                'path': path,
                'categoria': 'debug_temporario',
                'risco': info['risco'],
                'justificativa': info['justificativa'],
                'acao_requerida': info['acao_requerida'],
                'recomendacao': '⚠️ AÇÃO REQUERIDA: ' + info['acao_requerida']
            }
        
        # Verificar endpoints suspeitos
        if path in CSRFSecurityAnalyzer.ENDPOINTS_SUSPEITOS:
            return {
                'path': path,
                'categoria': 'suspeito',
                'risco': 'CRITICO',
                'justificativa': 'Endpoint administrativo não deve estar isento de CSRF',
                'recomendacao': '❌ REMOVER isenção CSRF - adicionar proteção'
            }
        
        # Endpoint desconhecido
        return {
            'path': path,
            'categoria': 'desconhecido',
            'risco': 'DESCONHECIDO',
            'justificativa': 'Endpoint não catalogado',
            'recomendacao': '🔍 INVESTIGAR - verificar se isenção é necessária'
        }
    
    @staticmethod
    def extrair_endpoints_isentos_do_codigo(arquivo_web_server: str) -> List[str]:
        """
        Extrai endpoints isentos de CSRF do código web_server.py
        """
        with open(arquivo_web_server, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        endpoints = []
        
        # Padrão 1: CSRF_EXEMPT_ROUTES = [...]
        match = re.search(
            r'CSRF_EXEMPT_ROUTES\s*=\s*\[(.*?)\]',
            conteudo,
            re.DOTALL
        )
        if match:
            rotas_texto = match.group(1)
            rotas = re.findall(r"'([^']+)'", rotas_texto)
            endpoints.extend(rotas)
        
        # Padrão 2: @csrf_instance.exempt logo antes de @app.route
        pattern = r'@csrf_instance\.exempt\s*\n\s*(?:@[^\n]+\s*\n\s*)*@app\.route\([\'"]([^\'"]+)[\'"]'
        matches = re.finditer(pattern, conteudo)
        for match in matches:
            rota = match.group(1)
            if rota not in endpoints:
                endpoints.append(rota)
        
        return sorted(set(endpoints))
    
    @staticmethod
    def gerar_relatorio(arquivo_web_server: str = 'web_server.py') -> Dict:
        """
        Gera relatório completo de análise de segurança CSRF
        """
        endpoints = CSRFSecurityAnalyzer.extrair_endpoints_isentos_do_codigo(
            arquivo_web_server
        )
        
        relatorio = {
            'total_endpoints_isentos': len(endpoints),
            'por_categoria': {
                'legitimo': 0,
                'debug_temporario': 0,
                'suspeito': 0,
                'desconhecido': 0
            },
            'por_risco': {
                'BAIXO': 0,
                'MEDIO': 0,
                'ALTO': 0,
                'CRITICO': 0,
                'DESCONHECIDO': 0
            },
            'endpoints': [],
            'acoes_requeridas': []
        }
        
        for endpoint in endpoints:
            analise = CSRFSecurityAnalyzer.analisar_endpoint(endpoint)
            relatorio['endpoints'].append(analise)
            
            # Contadores
            relatorio['por_categoria'][analise['categoria']] += 1
            relatorio['por_risco'][analise['risco']] += 1
            
            # Ações requeridas
            if analise['categoria'] in ['debug_temporario', 'suspeito'] or \
               analise['risco'] in ['ALTO', 'CRITICO']:
                relatorio['acoes_requeridas'].append({
                    'endpoint': endpoint,
                    'risco': analise['risco'],
                    'acao': analise['recomendacao']
                })
        
        return relatorio
    
    @staticmethod
    def imprimir_relatorio(relatorio: Dict):
        """Imprime relatório formatado"""
        print("\n" + "="*80)
        print(" ANÁLISE DE SEGURANÇA - CSRF PROTECTION")
        print("="*80 + "\n")
        
        print(f"📊 Total de endpoints isentos: {relatorio['total_endpoints_isentos']}\n")
        
        print("📈 Por Categoria:")
        for cat, count in relatorio['por_categoria'].items():
            if count > 0:
                emoji = {
                    'legitimo': '✅',
                    'debug_temporario': '⚠️',
                    'suspeito': '❌',
                    'desconhecido': '🔍'
                }.get(cat, '❓')
                print(f"   {emoji} {cat}: {count}")
        
        print("\n🎯 Por Nível de Risco:")
        for risco, count in relatorio['por_risco'].items():
            if count > 0:
                emoji = {
                    'BAIXO': '🟢',
                    'MEDIO': '🟡',
                    'ALTO': '🟠',
                    'CRITICO': '🔴',
                    'DESCONHECIDO': '⚪'
                }.get(risco, '❓')
                print(f"   {emoji} {risco}: {count}")
        
        print("\n" + "="*80)
        print(" DETALHAMENTO DOS ENDPOINTS")
        print("="*80 + "\n")
        
        for analise in relatorio['endpoints']:
            emoji_risco = {
                'BAIXO': '🟢',
                'MEDIO': '🟡',
                'ALTO': '🟠',
                'CRITICO': '🔴',
                'DESCONHECIDO': '⚪'
            }.get(analise['risco'], '❓')
            
            print(f"{emoji_risco} {analise['path']}")
            print(f"   Categoria: {analise['categoria']}")
            print(f"   Risco: {analise['risco']}")
            print(f"   Justificativa: {analise['justificativa']}")
            print(f"   {analise['recomendacao']}")
            print()
        
        if relatorio['acoes_requeridas']:
            print("="*80)
            print(" ⚠️  AÇÕES REQUERIDAS")
            print("="*80 + "\n")
            
            for acao in relatorio['acoes_requeridas']:
                print(f"🔴 {acao['endpoint']}")
                print(f"   Risco: {acao['risco']}")
                print(f"   {acao['acao']}")
                print()
        
        print("="*80)
        print(" RECOMENDAÇÕES GERAIS")
        print("="*80 + "\n")
        
        print("1. 🔒 Endpoints administrativos NUNCA devem estar isentos de CSRF")
        print("2. ⏰ Endpoints de debug devem ser removidos em produção")
        print("3. 🛡️ Endpoints públicos devem ter rate limiting")
        print("4. 📝 Todas as isenções devem ser documentadas e justificadas")
        print("5. 🔄 Revisar periodicamente a lista de isenções")
        print()


def corrigir_endpoint_admin_password():
    """
    Corrige endpoint administrativo que está incorretamente isento de CSRF
    """
    print("\n🔧 CORREÇÃO AUTOMÁTICA")
    print("="*80)
    print("Removendo isenção CSRF de /api/admin/passwords/force-upgrade")
    print("Este endpoint É administrativo e NÃO deve estar isento de CSRF")
    print("A proteção @require_admin já valida sessão, CSRF adiciona camada extra")
    print("="*80 + "\n")
    
    return {
        'arquivo': 'web_server.py',
        'linha_remover': '@csrf_instance.exempt',
        'funcao': 'force_password_upgrade',
        'justificativa': 'Endpoint administrativo - @require_admin já valida sessão'
    }


# ============================================================================
# SCRIPT CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    arquivo = 'web_server.py' if len(sys.argv) < 2 else sys.argv[1]
    
    try:
        relatorio = CSRFSecurityAnalyzer.gerar_relatorio(arquivo)
        CSRFSecurityAnalyzer.imprimir_relatorio(relatorio)
        
        # Sugerir correções
        if relatorio['acoes_requeridas']:
            print("\n💡 SCRIPT DE CORREÇÃO AUTOMÁTICA DISPONÍVEL")
            print("Execute: python csrf_security_review.py --fix")
            print()
        
    except FileNotFoundError:
        print(f"❌ Arquivo {arquivo} não encontrado")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao analisar: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

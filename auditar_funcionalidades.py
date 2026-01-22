"""
🔍 Auditoria de Funcionalidades - Sistema Financeiro
====================================================

Este script identifica:
1. Botões sem implementação no frontend
2. APIs sem conexão com frontend
3. Funções JavaScript órfãs (declaradas mas não chamadas)
4. Endpoints sem handler frontend
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple


class FunctionalityAuditor:
    """Auditor de funcionalidades do sistema"""
    
    def __init__(self, base_path: str = '.'):
        self.base_path = Path(base_path)
        self.frontend_functions = set()
        self.onclick_handlers = set()
        self.api_endpoints = {}
        self.api_calls_frontend = set()
        
    def extract_frontend_functions(self):
        """Extrai todas as funções JavaScript"""
        js_files = [
            'static/app.js',
            'static/analise_functions.js', 
            'static/lazy-integration.js',
            'static/lazy-loader.js'
        ]
        
        functions = {}
        
        for js_file in js_files:
            file_path = self.base_path / js_file
            if not file_path.exists():
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Padrão 1: function nome()
            pattern1 = r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
            for match in re.finditer(pattern1, content):
                func_name = match.group(1)
                functions[func_name] = js_file
            
            # Padrão 2: const nome = function()
            pattern2 = r'(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*function\s*\('
            for match in re.finditer(pattern2, content):
                func_name = match.group(1)
                functions[func_name] = js_file
            
            # Padrão 3: const nome = async function()
            pattern3 = r'(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*async\s+function\s*\('
            for match in re.finditer(pattern3, content):
                func_name = match.group(1)
                functions[func_name] = js_file
            
            # Padrão 4: async function nome()
            pattern4 = r'async\s+function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
            for match in re.finditer(pattern4, content):
                func_name = match.group(1)
                functions[func_name] = js_file
        
        return functions
    
    def extract_onclick_handlers(self):
        """Extrai handlers onclick dos templates"""
        html_files = list((self.base_path / 'templates').glob('*.html'))
        js_files = list((self.base_path / 'static').glob('*.js'))
        
        handlers = {}
        
        for file_path in html_files + js_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # onclick="funcao(...)"
            pattern = r'onclick=["\']([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                handlers[func_name] = str(file_path)
        
        return handlers
    
    def extract_api_endpoints(self):
        """Extrai todos os endpoints da API"""
        web_server = self.base_path / 'web_server.py'
        
        if not web_server.exists():
            return {}
        
        with open(web_server, 'r', encoding='utf-8') as f:
            content = f.read()
        
        endpoints = {}
        
        # Padrão: @app.route('/path', methods=[...])
        pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)\s*(?:@[^\n]+\s*)*\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            path = match.group(1)
            methods = match.group(2) if match.group(2) else 'GET'
            func_name = match.group(3)
            
            # Limpar métodos
            methods_list = [m.strip().strip("'\"") for m in methods.split(',')]
            
            endpoints[path] = {
                'methods': methods_list,
                'handler': func_name
            }
        
        return endpoints
    
    def extract_api_calls_frontend(self):
        """Extrai chamadas de API do frontend"""
        js_files = list((self.base_path / 'static').glob('*.js'))
        
        calls = set()
        
        for file_path in js_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Padrão: fetch('/api/...')
            pattern = r"fetch\(['\"]([^'\"]+)['\"]"
            for match in re.finditer(pattern, content):
                url = match.group(1)
                # Remover query params e normalizar
                url = url.split('?')[0]
                # Se tiver $ ou {, é template string
                if '$' not in url and '{' not in url:
                    calls.add(url)
        
        return calls
    
    def find_orphan_functions(self, functions: Dict, onclick: Dict) -> List[Dict]:
        """Encontra funções JavaScript que nunca são chamadas"""
        js_files = list((self.base_path / 'static').glob('*.js'))
        
        all_content = ""
        for file_path in js_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_content += f.read() + "\n"
        
        orphans = []
        
        for func_name, file in functions.items():
            # Ignorar algumas funções especiais
            if func_name in ['init', 'main', 'setup', 'DOMContentLoaded']:
                continue
            
            # Verificar se está em onclick
            if func_name in onclick:
                continue
            
            # Verificar se é chamada no código
            # Padrão: funcao( ou funcao.
            pattern = rf'\b{func_name}\s*[(\.]'
            
            # Contar ocorrências (pelo menos 2: definição + chamada)
            count = len(re.findall(pattern, all_content))
            
            if count <= 1:  # Apenas definição, nenhuma chamada
                orphans.append({
                    'function': func_name,
                    'file': file,
                    'reason': 'Função definida mas nunca chamada'
                })
        
        return orphans
    
    def find_missing_implementations(self, onclick: Dict, functions: Dict) -> List[Dict]:
        """Encontra botões onclick sem implementação"""
        missing = []
        
        for handler, file in onclick.items():
            if handler not in functions:
                missing.append({
                    'handler': handler,
                    'file': file,
                    'reason': 'Botão onclick sem função implementada'
                })
        
        return missing
    
    def find_unused_endpoints(self, endpoints: Dict, calls: Set) -> List[Dict]:
        """Encontra endpoints sem uso no frontend"""
        unused = []
        
        # Endpoints que devem ser ignorados (usados indiretamente)
        ignore = [
            '/api/auth/verify',
            '/api/debug/',
            '/api/admin/',
            '/',
            '/login',
            '/index'
        ]
        
        for path, info in endpoints.items():
            # Ignorar alguns
            should_ignore = any(path.startswith(ig) for ig in ignore)
            if should_ignore:
                continue
            
            # Verificar se é chamado no frontend
            # Normalizar path (remover params dinâmicos)
            normalized = re.sub(r'<[^>]+>', '*', path)
            
            found = False
            for call in calls:
                if self._match_path(call, path):
                    found = True
                    break
            
            if not found:
                unused.append({
                    'endpoint': path,
                    'methods': info['methods'],
                    'handler': info['handler'],
                    'reason': 'Endpoint sem chamada no frontend'
                })
        
        return unused
    
    def _match_path(self, call: str, endpoint: str) -> bool:
        """Verifica se uma chamada match com um endpoint"""
        # Converter endpoint pattern para regex
        pattern = re.sub(r'<[^>]+>', r'[^/]+', endpoint)
        pattern = f"^{pattern}$"
        
        return bool(re.match(pattern, call))
    
    def generate_report(self) -> Dict:
        """Gera relatório completo"""
        print("🔍 Extraindo funções JavaScript...")
        functions = self.extract_frontend_functions()
        
        print("🔍 Extraindo handlers onclick...")
        onclick = self.extract_onclick_handlers()
        
        print("🔍 Extraindo endpoints da API...")
        endpoints = self.extract_api_endpoints()
        
        print("🔍 Extraindo chamadas de API do frontend...")
        api_calls = self.extract_api_calls_frontend()
        
        print("🔍 Analisando inconsistências...\n")
        
        orphans = self.find_orphan_functions(functions, onclick)
        missing = self.find_missing_implementations(onclick, functions)
        unused = self.find_unused_endpoints(endpoints, api_calls)
        
        return {
            'summary': {
                'total_js_functions': len(functions),
                'total_onclick_handlers': len(onclick),
                'total_api_endpoints': len(endpoints),
                'total_api_calls_frontend': len(api_calls),
                'orphan_functions': len(orphans),
                'missing_implementations': len(missing),
                'unused_endpoints': len(unused)
            },
            'orphan_functions': orphans,
            'missing_implementations': missing,
            'unused_endpoints': unused,
            'all_functions': functions,
            'all_onclick': onclick,
            'all_endpoints': endpoints,
            'all_api_calls': sorted(api_calls)
        }
    
    def print_report(self, report: Dict):
        """Imprime relatório formatado"""
        print("=" * 80)
        print(" 📊 AUDITORIA DE FUNCIONALIDADES - SISTEMA FINANCEIRO")
        print("=" * 80)
        print()
        
        summary = report['summary']
        
        print("📈 RESUMO:")
        print(f"   Total de funções JavaScript: {summary['total_js_functions']}")
        print(f"   Total de handlers onclick: {summary['total_onclick_handlers']}")
        print(f"   Total de endpoints API: {summary['total_api_endpoints']}")
        print(f"   Total de chamadas API frontend: {summary['total_api_calls_frontend']}")
        print()
        
        print("⚠️  PROBLEMAS ENCONTRADOS:")
        print(f"   🔴 Funções órfãs: {summary['orphan_functions']}")
        print(f"   🔴 Botões sem implementação: {summary['missing_implementations']}")
        print(f"   🟡 Endpoints não usados: {summary['unused_endpoints']}")
        print()
        
        if report['missing_implementations']:
            print("=" * 80)
            print(" 🔴 BOTÕES SEM IMPLEMENTAÇÃO (CRÍTICO)")
            print("=" * 80)
            print()
            for item in report['missing_implementations']:
                print(f"❌ {item['handler']}()")
                print(f"   Arquivo: {item['file']}")
                print(f"   Motivo: {item['reason']}")
                print()
        
        if report['unused_endpoints']:
            print("=" * 80)
            print(" 🟡 ENDPOINTS SEM USO NO FRONTEND")
            print("=" * 80)
            print()
            for item in report['unused_endpoints'][:20]:  # Mostrar primeiros 20
                print(f"⚠️  {item['endpoint']}")
                print(f"   Métodos: {', '.join(item['methods'])}")
                print(f"   Handler: {item['handler']}()")
                print(f"   Motivo: {item['reason']}")
                print()
        
        if report['orphan_functions']:
            print("=" * 80)
            print(" 🟠 FUNÇÕES JavaScript ÓRFÃS")
            print("=" * 80)
            print()
            for item in report['orphan_functions'][:15]:  # Mostrar primeiras 15
                print(f"🔸 {item['function']}()")
                print(f"   Arquivo: {item['file']}")
                print(f"   Motivo: {item['reason']}")
                print()
        
        print("=" * 80)
        print(" 💡 RECOMENDAÇÕES")
        print("=" * 80)
        print()
        print("1. 🔴 URGENTE: Implementar funções faltantes para botões")
        print("2. 🟡 Conectar endpoints não usados ou documentar como deprecated")
        print("3. 🟠 Remover funções órfãs ou adicionar chamadas")
        print("4. 📝 Adicionar comentários TODO nas funções incompletas")
        print()


if __name__ == "__main__":
    auditor = FunctionalityAuditor('.')
    report = auditor.generate_report()
    auditor.print_report(report)
    
    # Salvar relatório JSON para análise
    import json
    with open('auditoria_funcionalidades.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("✅ Relatório completo salvo em: auditoria_funcionalidades.json")
    print()

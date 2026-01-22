"""
Verificador de Carregamento de Componentes
Analisa se todos os scripts e funções estão carregando corretamente
"""

import re
from pathlib import Path

class VerificadorCarregamento:
    def __init__(self):
        self.erros = []
        self.avisos = []
        self.sucessos = []
        
    def verificar_ordem_scripts(self):
        """Verifica a ordem de carregamento dos scripts no HTML"""
        print("\n" + "="*80)
        print("🔍 VERIFICANDO ORDEM DE CARREGAMENTO DOS SCRIPTS")
        print("="*80)
        
        html_file = Path('templates/interface_nova.html')
        
        if not html_file.exists():
            self.erros.append("❌ Arquivo interface_nova.html não encontrado")
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrair scripts
        scripts = re.findall(r'<script src="([^"]+)"', content)
        
        print("\n📋 Ordem de carregamento detectada:\n")
        for i, script in enumerate(scripts, 1):
            print(f"   {i}. {script}")
        
        # Verificar ordem esperada
        ordem_esperada = [
            'utils.js',
            'lazy-loader.js',
            'app.js',
            'lazy-integration.js',
            'pdf_functions.js',
            'excel_functions.js',
            'analise_functions.js',
            'modals.js'
        ]
        
        scripts_encontrados = [s.split('/')[-1].split('?')[0] for s in scripts if '/static/' in s]
        
        print("\n✅ Scripts esperados vs encontrados:\n")
        for esperado in ordem_esperada:
            if esperado in scripts_encontrados:
                idx = scripts_encontrados.index(esperado)
                print(f"   ✅ {esperado} (posição {idx+1})")
                self.sucessos.append(f"Script {esperado} encontrado")
            else:
                print(f"   ❌ {esperado} NÃO ENCONTRADO")
                self.erros.append(f"Script {esperado} ausente no HTML")
    
    def verificar_funcoes_globais(self):
        """Verifica se funções são expostas globalmente"""
        print("\n" + "="*80)
        print("🔍 VERIFICANDO FUNÇÕES GLOBAIS (window.*)")
        print("="*80)
        
        arquivos = {
            'app.js': ['editarConta', 'excluirConta', 'editarCategoria', 'excluirCategoria',
                      'editarCliente', 'excluirCliente', 'editarFornecedor', 'excluirFornecedor',
                      'loadClientes', 'loadFornecedores', 'showSection'],
            'modals.js': ['openModalConta', 'openModalCategoria', 'openModalCliente', 
                         'openModalFornecedor', 'openModalReceita', 'openModalDespesa',
                         'salvarConta', 'salvarCategoria', 'salvarCliente', 'salvarFornecedor'],
            'pdf_functions.js': ['exportarClientesPDF', 'exportarFornecedoresPDF',
                                'exportarContasPagarPDF', 'exportarContasReceberPDF'],
            'excel_functions.js': ['exportarClientesExcel', 'exportarFornecedoresExcel']
        }
        
        for arquivo, funcoes_esperadas in arquivos.items():
            print(f"\n📂 {arquivo}:")
            
            file_path = Path(f'static/{arquivo}')
            if not file_path.exists():
                print(f"   ❌ Arquivo não encontrado")
                self.erros.append(f"Arquivo {arquivo} não encontrado")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for funcao in funcoes_esperadas:
                # Verificar se função é definida
                pattern_def = rf'(?:async\s+)?function\s+{funcao}\s*\(|(?:const|let|var)\s+{funcao}\s*='
                if re.search(pattern_def, content):
                    # Verificar se é exposta globalmente
                    pattern_global = rf'window\.{funcao}\s*='
                    if re.search(pattern_global, content):
                        print(f"   ✅ {funcao}() - Definida e exposta")
                        self.sucessos.append(f"{funcao} OK")
                    else:
                        print(f"   ⚠️  {funcao}() - Definida mas NÃO exposta globalmente")
                        self.avisos.append(f"{funcao} não exposta em {arquivo}")
                else:
                    print(f"   ❌ {funcao}() - NÃO encontrada")
                    self.erros.append(f"{funcao} ausente em {arquivo}")
    
    def verificar_botoes_html(self):
        """Verifica se botões onclick têm funções correspondentes"""
        print("\n" + "="*80)
        print("🔍 VERIFICANDO BOTÕES ONCLICK")
        print("="*80)
        
        html_file = Path('templates/interface_nova.html')
        
        if not html_file.exists():
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrair handlers onclick
        handlers = re.findall(r'onclick=["\']([^"\']+)["\']', content)
        
        # Extrair nome das funções
        funcoes_chamadas = set()
        for handler in handlers:
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', handler)
            if match:
                funcoes_chamadas.add(match.group(1))
        
        print(f"\n📊 Total de funções chamadas via onclick: {len(funcoes_chamadas)}\n")
        
        # Verificar se funções existem nos JS
        js_files = list(Path('static').glob('*.js'))
        all_js_content = ""
        
        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    all_js_content += f.read() + "\n"
            except:
                pass
        
        funcoes_faltantes = []
        funcoes_presentes = []
        
        for funcao in sorted(funcoes_chamadas):
            pattern = rf'(?:async\s+)?function\s+{funcao}\s*\(|(?:const|let|var)\s+{funcao}\s*='
            if re.search(pattern, all_js_content):
                funcoes_presentes.append(funcao)
            else:
                funcoes_faltantes.append(funcao)
        
        if funcoes_presentes:
            print("✅ Funções implementadas:")
            for f in funcoes_presentes[:20]:  # Mostrar primeiras 20
                print(f"   ✅ {f}()")
            if len(funcoes_presentes) > 20:
                print(f"   ... e mais {len(funcoes_presentes)-20} funções")
        
        if funcoes_faltantes:
            print("\n❌ Funções FALTANTES (botões não funcionam):")
            for f in funcoes_faltantes:
                print(f"   ❌ {f}()")
                self.erros.append(f"Função {f}() chamada no HTML mas não implementada")
        
        # Estatísticas
        total = len(funcoes_chamadas)
        implementadas = len(funcoes_presentes)
        print(f"\n📊 Estatísticas:")
        print(f"   Total: {total} funções")
        print(f"   Implementadas: {implementadas} ({implementadas/total*100:.1f}%)")
        print(f"   Faltantes: {len(funcoes_faltantes)} ({len(funcoes_faltantes)/total*100:.1f}%)")
    
    def verificar_secoes(self):
        """Verifica se todas as seções têm funções de carregamento"""
        print("\n" + "="*80)
        print("🔍 VERIFICANDO SEÇÕES E FUNÇÕES DE CARREGAMENTO")
        print("="*80)
        
        html_file = Path('templates/interface_nova.html')
        
        if not html_file.exists():
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrair IDs de seções
        secoes = re.findall(r'id=["\']([^"\']*-section)["\']', content)
        secoes_unicas = sorted(set(secoes))
        
        print(f"\n📋 Total de seções encontradas: {len(secoes_unicas)}\n")
        
        # Verificar funções load correspondentes
        app_js = Path('static/app.js')
        if app_js.exists():
            with open(app_js, 'r', encoding='utf-8') as f:
                app_content = f.read()
        else:
            app_content = ""
        
        for secao in secoes_unicas:
            # Extrair nome da seção (remove -section)
            nome = secao.replace('-section', '').title().replace('-', '')
            
            # Possíveis nomes de função
            possiveis = [
                f'load{nome}',
                f'carregar{nome}',
                f'show{nome}'
            ]
            
            encontrada = False
            for possivel in possiveis:
                pattern = rf'(?:async\s+)?function\s+{possivel}\s*\('
                if re.search(pattern, app_content, re.IGNORECASE):
                    print(f"   ✅ {secao} → {possivel}()")
                    encontrada = True
                    break
            
            if not encontrada:
                print(f"   ⚠️  {secao} → Nenhuma função load encontrada")
                self.avisos.append(f"Seção {secao} sem função de carregamento")
    
    def gerar_relatorio(self):
        """Gera relatório final"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL")
        print("="*80)
        
        print(f"\n✅ Sucessos: {len(self.sucessos)}")
        print(f"⚠️  Avisos: {len(self.avisos)}")
        print(f"❌ Erros Críticos: {len(self.erros)}")
        
        if self.erros:
            print("\n🔴 ERROS CRÍTICOS (precisam ser corrigidos):")
            for erro in self.erros[:10]:
                print(f"   {erro}")
            if len(self.erros) > 10:
                print(f"   ... e mais {len(self.erros)-10} erros")
        
        if self.avisos:
            print("\n🟡 AVISOS (verificar se é problema):")
            for aviso in self.avisos[:10]:
                print(f"   {aviso}")
            if len(self.avisos) > 10:
                print(f"   ... e mais {len(self.avisos)-10} avisos")
        
        # Status geral
        print("\n" + "="*80)
        if len(self.erros) == 0:
            print("✅ SISTEMA PRONTO PARA USO")
            print("Todos os componentes essenciais estão carregando corretamente!")
        elif len(self.erros) < 5:
            print("🟡 SISTEMA FUNCIONAL COM PEQUENAS FALHAS")
            print(f"Corrigir {len(self.erros)} erro(s) para 100% de funcionalidade")
        else:
            print("🔴 SISTEMA COM PROBLEMAS CRÍTICOS")
            print(f"Corrigir {len(self.erros)} erro(s) antes de usar")
        print("="*80)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔧 VERIFICADOR DE CARREGAMENTO - SISTEMA FINANCEIRO")
    print("="*80)
    
    verificador = VerificadorCarregamento()
    
    verificador.verificar_ordem_scripts()
    verificador.verificar_funcoes_globais()
    verificador.verificar_botoes_html()
    verificador.verificar_secoes()
    verificador.gerar_relatorio()
    
    print("\n✅ Verificação concluída!\n")

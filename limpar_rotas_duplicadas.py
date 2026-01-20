"""
Script para remover rotas duplicadas do web_server.py
que já foram movidas para blueprints
"""

def remover_rotas_duplicadas():
    with open('web_server.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Encontrar e marcar linhas para remoção
    remover_blocos = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detectar início de rota de contratos
        if "@app.route('/api/contratos" in line:
            start = i
            # Encontrar o fim da função (próximo @app.route ou def sem indentação)
            i += 1
            while i < len(lines):
                if lines[i].startswith('@app.route') or (lines[i].startswith('def ') and not lines[i].startswith('    ')):
                    remover_blocos.append((start, i))
                    break
                i += 1
            continue
        
        # Detectar início de rota de sessões  
        if "@app.route('/api/sessoes" in line:
            start = i
            i += 1
            while i < len(lines):
                if lines[i].startswith('@app.route') or (lines[i].startswith('def ') and not lines[i].startswith('    ')):
                    remover_blocos.append((start, i))
                    break
                i += 1
            continue
        
        # Detectar início de rota de relatórios
        if "@app.route('/api/relatorios/" in line:
            start = i
            i += 1
            while i < len(lines):
                if lines[i].startswith('@app.route') or (lines[i].startswith('def ') and not lines[i].startswith('    ')):
                    remover_blocos.append((start, i))
                    break
                i += 1
            continue
        
        i += 1
    
    # Remover blocos de trás para frente (para não bagunçar os índices)
    for start, end in sorted(remover_blocos, reverse=True):
        print(f"Removendo linhas {start+1} a {end}")
        print(f"  Rota: {lines[start].strip()}")
        del lines[start:end]
    
    # Adicionar comentários explicativos
    for i, line in enumerate(lines):
        if "# === ROTAS DO MENU OPERACIONAL ===" in line:
            lines.insert(i+1, "# Rotas de Contratos movidas para app/routes/contratos.py\n")
            lines.insert(i+2, "# Rotas de Sessões movidas para app/routes/sessoes.py\n")
            lines.insert(i+3, "\n")
            break
        
        if "# === ROTAS DE RELATÓRIOS ===" in line:
            lines.insert(i+1, "# Todos os relatórios movidos para app/routes/relatorios.py\n")
            lines.insert(i+2, "\n")
            break
    
    # Salvar
    with open('web_server.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\n✅ Removidos {len(remover_blocos)} blocos de rotas duplicadas")
    print(f"📊 Arquivo reduzido para {len(lines)} linhas")

if __name__ == '__main__':
    remover_rotas_duplicadas()
